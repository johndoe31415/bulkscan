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
import uuid
from doclib import MultiDoc

class DocEntry():
	def __init__(self, mudfile):
		self._stats = {
			"filename":		mudfile,
		}
		self._stats["mtime"] = self.mudfile_mtime
		self._stats["data"] = self._get_stats()

	@property
	def doc_uuid(self):
		return self._stats["data"]["properties"]["doc_uuid"]

	@property
	def filename(self):
		return self._stats["filename"]

	@property
	def mudfile_mtime(self):
		return os.stat(self.filename).st_mtime

	def _get_stats(self):
		stats = { }
		with MultiDoc(self.filename) as doc:
			stats["properties"] = doc.get_document_properties()
			stats["tags"] = sorted(doc.tags)
			stats["pages"] = doc.get_all_page_properties()
		return stats

class DocLibrary():
	def __init__(self, cachefile):
		pass

	def add_document(self, filename):
		print(DocEntry(filename))
		pass

	def add_directory(self, dirname):
		if not dirname.endswith("/"):
			dirname += "/"
		for filename in os.listdir(dirname):
			if filename.endswith(".mud"):
				full_filename = dirname + filename
				self.add_document(full_filename)
