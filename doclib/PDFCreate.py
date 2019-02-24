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

import pdfrw
import textwrap
import subprocess

class PDFImage(object):
	def __init__(self, data, data_format, width, height, resolution_x_dpi, resolution_y_dpi):
		assert(data_format in [ "png", "jpg" ])
		self._data = data
		self._data_format = data_format
		self._width = width
		self._height = height
		self._resolution_x_dpi = resolution_x_dpi
		self._resolution_y_dpi = resolution_y_dpi

	@property
	def data(self):
		return self._data

	@property
	def data_format(self):
		return self._data_format

	@property
	def width(self):
		return self._width

	@property
	def height(self):
		return self._height

	@property
	def resolution_x_dpi(self):
		return self._resolution_x_dpi

	@property
	def resolution_y_dpi(self):
		return self._resolution_y_dpi

	@property
	def extents_mm(self):
		return (self.width / self._resolution_x_dpi * 25.4, self.height / self._resolution_y_dpi * 25.4)

	@classmethod
	def _identify_image(cls, filename):
		stdout = subprocess.check_output([ "identify", "-format", "%w %h %x %y %U %m", filename ])
		stdout = stdout.decode("ascii").split()
		resolution_unit = stdout[4]
		resolution_factor = {
			"PixelsPerInch":		1,
			"PixelsPerCentimeter":	2.54,
		}[resolution_unit]
		result = {
			"width":				int(stdout[0]),
			"height":				int(stdout[1]),
			"resolution_x_dpi":		float(stdout[2]) * resolution_factor,
			"resolution_y_dpi":		float(stdout[3]) * resolution_factor,
			"magic":				stdout[5],
		}
		return result

	@classmethod
	def from_jpgfile(cls, filename):
		info = cls._identify_image(filename)
		assert(info["magic"] == "JPEG")
		with open(filename, "rb") as f:
			data = f.read()
		return cls(data = data, data_format = "jpg", width = info["width"], height = info["height"], resolution_x_dpi = info["resolution_x_dpi"], resolution_y_dpi = info["resolution_y_dpi"])

	def __str__(self):
		return "PDFImage<%d bytes, %s, %d x %d>" % (len(self._data), self.data_format, self.width, self.height)

class PDFCreate(object):
	def __init__(self, filename, dimensions_mm = (210, 297), margin_mm = (10, 10, 10, 10)):
		self._writer = pdfrw.PdfWriter(filename)
		self._dimension = dimensions_mm
		self._margin = margin_mm
		assert(self.printable_width_mm > 0)
		assert(self.printable_height_mm > 0)

	@property
	def width_dots(self):
		return self._dimension[0] * 72 / 25.4

	@property
	def height_dots(self):
		return self._dimension[1] * 72 / 25.4

	@property
	def printable_width_mm(self):
		return self._dimension[0] - (self._margin[1] - self._margin[3])

	@property
	def printable_height_mm(self):
		return self._dimension[1] - (self._margin[0] - self._margin[2])

	def add_image(self, pdfimage):
		image = pdfrw.PdfDict({
			pdfrw.PdfName.Type:				pdfrw.PdfName.XObject,
			pdfrw.PdfName.Subtype:			pdfrw.PdfName.Image,
			pdfrw.PdfName.Width:			pdfimage.width,
			pdfrw.PdfName.Height:			pdfimage.height,
			pdfrw.PdfName.ColorSpace:		pdfrw.PdfName.DeviceRGB,
			pdfrw.PdfName.BitsPerComponent:	8,
			pdfrw.PdfName.Filter:			pdfrw.PdfName.DCTDecode if pdfimage.data else None,
			pdfrw.PdfName.Interpolate:		True,
		})
		image.stream = pdfimage.data.decode("latin1")

		image_extents_mm = pdfimage.extents_mm
		image_scale_x = self.printable_width_mm / image_extents_mm[0]
		image_scale_y = self.printable_height_mm / image_extents_mm[1]
		image_scalar = min(image_scale_x, image_scale_y)
		if image_scalar > 1:
			# Never enlarge
			image_scalar = 1

		printed_width_dots = (image_extents_mm[0] * image_scalar) * 72 / 25.4
		printed_height_dots = (image_extents_mm[1] * image_scalar) * 72 / 25.4

		params = {
			"xoffset":	(self.width_dots / 2) - (printed_width_dots / 2),
			"yoffset":	(self.height_dots / 2) - (printed_height_dots / 2),
			"xscalar":	image_scalar * pdfimage.resolution_x_dpi,
			"yscalar":	image_scalar * pdfimage.resolution_y_dpi,
		}

		page_content = pdfrw.PdfDict()
		page_content.stream = textwrap.dedent("""\
		%(xscalar)f 0 0 %(yscalar)f %(xoffset)f %(yoffset)f cm
		/Img Do
		""" % (params))

		page = pdfrw.PdfDict({
			pdfrw.PdfName.Type:		pdfrw.PdfName.Page,
			pdfrw.PdfName.Resources: pdfrw.PdfDict({
				pdfrw.PdfName.XObject:	pdfrw.PdfDict({
					pdfrw.PdfName.Img:	image,
				}),
			}),
			pdfrw.PdfName.MediaBox:	[ 0, 0, self.width_dots, self.height_dots ],
			pdfrw.PdfName.Contents:	page_content,
		})
		self._writer.addpage(page)

	def __enter__(self):
		return self

	def __exit__(self, *args):
		self.close()

	def close(self):
		self._writer.write()

if __name__ == "__main__":
	with PDFCreate("out.pdf") as pdf:
		jpg = PDFImage.from_jpgfile("guitar.jpg")
		print(jpg)
		pdf.add_image(jpg)

		png = PDFImage.from_jpgfile("x.png")
		print(png)
		pdf.add_image(png)
