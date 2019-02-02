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
