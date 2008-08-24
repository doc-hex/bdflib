import unittest

from bdflib import model

class TestFont(unittest.TestCase):

	def test_basic_properties(self):
		f = model.Font("TestFont", 12, 100,100)
		
		# Test that we're copying the values to BDF properties properly.
		self.failUnlessEqual(f["FACE_NAME"], "TestFont")
		self.failUnlessEqual(f["POINT_SIZE"], 12)
		self.failUnlessEqual(f["PIXEL_SIZE"], 17)
		self.failUnlessEqual(f["RESOLUTION_X"], 100)
		self.failUnlessEqual(f["RESOLUTION_Y"], 100)

	def test_property_setting(self):
		f = model.Font("TestFont", 12, 100,100)
		f["CHARSET_REGISTRY"] = "iso8859"
		self.failUnlessEqual(f["CHARSET_REGISTRY"], "iso8859")

	def test_comments(self):
		f = model.Font("TestFont", 12, 100,100)
		f.add_comment("This is another comment")
		f.add_comment("hello, world!\nMultiple lines!")
		self.failUnlessEqual(f.get_comments(),
				[
					"This is another comment",
					"hello, world!",
					"Multiple lines!",
				]
			)

class TestGlyph(unittest.TestCase):

	def test_glyph_creation(self):
		f = model.Font("TestFont", 12, 100,100)
		g = f.new_glyph_from_data("TestGlyph", ["1", "0", "0", "0", "0", "8"],
				-3,-4, 4,6, 8, 1)

		self.failUnlessEqual(g.name, "TestGlyph")
		self.failUnlessEqual(g.get_data(), ["1", "0", "0", "0", "0", "8"])
		self.failUnlessEqual(g.get_bounding_box(), (-3,-4, 4,6))
		self.failUnlessEqual(g.advance, 8)
		self.failUnlessEqual(g.codepoint, 1)
		self.failUnlessEqual(f[g.codepoint], g)

	def test_duplicate_codepoints(self):
		f = model.Font("TestFont", 12, 100,100)
		g = f.new_glyph_from_data("TestGlyph1", codepoint=1)

		self.failUnlessRaises(model.GlyphExists, f.new_glyph_from_data,
				"TestGlyph2", codepoint=1)

	def test_glyph_merging(self):
		f = model.Font("TestFont", 12, 100,100)
		g = f.new_glyph_from_data("TestGlyph", ["4", "8"], 0,0, 2,2, 3, 1)

		# Draw this glyph onto itself at 2,2
		g.merge_glyph(g, 2,2)

		# Check the results
		self.failUnlessEqual(g.get_data(), ["1", "2", "4", "8"])
		self.failUnlessEqual(g.get_bounding_box(), (0,0, 4,4))
		self.failUnlessEqual(g.advance, 5)
