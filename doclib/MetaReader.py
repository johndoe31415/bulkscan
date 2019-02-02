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
import json
import subprocess

class MetaReaderException(Exception): pass

class MetaReader():
	def __init__(self, filename):
		self._filename = filename

	def read(self):
		if not os.path.isfile(self._filename):
			raise FileNotFoundError(self._filename)
		comment = subprocess.check_output([ "exiftool", "-S", "-comment", self._filename ])
		comment = comment.decode("utf-8")
		comment = comment.rstrip("\r\n")
		comment = comment[9:]
		try:
			data = json.loads(comment)
		except json.JSONDecodeError as e:
			raise MetaReaderException("Could not read metadata", e)
		return data

	def write(self, data):
		jsondata = json.dumps(data)
		subprocess.check_call([ "exiftool", "-overwrite_original_in_place", "-comment=%s" % (jsondata), self._filename ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
