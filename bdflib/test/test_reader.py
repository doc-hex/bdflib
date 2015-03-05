import unittest
import tempfile
try:
	from io import StringIO
except ImportError:
	from io import StringIO

from bdflib import model, reader

# This comes from the X11 BDF spec.
SAMPLE_FONT = """
STARTFONT 2.1
COMMENT This is a sample font in 2.1 format.
FONT -Adobe-Helvetica-Bold-R-Normal--24-240-75-75-P-65-ISO8859-1
SIZE 24 75 75
FONTBOUNDINGBOX 9 24 -2 -6
STARTPROPERTIES 19
FOUNDRY "Adobe"
FAMILY "Helvetica"
WEIGHT_NAME "Bold"
SLANT "R"
SETWIDTH_NAME "Normal"
ADD_STYLE_NAME ""
PIXEL_SIZE 24
POINT_SIZE 240
RESOLUTION_X 75
RESOLUTION_Y 75
SPACING "P"
AVERAGE_WIDTH 65
CHARSET_REGISTRY "ISO8859"
CHARSET_ENCODING "1"
MIN_SPACE 4
FONT_ASCENT 21
FONT_DESCENT 7
COPYRIGHT "Copyright (c) 1987 Adobe Systems, Inc."
NOTICE "Helvetica is a registered trademark of Linotype Inc."
ENDPROPERTIES
CHARS 2
STARTCHAR j
ENCODING 106
SWIDTH 355 0
DWIDTH 8 0
BBX 9 22 -2 -6
BITMAP
0380
0380
0380
0380
0000
0700
0700
0700
0700
0E00
0E00
0E00
0E00
0E00
1C00
1C00
1C00
1C00
3C00
7800
F000
E000
ENDCHAR
STARTCHAR quoteright
ENCODING 39
SWIDTH 223 0
DWIDTH 5 0
BBX 4 6 2 12
ATTRIBUTES 01C0
BITMAP
70
70
70
60
E0
C0
ENDCHAR
ENDFONT
""".strip()


class TestGlyph(unittest.TestCase):

	def test_basic_operation(self):
		testFont = model.Font("Adobe Helvetica", 24, 75, 75)
		testGlyphData = iter(SAMPLE_FONT.split('\n')[27:56])

		reader._read_glyph(testGlyphData, testFont)

		# The font should now have an entry for j.
		testGlyph = testFont[106]

		# The glyph should have the correct header data.
		self.assertEqual(testGlyph.name, 'j')
		self.assertEqual(testGlyph.codepoint, 106)
		self.assertEqual(testGlyph.advance, 8)
		self.assertEqual(testGlyph.bbX, -2)
		self.assertEqual(testGlyph.bbY, -6)
		self.assertEqual(testGlyph.bbW,  9)
		self.assertEqual(testGlyph.bbH, 22)

		# Make sure we got the correct glyph bitmap.
		self.assertEqual(str(testGlyph),
				'..|...###\n'
				'..|...###\n'
				'..|...###\n'
				'..|...###\n'
				'..|......\n'
				'..|..###.\n'
				'..|..###.\n'
				'..|..###.\n'
				'..|..###.\n'
				'..|.###..\n'
				'..|.###..\n'
				'..|.###..\n'
				'..|.###..\n'
				'..|.###..\n'
				'..|###...\n'
				'--+###---\n'
				'..|###...\n'
				'..|###...\n'
				'..####...\n'
				'.####....\n'
				'####.....\n'
				'###......'
			)

		# The iterator should have nothing left in it.
		self.assertRaises(StopIteration, testGlyphData.__next__)


class TestReadProperty(unittest.TestCase):

	def test_basic_operation(self):
		testFont = model.Font("Adobe Helvetica", 24, 75, 75)
		testProperties = iter(SAMPLE_FONT.split('\n')[6:26])

		for i in range(19):
			reader._read_property(testProperties, testFont)

		# After reading the properties, the iterator should be just up to the
		# ENDPROPERTIES line.
		self.assertEqual(next(testProperties), "ENDPROPERTIES")

		# Test that the properties were read correctly.
		self.assertEqual(testFont['FOUNDRY'], "Adobe")
		self.assertEqual(testFont['FAMILY'], "Helvetica")
		self.assertEqual(testFont['WEIGHT_NAME'], "Bold")
		self.assertEqual(testFont['SLANT'], "R")
		self.assertEqual(testFont['SETWIDTH_NAME'], "Normal")
		self.assertEqual(testFont['ADD_STYLE_NAME'], "")
		self.assertEqual(testFont['POINT_SIZE'], 24.0)
		self.assertEqual(testFont['RESOLUTION_X'], 75)
		self.assertEqual(testFont['RESOLUTION_Y'], 75)
		self.assertEqual(testFont['SPACING'], "P")
		self.assertEqual(testFont['AVERAGE_WIDTH'], 65)
		self.assertEqual(testFont['CHARSET_REGISTRY'], "ISO8859")
		self.assertEqual(testFont['CHARSET_ENCODING'], "1")
		self.assertEqual(testFont['MIN_SPACE'], 4)
		self.assertEqual(testFont['FONT_ASCENT'], 21)
		self.assertEqual(testFont['FONT_DESCENT'], 7)
		self.assertEqual(testFont['COPYRIGHT'],
				"Copyright (c) 1987 Adobe Systems, Inc.")
		self.assertEqual(testFont['NOTICE'],
				"Helvetica is a registered trademark of Linotype Inc.")


class TestReadFont(unittest.TestCase):

	def _check_font(self, font):
		"""
		Checks that the given font is a representation of the sample font.
		"""
		self.assertEqual(font["FACE_NAME"],
				"-Adobe-Helvetica-Bold-R-Normal--24-240-75-75-P-65-ISO8859-1")
		self.assertEqual(font["POINT_SIZE"], 24.0)
		self.assertEqual(font["RESOLUTION_X"], 75)
		self.assertEqual(font["RESOLUTION_Y"], 75)
		self.assertEqual(font.get_comments(), [
				"This is a sample font in 2.1 format."
			])
		self.assertEqual(len(font.glyphs), 2)
		# Our code ignores PIXEL_SIZE but adds FACE_NAME, so the total is still
		# 19.
		self.assertEqual(len(font.properties), 19)

	def test_basic_operation(self):
		testFontData = StringIO(SAMPLE_FONT)
		testFont = reader.read_bdf(testFontData)

		self._check_font(testFont)

	def test_fractional_point_size(self):
		"""
		We should correctly interpret and store a fractional point size.
		"""
		bdf_data = (
				"STARTFONT 2.1\n"
				"FONT TestFont\n"
				"SIZE 12.2 100 100\n"
				"FONTBOUNDINGBOX 0 0 0 0\n"
				"STARTPROPERTIES 5\n"
				"FACE_NAME \"TestFont\"\n"
				"FONT_ASCENT 0\n"
				"FONT_DESCENT 0\n"
				"RESOLUTION_X 100\n"
				"RESOLUTION_Y 100\n"
				"ENDPROPERTIES\n"
				"CHARS 0\n"
				"ENDFONT\n"
			)

		font = reader.read_bdf(StringIO(bdf_data))

		self.assertEqual("%0.1f" % font["POINT_SIZE"], "12.2")

	def test_ignored_properties(self):
		"""
		Certain properties can't be set.

		These properties include:
		 - FACE_NAME: comes from FONT header.
		 - POINT_SIZE: comes from SIZE header.
		 - RESOLUTION_X: comes from SIZE header.
		 - RESOLUTION_Y: comes from SIZE header.
		 - PIXEL_SIZE: calculated from 3 previous properties.
		"""

		bdf_data = (
				"STARTFONT 2.1\n"
				"FONT TestFont\n"
				"SIZE 1 2 3\n"
				"FONTBOUNDINGBOX 0 0 0 0\n"
				"STARTPROPERTIES 5\n"
				"FACE_NAME \"NotATestFont\"\n"
				"POINT_SIZE 456\n"
				"PIXEL_SIZE 789\n"
				"RESOLUTION_X 012\n"
				"RESOLUTION_Y 345\n"
				"ENDPROPERTIES\n"
				"CHARS 0\n"
				"ENDFONT\n"
			)

		font = reader.read_bdf(StringIO(bdf_data))

		self.assertEqual(font["FACE_NAME"], "TestFont")
		self.assertEqual("%0.1f" % font["POINT_SIZE"], "1.0")
		self.assertEqual(font["RESOLUTION_X"], 2)
		self.assertEqual(font["RESOLUTION_Y"], 3)
		self.assertFalse("PIXEL_SIZE" in font)
