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
import collections

class AutocompleteDB():
	def __init__(self, filename):
		self._filename = filename
		self._tag = set()
		self._docname_by_peer = collections.defaultdict(set)
		self._load(filename)
		self._dirty = False

	def _load(self, filename):
		with open(filename) as f:
			json_data = json.load(f)
		self._tag |= set(json_data.get("tag", [ ]))
		for (key, values) in json_data.get("docname_by_peer", { }).items():
			self._docname_by_peer[key] |= set(values)

	def get_all(self):
		write_data = {
			"tag":				sorted(list(self._tag)),
			"docname_by_peer":	{ key: sorted(list(value)) for (key, value) in self._docname_by_peer.items() },
		}
		return write_data

	def put_tag(self, tag):
		if tag not in self._tag:
			self._tag.add(tag)
			self._dirty = True

	def put_tags(self, tags):
		for tag in tags:
			self.put_tag(tag)

	def put_peer_docname(self, peer, docname):
		if peer is not None:
			if peer not in self._docname_by_peer:
				self._docname_by_peer[peer]
				self._dirty = True
			if (docname is not None) and (docname not in self._docname_by_peer[peer]):
				self._docname_by_peer[peer].add(docname)
				self._dirty = True

	def write(self):
		if not self._dirty:
			return
		write_data = self.get_all()
		with open(self._filename + "_", "w") as f:
			json.dump(write_data, f)
		os.rename(self._filename + "_", self._filename)
		self._dirty = False

if __name__ == "__main__":
	acdb = AutocompleteDB("autocomplete.json")
	print(acdb.get_all())
	acdb.write()
