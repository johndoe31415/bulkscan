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
import sqlite3
import contextlib
import textwrap
import hashlib
import uuid
import subprocess
import collections
import contextlib

class MultiDoc(object):
	_ImageCollection = collections.namedtuple("ImageCollection", [ "original", "enhanced", "thumbs" ])
	_ImageInfo = collections.namedtuple("ImageInfo", [ "datatype", "width", "height", "resolution_dpi" ])
	_DerivativeInfo = collections.namedtuple("DerivativeInfo", [ "derivative_id", "image_info" ])
	def __init__(self, filename):
		self._filename = filename
		self._conn = sqlite3.connect(filename)
		self._cursor = self._conn.cursor()

		with contextlib.suppress(sqlite3.OperationalError):
			self._cursor.execute(textwrap.dedent("""\
			CREATE TABLE fileversion (
				version integer PRIMARY KEY
			);
			"""))
			self._cursor.execute("INSERT INTO fileversion (version) VALUES (2);")
			self._conn.commit()

		with contextlib.suppress(sqlite3.OperationalError):
			self._cursor.execute(textwrap.dedent("""\
			CREATE TABLE image_original (
				side_uuid uuid PRIMARY KEY,
				sheet_uuid uuid NOT NULL,
				sheet_side varchar NOT NULL,
				data blob NOT NULL,
				datatype varchar NOT NULL,
				width integer NOT NULL,
				height integer NOT NULL,
				resolution_dpi float NOT NULL,
				img_hash_sha256 NULL,
				orderno integer UNIQUE,
				CHECK ((sheet_side = 'front') OR (sheet_side = 'back'))
			);
			"""))
			self._conn.commit()

		with contextlib.suppress(sqlite3.OperationalError):
			self._cursor.execute(textwrap.dedent("""\
			CREATE TABLE image_derivative (
				derivative_id integer PRIMARY KEY,
				side_uuid uuid NOT NULL,
				derivative_type varchar NOT NULL,
				data blob NOT NULL,
				datatype varchar NOT NULL,
				width integer NULL,
				height integer NULL,
				resolution_dpi float NULL,
				CHECK ((derivative_type = 'thumb') OR (derivative_type = 'enhanced') OR (derivative_type = 'ocr'),
				FOREIGN KEY(side_uuid) REFERENCES image_original(side_uuid)
			);
			"""))
			self._conn.commit()

		with contextlib.suppress(sqlite3.OperationalError):
			self._cursor.execute(textwrap.dedent("""\
			CREATE TABLE image_meta (
				side_uuid varchar NOT NULL,
				key varchar NOT NULL,
				value varchar NOT NULL,
				PRIMARY KEY(side_uuid, key)
			);
			"""))
			self._conn.commit()

		with contextlib.suppress(sqlite3.OperationalError):
			self._cursor.execute(textwrap.dedent("""\
			CREATE TABLE document_meta (
				key varchar PRIMARY KEY,
				value varchar NOT NULL
			);
			"""))
			self._conn.commit()

		with contextlib.suppress(sqlite3.OperationalError):
			self._cursor.execute(textwrap.dedent("""\
			CREATE TABLE document_tags (
				tag varchar PRIMARY KEY
			);
			"""))
			self._conn.commit()

	def _image_info(self, filename, input_data = None):
		if input_data is not None:
			filename = "-"
		stdout = subprocess.check_output([ "identify", "-format", "%w %h %x %y %U %m", filename ], input = input_data)
		stdout = stdout.decode("ascii").split()
		(width, height, resolution_x, resolution_y, resolution_unit, datatype) = stdout
		width = int(width)
		height = int(height)
		resolution_x = float(resolution_x)
		resolution_y = float(resolution_y)
		datatype = datatype.lower()
		if abs((resolution_x - resolution_y) / resolution_x) > 0.01:
			raise Exception("X and Y resolution of image disagree more than 1%% from each other (%f and %f %s, respectively)." % (resolution_x, resolution_y, resolution_unit))
		resolution = (resolution_x + resolution_y) / 2
		scalar = {
			"PixelsPerInch":			1,
			"PixelsPerCentimeter":		2.54,
		}
		resolution_dpi = resolution * scalar[resolution_unit]
		return self._ImageInfo(datatype = datatype, width = width, height = height, resolution_dpi = resolution_dpi)

	@property
	def filename(self):
		return self._filename

	@property
	def pagecnt(self):
		count = self._cursor.execute("SELECT COUNT(*) FROM image_original;").fetchone()[0]
		return count

	@property
	def tags(self):
		tags = set([ row[0] for row in self._cursor.execute("SELECT tag FROM document_tags;").fetchall() ])
		return tags

	@property
	def peer(self):
		return self.get_document_property("peer")

	@property
	def docname(self):
		return self.get_document_property("docname")

	def close(self):
		self._conn.commit()
		self._cursor.close()
		self._conn.close()

	def add_derivative(self, side_uuid, img_data, derivative_type):
		info = self._image_info(filename = None, input_data = img_data)
		self._cursor.execute("""INSERT INTO image_derivative (derivative_id, side_uuid, derivative_type, data, datatype, width, height, resolution_dpi) VALUES
				((SELECT MAX(derivative_id) + 1 FROM image_derivative), ?, ?, ?, ?, ?, ?, ?);""",
				(side_uuid, derivative_type, img_data, info.datatype, info.width, info.height, info.resolution_dpi))

	def delete_all_derivatives(self):
		self._cursor.execute("DELETE FROM image_derivative;")
		self._conn.commit()
		self._cursor.execute("VACUUM;")

	def add(self, filename, side_uuid = None, sheet_uuid = None, sheet_side = "front"):
		with open(filename, "rb") as f:
			data = f.read()
		img_hash_sha256 = hashlib.sha256(data).hexdigest()
		info = self._image_info(filename)

		if side_uuid is None:
			side_uuid = str(uuid.uuid4())
		if sheet_uuid is None:
			sheet_uuid = str(uuid.uuid4())

		self._cursor.execute("INSERT INTO image_original (side_uuid, sheet_uuid, sheet_side, data, datatype, width, height, resolution_dpi, img_hash_sha256, orderno) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
				(side_uuid, sheet_uuid, sheet_side, data, info.datatype, info.width, info.height, info.resolution_dpi, img_hash_sha256, self.pagecnt))

		return side_uuid

	def get_side_images_info(self, side_uuid):
		original_info = self._cursor.execute("SELECT datatype, width, height, resolution_dpi FROM image_original WHERE side_uuid = ?;", (side_uuid, )).fetchone()
		if original_info is None:
			raise FileNotFoundError("No side with UUID %s found in MUD." % (side_uuid))
		original_info = self._ImageInfo(*original_info)

		derivatives = collections.defaultdict(list)
		derived_imgs = self._cursor.execute("SELECT derivative_id, derivative_type, datatype, width, height, resolution_dpi FROM image_derivative WHERE side_uuid = ?;", (side_uuid, )).fetchall()
		for derivative_info in derived_imgs:
			(derivative_id, derivative_type) = derivative_info[:2]
			image_info = self._ImageInfo(*(derivative_info[2:]))
			derivative_info = self._DerivativeInfo(derivative_id = derivative_id, image_info = image_info)
			derivatives[derivative_type].append(derivative_info)
		return self._ImageCollection(original = original_info, enhanced = derivatives["enhanced"], thumbs = derivatives["thumb"])

	def get_derived_image(self, derivative_id):
		return self._cursor.execute("SELECT data FROM image_derivative WHERE derivative_id = ?;", (derivative_id, )).fetchone()[0]

	def get_page_image(self, side_uuid, allow_enhanced = True):
		return self._cursor.execute("SELECT data FROM image_original WHERE side_uuid = ?;", (side_uuid, )).fetchone()[0]

	def get_page_order(self):
		return [ row[0] for row in self._cursor.execute("SELECT side_uuid FROM image_original ORDER BY orderno ASC;").fetchall() ]

	def get_page_properties(self, side_uuid):
		return { key: value for (key, value) in self._cursor.execute("SELECT key, value FROM image_meta WHERE side_uuid = ?;", (side_uuid, )).fetchall() }

	def get_all_page_properties(self):
		return [ self.get_page_properties(side_uuid) for side_uuid in self.get_page_order() ]

	def set_document_property(self, key, value):
		count = self._cursor.execute("SELECT COUNT(*) FROM document_meta WHERE key = ?;", (key, )).fetchone()[0]
		if count == 0:
			self._cursor.execute("INSERT INTO document_meta (key, value) VALUES (?, ?);", (key, value))
		else:
			self._cursor.execute("UPDATE document_meta SET value = ? WHERE key = ?;", (value, key))

	def set_side_property(self, side_uuid, key, value):
		count = self._cursor.execute("SELECT COUNT(*) FROM image_meta WHERE (key = ?) AND (side_uuid = ?);", (key, side_uuid)).fetchone()[0]
		if count == 0:
			self._cursor.execute("INSERT INTO image_meta (side_uuid, key, value) VALUES (?, ?, ?);", (side_uuid, key, value))
		else:
			self._cursor.execute("UPDATE image_meta SET value = ? WHERE (key = ?) AND (side_uuid = ?);", (value, key, side_uuid))

	def get_document_properties(self):
		return { key: value for (key, value) in  self._cursor.execute("SELECT key, value FROM document_meta;").fetchall() }

	def get_document_property(self, key):
		row = self._cursor.execute("SELECT value FROM document_meta WHERE key = ?;", (key, )).fetchone()
		if row is None:
			return None
		else:
			return row[0]

	def add_tag(self, tag):
		with contextlib.suppress(sqlite3.IntegrityError):
			self._cursor.execute("INSERT INTO document_tags (tag) VALUES (?);", (tag, ));

	def remove_tag(self, tag):
		self._cursor.execute("DELETE FROM document_tags WHERE tag = ?;", (tag, ))

	def dump_all_content(self, directory):
		os.makedirs(directory + "/original/")
		os.makedirs(directory + "/enhanced/")
		os.makedirs(directory + "/thumbs/")
		for (pageno, side_uuid) in enumerate(self.get_page_order(), 1):
			info = self.get_side_images_info(side_uuid)
			with open("%s/original/%03d_%s.%s" % (directory, pageno, side_uuid, info.original.datatype), "wb") as f:
				img_data = self.get_page_image(side_uuid, allow_enhanced = False)
				f.write(img_data)

			for (derivative_type, derivatives) in [ ("enhanced", info.enhanced), ("thumbs", info.thumbs) ]:
				for derivative in derivatives:
					with open("%s/%s/%03d_%s.%s" % (directory, derivative_type, derivative.derivative_id, side_uuid, derivative.image_info.datatype), "wb") as f:
						img_data = self.get_derived_image(derivative.derivative_id)
						f.write(img_data)


#			orig_filename = "%05d_%s.

#		def get_page_order(self):
#		return [ row[0] for row in self._cursor.execute("SELECT side_uuid FROM image_original ORDER BY orderno ASC;").fetchall() ]

	def __enter__(self):
		return self

	def __exit__(self, *args):
		self.close()

	def __str__(self):
		return "MultiDoc<%s, %d pages>" % (self.filename, self.pagecnt)

if __name__ == "__main__":
	with MultiDoc("scan.mud") as md:
		print(md)
		md.add("bulk_12345_12345.png")
		print(md)
