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

	def test_glyph_merging_no_op(self):
		f = model.Font("TestFont", 12, 100,100)
		g = f.new_glyph_from_data("TestGlyph", ["4", "8"], 0,0, 2,2, 3, 1)

		# Draw this glyph onto itself at 0,0
		g.merge_glyph(g, 0,0)

		# Nothing should have changed.
		self.failUnlessEqual(g.get_bounding_box(), (0,0, 2,2))
		self.failUnlessEqual(g.get_data(), ["4", "8"])
		self.failUnlessEqual(g.advance, 3)

	def test_glyph_merging_above(self):
		f = model.Font("TestFont", 12, 100,100)
		g = f.new_glyph_from_data("TestGlyph", ["4", "8"], 0,0, 2,2, 3, 1)

		# Draw this glyph onto itself but a few rows higher.
		g.merge_glyph(g, 0,4)

		# The bounding box should be higher.
		self.failUnlessEqual(g.get_bounding_box(), (0,0, 2,6))

		# The advance shouldn't have changed.
		self.failUnlessEqual(g.advance, 3)

		# There should be some blank rows in the bitmap
		self.failUnlessEqual(g.get_data(), ["4", "8", "0", "0", "4", "8"])

	def test_glyph_merging_below(self):
		f = model.Font("TestFont", 12, 100,100)
		g = f.new_glyph_from_data("TestGlyph", ["4", "8"], 0,0, 2,2, 3, 1)

		# Draw this glyph onto itself but a row lower.
		g.merge_glyph(g, 0,-3)

		# The origin vector should have moved downward, and the height
		# increased to compensate.
		self.failUnlessEqual(g.get_bounding_box(), (0,-3, 2,5))

		# The advance shouldn't have changed.
		self.failUnlessEqual(g.advance, 3)

		# There should be a blank row in the bitmap
		self.failUnlessEqual(g.get_data(), ["4", "8", "0", "4", "8"])

	def test_glyph_merging_left(self):
		f = model.Font("TestFont", 12, 100,100)
		g = f.new_glyph_from_data("TestGlyph", ["4", "8"], 0,0, 2,2, 3, 1)

		# Draw this glyph onto itself a few columns to the left.
		g.merge_glyph(g, -4,0)

		# The origin vector should have moved left, and the width enlarged to
		# compensate.
		self.failUnlessEqual(g.get_bounding_box(), (-4,0, 6,2))

		# The advance shouldn't have changed, since we didn't add anything
		# right of the origin.
		self.failUnlessEqual(g.advance, 3)

		# The bitmap should be wider.
		self.failUnlessEqual(g.get_data(), ["44", "88"])

	def test_glyph_merging_right(self):
		f = model.Font("TestFont", 12, 100,100)
		g = f.new_glyph_from_data("TestGlyph", ["4", "8"], 0,0, 2,2, 3, 1)

		# Draw this glyph onto itself a few columns to the right.
		g.merge_glyph(g, 3,0)

		# The origin vector should be the same, and the width enlarged.
		self.failUnlessEqual(g.get_bounding_box(), (0,0, 5,2))

		# The advance have enlarged, since we drew to the right of the origin.
		self.failUnlessEqual(g.advance, 6)

		# The bitmap should be wider.
		self.failUnlessEqual(g.get_data(), ["48", "90"])

	def test_glyph_merging(self):
		f = model.Font("TestFont", 12, 100,100)
		g = f.new_glyph_from_data("TestGlyph", ["4", "8"], 0,0, 2,2, 3, 1)

		# Draw this glyph onto itself at 2,2
		g.merge_glyph(g, 2,2)

		# Check the results
		self.failUnlessEqual(g.get_bounding_box(), (0,0, 4,4))
		self.failUnlessEqual(g.advance, 5)
		self.failUnlessEqual(g.get_data(), ["1", "2", "4", "8"])

	def test_glyph_printing(self):

		# A small circle
		glyph_data = ["70", "88", "88", "88", "70"]

		f = model.Font("TestFont", 12, 100,100)
		glyphs = []
		for offset in range(0,7):
			glyphs.append(f.new_glyph_from_data(
					"TestGlyph%d" % offset,
					glyph_data,
					-5 + offset, -5 + offset,
					5,5,
					offset,
					offset,
				))

		for g in glyphs:
			print g
			print

		self.failUnlessEqual([str(g) for g in glyphs],
				[
					"-----+\n"
					".###.|\n"
					"#...#|\n"
					"#...#|\n"
					"#...#|\n"
					".###.|",

					"-###+\n"
					"#...#\n"
					"#...#\n"
					"#...#\n"
					".###|",

					".###.\n"
					"#--+#\n"
					"#..|#\n"
					"#..|#\n"
					".###.",

					".###.\n"
					"#.|.#\n"
					"#-+-#\n"
					"#.|.#\n"
					".###.",

					".###.\n"
					"#|..#\n"
					"#|..#\n"
					"#+--#\n"
					".###.",

					"|###.\n"
					"#...#\n"
					"#...#\n"
					"#...#\n"
					"+###-",

					"|.###.\n"
					"|#...#\n"
					"|#...#\n"
					"|#...#\n"
					"|.###.\n"
					"+-----",
				]
			)
