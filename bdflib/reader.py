"""
Code to build font and glyph objects from a BDF font.
"""
from bdflib import model

def _read_glyph(iterator, font):
	glyphName = ""
	codepoint = -1
	bbX = 0
	bbY = 0
	bbW = 0
	bbH = 0
	advance = 0
	data = []

	for line in iterator:
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
			data = [iterator.next().strip() for i in range(bbH)]
			break

	assert iterator.next() == "ENDCHAR"

	font.new_glyph_from_data(glyphName, data, bbX, bbY, bbW, bbH, advance,
			codepoint)


def _read_property(iterator, font):
	def parse_property(value):
		if value[0] == '"':
			return value[1:-1].replace('""', '"')
		else:
			return int(value)

	key, value = iterator.next().strip().split(' ', 1)

	font[key] = parse_property(value)


def _read_font(iterator):
	name = ""
	pointSize = 0.0
	resX = 0
	resY = 0
	comments = []
	font = None

	for line in iterator:
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
			[_read_property(iterator, font) for i in range(propertyCount)]

			assert iterator.next() == "ENDPROPERTIES"
		elif key == "CHARS":
			glyphCount = int(values[0])
			[_read_glyph(iterator, font) for i in range(glyphCount)]
			break

	assert iterator.next() == "ENDFONT"

	return font


def read_from_iterable(iterable):
	return _read_font(iter(iterable))


def read_from_file(filename):
	return read_from_iterable(open(filename, 'r'))


def read_from_string(string):
	return read_from_iterable(string.split("\n"))
