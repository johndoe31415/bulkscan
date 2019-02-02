#	bulkscan - Document scanning and maintenance solution
#	Copyright (C) 2019-2019 Johannes Bauer
#
#	This file is part of bulkscan.
#
#	bulkscan is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	bulkscan is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with bulkscan; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import os
import time
import re
import json
import subprocess
import contextlib
import tempfile
import shutil
import doclib
import datetime
from .AutocompleteDB import AutocompleteDB

class Controller():
	def __init__(self, app):
		self._app = app
		self._config = None
		self._basedir = os.path.dirname(__file__)
		self._acdb = None

	def _late_init(self):
		# Now config is available
		with contextlib.suppress(FileExistsError):
			os.makedirs(self._config["thumb_dir"])
		with contextlib.suppress(FileExistsError):
			os.makedirs(self._config["trash_dir"])
		with contextlib.suppress(FileExistsError):
			os.makedirs(self._config["doc_dir"])
		with contextlib.suppress(FileExistsError):
			os.makedirs(self._config["processed_dir"])
		self._acdb = AutocompleteDB(self._config["autocomplete_config"])

	@property
	def config(self):
		return self._config

	@property
	def acdb(self):
		return self._acdb

	def set_config(self, config):
		self._config = config
		self._late_init()

	@property
	def staticdir(self):
		return self._basedir + "/static"

	def list_incoming(self):
		incoming_files = [ filename for filename in os.listdir(self._config["incoming_dir"]) if filename.endswith(".png") ]
		incoming_files.sort()
		return incoming_files

	def rotate(self, filename, degrees):
		input_filename = self._config["incoming_dir"] + "/" + filename
		with tempfile.NamedTemporaryFile(suffix = ".png", delete = False) as outfile:
			subprocess.check_call([ "convert", "-rotate", str(degrees), input_filename, outfile.name ])
			shutil.move(outfile.name, input_filename)
			self.remove_thumb(filename)

	def _find_filename(self, filename):
		for i in range(1000):
			if i == 0:
				result_filename = filename
			else:
				(prefix, extension) = os.path.splitext(filename)
				result_filename = prefix + "_%03d" % (i) + extension
			if not os.path.exists(result_filename):
				return result_filename
		return None

	def _delete_file(self, src_filename):
		return self._move_file(src_filename, self._config["trash_dir"])

	def _move_file(self, src_filename, target_dir):
		dst_filename = self._find_filename(target_dir + "/" + os.path.basename(src_filename))
		if dst_filename is not None:
			os.rename(src_filename, dst_filename)
		return dst_filename is not None

	def delete_incoming(self, filelist):
		result = { }
		return { filename: self._delete_file(self._config["incoming_dir"] + "/" + filename) for filename in filelist }

	def get_thumb_filename_for(self, filename):
		thumb_filename = self._config["thumb_dir"] + "/" + filename
		if thumb_filename.endswith(".png"):
			thumb_filename = thumb_filename[:-3] + "jpg"
		return thumb_filename

	def remove_thumb(self, filename):
		with contextlib.suppress(FileNotFoundError):
			os.unlink(self.get_thumb_filename_for(filename))

	def get_thumb(self, filename):
		thumb_filename = self.get_thumb_filename_for(filename)
		if not os.path.isfile(thumb_filename):
			src_filename = self._config["incoming_dir"] + "/" + filename
			subprocess.check_call([ "convert", "-quality", "80", "-resize", "200x300", src_filename, thumb_filename ])
		return os.path.basename(thumb_filename)

	def create_document(self, filenames, tags = None, attributes = None):
		if tags is None:
			tags = [ ]
		if attributes is None:
			attributes = { }
		attributes = { key: value for (key, value) in attributes.items() if (value is not None) }

		fn_elements = [ ]
		if "docdate" in attributes:
			fn_elements.append(attributes["docdate"].split(":")[1])
		if "peer" in attributes:
			fn_elements.append(attributes["peer"].replace(" ", "_"))
		if "docname" in attributes:
			fn_elements.append(attributes["docname"].replace(" ", "_"))
		self.acdb.put_peer_docname(attributes.get("peer"), attributes.get("docname"))
		self.acdb.put_tags(tags)
		self.acdb.write()

		output_doc = self._find_filename(self._config["doc_dir"] + "/" + "-".join(fn_elements) + ".mud")
		with doclib.MultiDoc(output_doc) as doc:
			for filename in filenames:
				full_filename = self._config["incoming_dir"] + "/" + filename
				try:
					meta = doclib.MetaReader(full_filename).read()
				except doclib.MetaReaderException:
					meta = { }
				side_uuid = doc.add(full_filename, "png", side_uuid = meta.get("side_uuid"), sheet_uuid = meta.get("page_uuid"), sheet_side = meta.get("side", "front"))
				doc.set_side_property(side_uuid, "orig_filename", filename)
				for attribute in [ "batch_uuid", "created_utc", "scanned_page_no" ]:
					if attribute in meta:
						doc.set_side_property(side_uuid, attribute, str(meta[attribute]))

			doc.set_document_property("created_utc", datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))
			for (key, value) in attributes.items():
				doc.set_document_property(key, value)
			for tag in tags:
				doc.add_tag(tag)
		for filename in filenames:
			self._move_file(self._config["incoming_dir"] + "/" + filename, self._config["processed_dir"])
		return { "success": True }
