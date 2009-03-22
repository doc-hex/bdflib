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
Code to build font and glyph objects from a BDF font.
"""
from bdflib import model

def _read_glyph(iterable, font):
	glyphName = ""
	codepoint = -1
	bbX = 0
	bbY = 0
	bbW = 0
	bbH = 0
	advance = 0
	data = []

	for line in iterable:
		parts = line.strip().split(' ')
		key = parts[0]
		values = parts[1:]

		if key == "STARTCHAR":
			glyphName = " ".join(values)
		elif key == "ENCODING":
			codepoint = int(values[0])
		elif key == "DWIDTH":
			advance = int(values[0])
		elif key == "BBX":
			bbW, bbH, bbX, bbY = [int(val) for val in values]
		elif key == "BITMAP":
			# The next bbH lines describe the font bitmap.
			data = [iterable.next().strip() for i in range(bbH)]
			assert iterable.next().strip() == "ENDCHAR"
			break

	font.new_glyph_from_data(glyphName, data, bbX, bbY, bbW, bbH, advance,
			codepoint)


def _unquote_property_value(value):
	if value[0] == '"':
		# Must be a string. Remove the outer quotes and un-escape embedded
		# quotes.
		return value[1:-1].replace('""', '"')
	else:
		# No quotes, must be an integer.
		return int(value)


def _read_property(iterable, font):
	key, value = iterable.next().strip().split(' ', 1)

	font[key] = _unquote_property_value(value)


def read_bdf(iterable):
	"""
	Read a BDF-format font from the given source.

	iterable should be an iterable that yields a string for each line of the
	BDF file - for example, a list of strings, or a file-like object.
	"""
	name = ""
	pointSize = 0.0
	resX = 0
	resY = 0
	comments = []
	font = None

	for line in iterable:
		parts = line.strip().split(' ')
		key = parts[0]
		values = parts[1:]

		if key == "COMMENT":
			comments.append(" ".join(values))
		elif key == "FONT":
			name = " ".join(values)
		elif key == "SIZE":
			pointSize = float(values[0])
			resX = int(values[1])
			resY = int(values[2])
		elif key == "FONTBOUNDINGBOX":
			# We don't care about the font bounding box, but it's the last
			# header to come before the variable-length fields for which we
			# need a font object around.
			font = model.Font(name, pointSize, resX, resY)
			for c in comments:
				font.add_comment(c)
		elif key == "STARTPROPERTIES":
			propertyCount = int(values[0])
			[_read_property(iterable, font) for i in range(propertyCount)]

			assert iterable.next().strip() == "ENDPROPERTIES"
		elif key == "CHARS":
			glyphCount = int(values[0])
			[_read_glyph(iterable, font) for i in range(glyphCount)]
			break

	assert iterable.next().strip() == "ENDFONT"

	return font
