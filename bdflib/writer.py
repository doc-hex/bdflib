# bdflib, a library for working with BDF font files
# Copyright (C) 2009, Timothy Alle
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Tools to write a Font object to a BDF File.
"""
import math

def _quote_property_value(val):
	if isinstance(val, int):
		return str(val)
	else:
		return '"%s"' % (str(val).replace('"', '""'),)

def write_bdf(font, stream):
	"""
	Write the given font object to the given stream as a BDF font.
	"""
	# The font bounding box is the union of glyph bounding boxes.
	font_bbX = 0
	font_bbY = 0
	font_bbW = 0
	font_bbH = 0
	for g in font.glyphs:
		new_bbX = min(font_bbX, g.bbX)
		new_bbY = min(font_bbY, g.bbY)
		new_bbW = max(font_bbX + font_bbW, g.bbX + g.bbW) - new_bbX
		new_bbH = max(font_bbY + font_bbH, g.bbY + g.bbH) - new_bbY

		(font_bbX, font_bbY, font_bbW, font_bbH) = (
				new_bbX, new_bbY, new_bbW, new_bbH)

	# Calculated properties that aren't in the font model.
	properties = {
			"PIXEL_SIZE": int(math.ceil(
				font["RESOLUTION_Y"] * font["POINT_SIZE"] / 72.0)),
			"FONT_ASCENT": font_bbY + font_bbH,
			"FONT_DESCENT": font_bbY * -1,
		}
	if len(font.glyphs_by_codepoint) > 0:
		properties["DEFAULT_CHAR"] = max(font.glyphs_by_codepoint.keys())
	properties.update(font.properties)

	# The POINT_SIZE property is actually in deci-points.
	properties["POINT_SIZE"] = int(properties["POINT_SIZE"] * 10)

	# Write the basic header.
	stream.write("STARTFONT 2.1\n")
	stream.write("FONT %s\n" % (font["FACE_NAME"],))
	stream.write("SIZE %g %d %d\n" %
			(font["POINT_SIZE"], font["RESOLUTION_X"], font["RESOLUTION_Y"]))
	stream.write("FONTBOUNDINGBOX %d %d %d %d\n"
			% (font_bbW, font_bbH, font_bbX, font_bbY))

	# Write the properties
	stream.write("STARTPROPERTIES %d\n" % (len(properties),))
	keys = sorted(properties.keys())
	for key in keys:
		stream.write("%s %s\n" % (key,
			_quote_property_value(properties[key])))
	stream.write("ENDPROPERTIES\n")

	# Write out the glyphs
	stream.write("CHARS %d\n" % (len(font.glyphs),))
	for glyph in font.glyphs:
		scalable_width = int(1000.0 * glyph.advance
				/ properties["PIXEL_SIZE"])
		stream.write("STARTCHAR %s\n" % (glyph.name,))
		stream.write("ENCODING %d\n" % (glyph.codepoint,))
		stream.write("SWIDTH %d 0\n" % (scalable_width,))
		stream.write("DWIDTH %d 0\n" % (glyph.advance,))
		stream.write("BBX %d %d %d %d\n"
				% (glyph.bbW, glyph.bbH, glyph.bbX, glyph.bbY))
		stream.write("BITMAP\n")
		for row in glyph.get_data():
			stream.write("%s\n" % (row,))
		stream.write("ENDCHAR\n")

	stream.write("ENDFONT\n")
