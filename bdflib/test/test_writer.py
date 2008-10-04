import unittest
try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO

from bdflib import model, writer

class TestBDFWriter(unittest.TestCase):

	def setUp(self):
		self.font = model.Font("TestFont", 12, 100,100)

	def test_basic_writing(self):
		"""
		Writing out a simple font should work.
		"""
		self.font.new_glyph_from_data("TestGlyph", ["4", "8"], 0,0, 2,2, 3, 1)

		stream = StringIO()
		writer.write_bdf(self.font, stream)

		self.failUnlessEqual(stream.getvalue(),
				"STARTFONT 2.1\n"
				"FONT TestFont\n"
				"SIZE 12 100 100\n"
				"FONTBOUNDINGBOX 2 2 0 0\n"
				"STARTPROPERTIES 8\n"
				"DEFAULT_CHAR 1\n"
				"FACE_NAME \"TestFont\"\n"
				"FONT_ASCENT 2\n"
				"FONT_DESCENT 0\n"
				"PIXEL_SIZE 17\n"
				"POINT_SIZE 120\n"
				"RESOLUTION_X 100\n"
				"RESOLUTION_Y 100\n"
				"ENDPROPERTIES\n"
				"CHARS 1\n"
				"STARTCHAR TestGlyph\n"
				"ENCODING 1\n"
				"SWIDTH 176 0\n"
				"DWIDTH 3 0\n"
				"BBX 2 2 0 0\n"
				"BITMAP\n"
				"40\n"
				"80\n"
				"ENDCHAR\n"
				"ENDFONT\n"
			)

	def test_empty_font(self):
		"""
		We should be able to write an empty font.
		"""
		stream = StringIO()
		writer.write_bdf(self.font, stream)

		self.failUnlessEqual(stream.getvalue(),
				"STARTFONT 2.1\n"
				"FONT TestFont\n"
				"SIZE 12 100 100\n"
				"FONTBOUNDINGBOX 0 0 0 0\n"
				"STARTPROPERTIES 7\n"
				"FACE_NAME \"TestFont\"\n"
				"FONT_ASCENT 0\n"
				"FONT_DESCENT 0\n"
				"PIXEL_SIZE 17\n"
				"POINT_SIZE 120\n"
				"RESOLUTION_X 100\n"
				"RESOLUTION_Y 100\n"
				"ENDPROPERTIES\n"
				"CHARS 0\n"
				"ENDFONT\n"
			)

	def test_bounding_box_calculations(self):
		"""
		FONTBOUNDINGBOX should be calculated from individual glyphs.
		"""
		self.font.new_glyph_from_data("TestGlyph1", ["4", "8"],
				1,3, 2,2, 3, 1)
		self.font.new_glyph_from_data("TestGlyph2", ["4", "8"],
				-5,-7, 2,2, 1, 2)

		stream = StringIO()
		writer.write_bdf(self.font, stream)

		self.failUnlessEqual(stream.getvalue(),
				"STARTFONT 2.1\n"
				"FONT TestFont\n"
				"SIZE 12 100 100\n"
				"FONTBOUNDINGBOX 8 12 -5 -7\n"
				"STARTPROPERTIES 8\n"
				"DEFAULT_CHAR 2\n"
				"FACE_NAME \"TestFont\"\n"
				"FONT_ASCENT 5\n"
				"FONT_DESCENT 7\n"
				"PIXEL_SIZE 17\n"
				"POINT_SIZE 120\n"
				"RESOLUTION_X 100\n"
				"RESOLUTION_Y 100\n"
				"ENDPROPERTIES\n"
				"CHARS 2\n"
				"STARTCHAR TestGlyph1\n"
				"ENCODING 1\n"
				"SWIDTH 176 0\n"
				"DWIDTH 3 0\n"
				"BBX 2 2 1 3\n"
				"BITMAP\n"
				"40\n"
				"80\n"
				"ENDCHAR\n"
				"STARTCHAR TestGlyph2\n"
				"ENCODING 2\n"
				"SWIDTH 58 0\n"
				"DWIDTH 1 0\n"
				"BBX 2 2 -5 -7\n"
				"BITMAP\n"
				"40\n"
				"80\n"
				"ENDCHAR\n"
				"ENDFONT\n"
			)

	def test_property_quoting(self):
		"""
		Test that property values are quoted properly.
		"""

		self.font["AN_INTEGER"] = 42
		self.font["A_STRING"] = "42"
		self.font["STRING_WITH_QUOTES"] = 'Neville "The Banker" Robinson'

		stream = StringIO()
		writer.write_bdf(self.font, stream)

		self.failUnlessEqual(stream.getvalue(),
				"STARTFONT 2.1\n"
				"FONT TestFont\n"
				"SIZE 12 100 100\n"
				"FONTBOUNDINGBOX 0 0 0 0\n"
				"STARTPROPERTIES 10\n"
				"AN_INTEGER 42\n"
				"A_STRING \"42\"\n"
				"FACE_NAME \"TestFont\"\n"
				"FONT_ASCENT 0\n"
				"FONT_DESCENT 0\n"
				"PIXEL_SIZE 17\n"
				"POINT_SIZE 120\n"
				"RESOLUTION_X 100\n"
				"RESOLUTION_Y 100\n"
				"STRING_WITH_QUOTES \"Neville \"\"The Banker\"\" Robinson\"\n"
				"ENDPROPERTIES\n"
				"CHARS 0\n"
				"ENDFONT\n"
			)

	def test_default_char_setting(self):
		"""
		If a default char is explicitly set, it should be used.
		"""
		self.font.new_glyph_from_data("TestGlyph1", ["4", "8"],
				0,0, 2,2, 3, 1)
		self.font.new_glyph_from_data("TestGlyph2", ["8", "4"],
				0,0, 2,2, 3, 0xFFFD)
		self.font["DEFAULT_CHAR"] = 0xFFFD

		stream = StringIO()
		writer.write_bdf(self.font, stream)

		self.failUnlessEqual(stream.getvalue(),
				"STARTFONT 2.1\n"
				"FONT TestFont\n"
				"SIZE 12 100 100\n"
				"FONTBOUNDINGBOX 2 2 0 0\n"
				"STARTPROPERTIES 8\n"
				"DEFAULT_CHAR 65533\n"
				"FACE_NAME \"TestFont\"\n"
				"FONT_ASCENT 2\n"
				"FONT_DESCENT 0\n"
				"PIXEL_SIZE 17\n"
				"POINT_SIZE 120\n"
				"RESOLUTION_X 100\n"
				"RESOLUTION_Y 100\n"
				"ENDPROPERTIES\n"
				"CHARS 2\n"
				"STARTCHAR TestGlyph1\n"
				"ENCODING 1\n"
				"SWIDTH 176 0\n"
				"DWIDTH 3 0\n"
				"BBX 2 2 0 0\n"
				"BITMAP\n"
				"40\n"
				"80\n"
				"ENDCHAR\n"
				"STARTCHAR TestGlyph2\n"
				"ENCODING 65533\n"
				"SWIDTH 176 0\n"
				"DWIDTH 3 0\n"
				"BBX 2 2 0 0\n"
				"BITMAP\n"
				"80\n"
				"40\n"
				"ENDCHAR\n"
				"ENDFONT\n"
			)

	def test_resolution_calculations(self):
		"""
		The pixel size should be correctly calculated from the point size.
		"""
		tests = [
				(12, 72, 12),
				(12, 100, 17),
				(12.2, 100, 17),
				(12, 144, 24),
			]

		for pointSz, res, pixelSz in tests:
			deci_pointSz = int(pointSz * 10)

			font = model.Font("TestFont", pointSz, res, res)

			stream = StringIO()
			writer.write_bdf(font, stream)

			self.failUnlessEqual(stream.getvalue(),
					"STARTFONT 2.1\n"
					"FONT TestFont\n"
					"SIZE %(pointSz)g %(res)d %(res)d\n"
					"FONTBOUNDINGBOX 0 0 0 0\n"
					"STARTPROPERTIES 7\n"
					"FACE_NAME \"TestFont\"\n"
					"FONT_ASCENT 0\n"
					"FONT_DESCENT 0\n"
					"PIXEL_SIZE %(pixelSz)d\n"
					"POINT_SIZE %(deci_pointSz)d\n"
					"RESOLUTION_X %(res)s\n"
					"RESOLUTION_Y %(res)s\n"
					"ENDPROPERTIES\n"
					"CHARS 0\n"
					"ENDFONT\n"
					% locals()
				)

