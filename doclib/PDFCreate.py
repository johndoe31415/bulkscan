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

class PixelFormat(enum.IntEnum):
	BlackWhite = 0
	Grayscale = 1
	RGB = 2

class NamedVector(object):
	_COMPONENTS = None

	def __init__(self, *values, **kwargs):
		if (len(values) == len(self._COMPONENTS)) and (len(kwargs) == 0):
			self._values = tuple(values)
		elif (len(kwargs) == len(self._COMPONENTS)) and (len(values) == 0):
			self._values = tuple(kwargs[key] for key in self._COMPONENTS)
		else:
			if (len(values) > 0) and (len(kwargs) > 0):
				raise Exception("Can only specify args or kwargs, not mix the two")
			else:
				raise Exception("Agument count mismatch (expected %d)." % (len(self._COMPONENTS)))

	def __getattr__(self, key):
		return self._values[self._COMPONENTS.index(key)]

	def __iter__(self):
		return iter(self._values)

	def __add__(self, other):
		return self.__class__(*((x + y) for (x, y) in zip(self, other)))

	def __mul__(self, scalar):
		return self.__class__(*((x * scalar) for x in self))

	def __truediv__(self, dividend):
		return self * (1 / dividend)

	def __sub__(self, other):
		return self + (-other)

	def __neg__(self):
		return self.__class__(*(-x for x in self))

	def __len__(self):
		return len(self._values)

	def __str__(self):
		return "%s<%s>" % (self.__class__.__name__, ", ".join("%.3f" % (x) for x in self))


class Dimensions(NamedVector):
	_COMPONENTS = [ "width", "height" ]

class Margin(NamedVector):
	_COMPONENTS = [ "top", "right", "bottom", "left" ]

class ResolutionDPI(NamedVector):
	_COMPONENTS = [ "x", "y" ]

class PDFImage(object):
	def __init__(self, data, image_format, pixel_format, dimensions, resolution_dpi):
		assert(isinstance(pixel_format, PixelFormat))
		self._data = data
		self._image_format = image_format
		self._pixel_format = pixel_format
		self._dimensions = dimensions
		self._resolution_dpi = resolution_dpi

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
	def extents_mm(self):
		return Dimensions(width = self.dimensions.width / self._resolution_dpi.x * 25.4, height = self.dimensions.height / self._resolution_dpi.y * 25.4)

	def convert_to(self, image_format, pixel_format, max_resolution_dpi):
		current_resolution = max(self._resolution_dpi)
		if (image_format == self.image_format) and (self.pixel_format <= pixel_format) and ((max_resolution_dpi is None) or (current_resolution <= max_resolution_dpi)):
			# No changes needed.
			return self

		cmd = [ "convert" ]
		if pixel_format == PixelFormat.RGB:
			cmd += [ "-set", "colorspace", "sRGB", "-depth", "8", "-type", "truecolor" ]
		elif pixel_format == PixelFormat.Grayscale:
			cmd += [ "-set", "colorspace", "gray", "-depth", "8", "-type", "grayscale" ]
		elif pixel_format == PixelFormat.BlackWhite:
			if image_format == "JPEG":
				raise Exception("JPEG does not support Black/White")
			cmd += [ "-set", "colorspace", "gray", "-type", "bilevel", "-depth", "1" ]
		else:
			raise NotImplementedError(pixel_format)
		if (max_resolution_dpi is not None) and max(self._resolution_dpi) > max_resolution_dpi:
			new_resolution = ResolutionDPI(max_resolution_dpi, max_resolution_dpi)
			new_dimensions = Dimensions(width = round(self.dimensions.width * new_resolution.x / self.resolution_dpi.x), height = round(self.dimensions.height * new_resolution.y / self.resolution_dpi.y))
			cmd += [ "-geometry", "%dx%d!" % (new_dimensions.width, new_dimensions.height), "-units", "PixelsPerInch", "-density", "%f" % (new_resolution.x) ]
		else:
			new_resolution = self.resolution_dpi
			new_dimensions = self.dimensions
		cmd += [ "-", image_format + ":-" ]
		print(" ".join(cmd))
		data = subprocess.check_output(cmd, input = self._data)
		return PDFImage(data = data, image_format = image_format, pixel_format = pixel_format, dimensions = new_dimensions, resolution_dpi = new_resolution)

	@classmethod
	def _identify_image(cls, filename):
		field_defs = {
			"%w":				"width",
			"%h":				"height",
			"%x":				"resolution_x",
			"%y":				"resolution_y",
			"%U":				"resolution_unit",
			"%m":				"image_format",
			"%[bit-depth]":		"bit_depth",
			"%[colorspace]":	"color_space",
		}
		field_defs = sorted((x, y) for (x, y) in field_defs.items())
		cmd = [ "identify", "-format", "|".join(field_def[0] for field_def in field_defs), filename ]
		stdout = subprocess.check_output(cmd)
		field_values = stdout.decode("ascii").split("|")
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
		}
		return result

	@classmethod
	def from_file(cls, filename):
		info = cls._identify_image(filename)
		with open(filename, "rb") as f:
			data = f.read()
		return cls(data = data, image_format = info["image_format"], pixel_format = info["pixel_format"], dimensions = info["dimensions"], resolution_dpi = info["resolution_dpi"])

	def __str__(self):
		return "PDFImage<%d bytes, %s, %s, %d x %dpx / %.1f x %.1fmm>" % (len(self._data), self.image_format, self.pixel_format, self.dimensions.width, self.dimensions.height, self.extents_mm.width, self.extents_mm.height)

class PDFCreate(object):
	def __init__(self, filename, dimensions_mm = Dimensions(width = 210, height = 297), margin_mm = Margin(0, 0, 0, 0)):
		self._writer = pdfrw.PdfWriter(filename)
		self._dimensions = dimensions_mm
		self._margin = margin_mm
		self._printable_area = Dimensions(width = self._dimensions.width - self._margin.left - self._margin.right, height = self._dimensions.height - self._margin.top - self._margin.bottom)
		assert(self.printable_area_mm.width > 0)
		assert(self.printable_area_mm.height > 0)

	@property
	def dimensions_dots(self):
		return self._dimensions * 72 / 25.4

	@property
	def printable_area_mm(self):
		return self._printable_area

	@staticmethod
	def _pdf_pixel_compression(width, bilevel_data):
		"""Convert 1-bit per pixel/byte to 1 bit per pixel, but 8 bit per byte."""
		print(bilevel_data[:10].hex())
		return bilevel_data

	def add_image(self, pdfimage, pixel_format = None, max_resolution_dpi = None, lossless = False):
		if pixel_format is None:
			pixel_format = pdfimage.pixel_format

		image = pdfrw.PdfDict({
			pdfrw.PdfName.Type:				pdfrw.PdfName.XObject,
			pdfrw.PdfName.Subtype:			pdfrw.PdfName.Image,
			pdfrw.PdfName.Interpolate:		True,
		})
		print("Add image:", pdfimage)
		if not lossless:
			pdfimage = pdfimage.convert_to("JPEG", pixel_format = pixel_format, max_resolution_dpi = max_resolution_dpi)
		else:
			if pixel_format == PixelFormat.RGB:
				pdfimage = pdfimage.convert_to("RGB", pixel_format = pixel_format, max_resolution_dpi = max_resolution_dpi)
			elif pixel_format in [ PixelFormat.Grayscale, PixelFormat.BlackWhite ]:
				pdfimage = pdfimage.convert_to("GRAY", pixel_format = pixel_format, max_resolution_dpi = max_resolution_dpi)
			else:
				raise NotImplementedError(pixel_format)
		image.update({
			pdfrw.PdfName.Width:			pdfimage.dimensions.width,
			pdfrw.PdfName.Height:			pdfimage.dimensions.height,
		})
		print("After conv:", pdfimage)

		if pdfimage.image_format == "JPEG":
			image[pdfrw.PdfName.Filter] = pdfrw.PdfName.DCTDecode
			image.stream = pdfrw.py23_diffs.convert_load(pdfimage.data)
		elif pdfimage.image_format in [ "RGB", "GRAY" ]:
			image[pdfrw.PdfName.Filter] = pdfrw.PdfName.FlateDecode
			if pdfimage.pixel_format != PixelFormat.BlackWhite:
				image.stream = pdfrw.py23_diffs.convert_load(zlib.compress(pdfimage.data))
			else:
				x = bytearray(pdfimage.data)
				print(pdfimage.data[:60].hex())
				def bito(x):
					y = 0
					for i in range(8):
						if x & (1 << i):
							y |= (1 << (7 - i))
					return y
				for i in range(60):
					x[i] = bito(x[i])


				image.stream = pdfrw.py23_diffs.convert_load(zlib.compress(self._pdf_pixel_compression(pdfimage.dimensions.width, x)))
				#image.stream = pdfrw.py23_diffs.convert_load(zlib.compress(self._pdf_pixel_compression(pdfimage.dimensions.width, pdfimage.data)))
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

if __name__ == "__main__":
	with PDFCreate("out.pdf") as pdf:
#		pdf.add_image(PDFImage.from_file("test.png"), lossless = False, max_resolution_dpi = 150)
#		pdf.add_image(PDFImage.from_file("guitar.jpg"), lossless = False, max_resolution_dpi = 150)
		pdf.add_image(PDFImage.from_file("test.png"), lossless = True, pixel_format = PixelFormat.BlackWhite, max_resolution_dpi = 150)
