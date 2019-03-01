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
import zlib
import enum
import json
from .NamedVector import NamedVector

class UnsupportedError(Exception): pass

class PixelFormat(enum.IntEnum):
	BlackWhite = 0
	Grayscale = 1
	RGB = 2

class Dimensions(NamedVector):
	_COMPONENTS = [ "width", "height" ]

class Margin(NamedVector):
	_COMPONENTS = [ "top", "right", "bottom", "left" ]

class ResolutionDPI(NamedVector):
	_COMPONENTS = [ "x", "y" ]

class PDFImage(object):
	def __init__(self, data, image_format, pixel_format, dimensions, resolution_dpi, comment = None):
		assert(isinstance(pixel_format, PixelFormat))
		self._data = data
		self._image_format = image_format.upper()
		self._pixel_format = pixel_format
		self._dimensions = dimensions
		self._resolution_dpi = resolution_dpi
		self._comment = comment

	@property
	def data(self):
		return self._data

	@property
	def image_format(self):
		return self._image_format

	@property
	def pixel_format(self):
		return self._pixel_format

	@property
	def dimensions(self):
		return self._dimensions

	@property
	def resolution_dpi(self):
		return self._resolution_dpi

	@property
	def comment(self):
		return self._comment

	@property
	def extents_mm(self):
		return Dimensions(width = self.dimensions.width / self._resolution_dpi.x * 25.4, height = self.dimensions.height / self._resolution_dpi.y * 25.4)

	def convert_to(self, image_format = None, pixel_format = None, resolution_dpi = None):
		cmd = [ "convert" ]

		# Change pixel format, if requested
		if pixel_format is not None:
			if pixel_format == PixelFormat.RGB:
				cmd += [ "-set", "colorspace", "sRGB", "-depth", "8", "-type", "truecolor" ]
			elif pixel_format == PixelFormat.Grayscale:
				cmd += [ "-set", "colorspace", "gray", "-depth", "8", "-type", "grayscale" ]
			elif pixel_format == PixelFormat.BlackWhite:
				if image_format == "JPEG":
					raise UnsupportedError("JPEG does not support pixel format BlackWhite.")
				cmd += [ "-set", "colorspace", "gray", "-type", "bilevel", "-depth", "1" ]
			else:
				raise NotImplementedError(pixel_format)
		else:
			pixel_format = self.pixel_format

		# Change resolution, if requested
		if resolution_dpi is not None:
			new_resolution = ResolutionDPI(resolution_dpi, resolution_dpi)
			new_dimensions = Dimensions(width = round(self.dimensions.width * new_resolution.x / self.resolution_dpi.x), height = round(self.dimensions.height * new_resolution.y / self.resolution_dpi.y))
			cmd += [ "-geometry", "%dx%d!" % (new_dimensions.width, new_dimensions.height), "-units", "PixelsPerInch", "-density", "%f" % (new_resolution.x) ]
		else:
			new_resolution = self.resolution_dpi
			new_dimensions = self.dimensions

		# Change format, if requested
		cmd += [ "-" ]
		if image_format is not None:
			cmd += [ image_format + ":-" ]
		else:
			cmd += [ self.image_format + ":-" ]
			image_format = self.image_format
#		print(" ".join(cmd))
		data = subprocess.check_output(cmd, input = self._data)
		return PDFImage(data = data, image_format = image_format, pixel_format = pixel_format, dimensions = new_dimensions, resolution_dpi = new_resolution, comment = self.comment)

	@classmethod
	def _identify_image(cls, image_data):
		field_defs = {
			"%w":				"width",
			"%h":				"height",
			"%x":				"resolution_x",
			"%y":				"resolution_y",
			"%U":				"resolution_unit",
			"%m":				"image_format",
			"%[bit-depth]":		"bit_depth",
			"%[colorspace]":	"color_space",
			"%c":				"comment",
		}
		field_defs = sorted((x, y) for (x, y) in field_defs.items())
		cmd = [ "identify", "-format", "\\n".join(field_def[0] for field_def in field_defs), "-" ]
		stdout = subprocess.check_output(cmd, input = image_data)
		field_values = stdout.decode("ascii").split("\n")
		fields = { key: value for (key, value) in zip((field_def[1] for field_def in field_defs), field_values) }
		resolution_factor = {
			"PixelsPerInch":		1,
			"PixelsPerCentimeter":	2.54,
		}[fields["resolution_unit"]]
		pixel_format = {
			("sRGB", 8):		PixelFormat.RGB,
			("Gray", 8):		PixelFormat.Grayscale,
		}[(fields["color_space"], int(fields["bit_depth"]))]
		result = {
			"dimensions":			Dimensions(int(fields["width"]), int(fields["height"])),
			"resolution_dpi":		ResolutionDPI(float(fields["resolution_x"]) * resolution_factor, float(fields["resolution_y"]) * resolution_factor),
			"image_format":			fields["image_format"],
			"pixel_format":			pixel_format,
			"comment":				fields["comment"],
		}
		return result

	@classmethod
	def from_data(cls, image_data):
		info = cls._identify_image(image_data)
		return cls(data = image_data, image_format = info["image_format"], pixel_format = info["pixel_format"], dimensions = info["dimensions"], resolution_dpi = info["resolution_dpi"], comment = info["comment"])

	@classmethod
	def from_file(cls, filename):
		with open(filename, "rb") as f:
			data = f.read()
		return cls.from_data(data)

	def __str__(self):
		return "PDFImage<%d bytes, %s, %s, %d x %dpx / %.1f x %.1fmm>" % (len(self._data), self.image_format, self.pixel_format, self.dimensions.width, self.dimensions.height, self.extents_mm.width, self.extents_mm.height)

class PDFCreate(object):
	def __init__(self, filename, dimensions_mm = Dimensions(width = 210, height = 297), margin_mm = Margin(0, 0, 0, 0), author = None, title = None):
		self._writer = pdfrw.PdfWriter(filename)
		self._dimensions = dimensions_mm
		self._margin = margin_mm
		self._author = author
		self._title = title
		self._printable_area = Dimensions(width = self._dimensions.width - self._margin.left - self._margin.right, height = self._dimensions.height - self._margin.top - self._margin.bottom)
		assert(self.printable_area_mm.width > 0)
		assert(self.printable_area_mm.height > 0)

	@property
	def dimensions_dots(self):
		return self._dimensions * 72 / 25.4

	@property
	def printable_area_mm(self):
		return self._printable_area

	def add_page(self, pdfimage):
		if pdfimage.image_format not in [ "JPEG", "RGB", "GRAY" ]:
			raise UnsupportedError("PDF can only handle JPEG, RGB or GRAY image formats, but %s was supplied." % (pdfimage.image_format))

		custom_metadata = {
			"resolution_dpi":	list(pdfimage.resolution_dpi),
			"comment":			pdfimage.comment,
		}
		image = pdfrw.PdfDict({
			pdfrw.PdfName.Type:				pdfrw.PdfName.XObject,
			pdfrw.PdfName.Subtype:			pdfrw.PdfName.Image,
			pdfrw.PdfName.Interpolate:		True,
			pdfrw.PdfName.Width:			pdfimage.dimensions.width,
			pdfrw.PdfName.Height:			pdfimage.dimensions.height,
			pdfrw.PdfName.CustomMetadata:	json.dumps(custom_metadata),
		})

		if pdfimage.image_format == "JPEG":
			image[pdfrw.PdfName.Filter] = pdfrw.PdfName.DCTDecode
			image.stream = pdfrw.py23_diffs.convert_load(pdfimage.data)
		elif pdfimage.image_format in [ "RGB", "GRAY" ]:
			image[pdfrw.PdfName.Filter] = pdfrw.PdfName.FlateDecode
			image.stream = pdfrw.py23_diffs.convert_load(zlib.compress(pdfimage.data))
		else:
			raise NotImplementedError(pdfimage.image_format)

		if pdfimage.pixel_format == PixelFormat.RGB:
			image[pdfrw.PdfName.ColorSpace] = pdfrw.PdfName.DeviceRGB
			image[pdfrw.PdfName.BitsPerComponent] = 8
		elif pdfimage.pixel_format == PixelFormat.Grayscale:
			image[pdfrw.PdfName.ColorSpace] = pdfrw.PdfName.DeviceGray
			image[pdfrw.PdfName.BitsPerComponent] = 8
		elif pdfimage.pixel_format == PixelFormat.BlackWhite:
			image[pdfrw.PdfName.ColorSpace] = pdfrw.PdfName.DeviceGray
			image[pdfrw.PdfName.BitsPerComponent] = 1
		else:
			raise NotImplementedError(pdfimage.pixel_format)

		image_extents_mm = pdfimage.extents_mm
		image_scale_x = self.printable_area_mm.width / image_extents_mm.width
		image_scale_y = self.printable_area_mm.height / image_extents_mm.height
		image_scalar = min(image_scale_x, image_scale_y)
		if image_scalar > 1:
			# Never enlarge
			image_scalar = 1

		printed_size_dots = image_extents_mm * image_scalar * 72 / 25.4
		offset = (self.dimensions_dots - printed_size_dots) / 2
		params = {
			"xoffset":	offset.width,
			"yoffset":	offset.height,
			"xscalar":	printed_size_dots.width,
			"yscalar":	printed_size_dots.height,
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
			pdfrw.PdfName.MediaBox:	[ 0, 0, self.dimensions_dots.width, self.dimensions_dots.height ],
			pdfrw.PdfName.Contents:	page_content,
		})
		self._writer.addpage(page)

	def __enter__(self):
		return self

	def __exit__(self, *args):
		self.close()

	def close(self):
		self._writer.write()

class PDFImageFormatter(object):
	def __init__(self, best_chosen_pixel_format = PixelFormat.RGB, allow_lossy_compression = False, maximum_resolution_dpi = 600):
		self._allow_lossy_compression = allow_lossy_compression
		self._best_chosen_pixel_format = best_chosen_pixel_format
		self._maximum_resolution_dpi = maximum_resolution_dpi

	@classmethod
	def highlevel_color(cls):
		return cls(best_chosen_pixel_format = PixelFormat.RGB, allow_lossy_compression = True, maximum_resolution_dpi = 300)

	@classmethod
	def midlevel_color(cls):
		return cls(best_chosen_pixel_format = PixelFormat.RGB, allow_lossy_compression = True, maximum_resolution_dpi = 150)

	@classmethod
	def midlevel_gray(cls):
		return cls(best_chosen_pixel_format = PixelFormat.Grayscale, allow_lossy_compression = True, maximum_resolution_dpi = 150)

	@classmethod
	def lowlevel_bw(cls):
		return cls(best_chosen_pixel_format = PixelFormat.BlackWhite, allow_lossy_compression = True, maximum_resolution_dpi = 100)

	def reformat(self, pdfimage):
		conversion = { }

		if pdfimage.pixel_format > self._best_chosen_pixel_format:
			conversion["pixel_format"] = self._best_chosen_pixel_format
			new_pixel_format = self._best_chosen_pixel_format
		else:
			new_pixel_format = pdfimage.pixel_format

		if self._allow_lossy_compression and (new_pixel_format >= PixelFormat.Grayscale):
			conversion["image_format"] = "jpeg"
		else:
			if new_pixel_format in [ PixelFormat.BlackWhite, PixelFormat.Grayscale ]:
				conversion["image_format"] = "gray"
			else:
				conversion["image_format"] = "rgb"

		current_resolution = max(pdfimage.resolution_dpi)
		if current_resolution > self._maximum_resolution_dpi:
			conversion["resolution_dpi"] = self._maximum_resolution_dpi

		return pdfimage.convert_to(**conversion)

if __name__ == "__main__":
	formatter = PDFImageFormatter.midlevel_color()
	with PDFCreate("out.pdf", author = "Föö Bär", title = "Ze Title") as pdf:
#		pdf.add_image(PDFImage.from_file("test.png"), lossless = False, max_resolution_dpi = 150)
#		pdf.add_image(PDFImage.from_file("guitar.jpg"), lossless = False, max_resolution_dpi = 150)
		pdf.add_image(formatter.reformat(PDFImage.from_file("test.png")))
		pdf.add_image(formatter.reformat(PDFImage.from_file("guitar.jpg")))
