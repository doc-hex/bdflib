import unittest

from bdflib import model

class TestFont(unittest.TestCase):

	def test_basic_properties(self):
		f = model.Font("TestFont", 12, 100,100)
		
		# Test that we're copying the values to BDF properties properly.
		self.failUnlessEqual(f["FACE_NAME"], "TestFont")
		self.failUnlessEqual(f["POINT_SIZE"], 12)
		self.failUnlessEqual(f["RESOLUTION_X"], 100)
		self.failUnlessEqual(f["RESOLUTION_Y"], 100)

	def test_property_setting(self):
		f = model.Font("TestFont", 12, 100,100)
		f["CHARSET_REGISTRY"] = "iso8859"
		self.failUnlessEqual(f["CHARSET_REGISTRY"], "iso8859")

		# Test that properties set in the font header can't be overridden by
		# ordinary properties.
		f["FACE_NAME"] = "blargle"
		f["POINT_SIZE"] = 999
		f["RESOLUTION_X"] = 999
		f["RESOLUTION_Y"] = 999

		self.failUnlessEqual(f["FACE_NAME"], "TestFont")
		self.failUnlessEqual(f["POINT_SIZE"], 12)
		self.failUnlessEqual(f["RESOLUTION_X"], 100)
		self.failUnlessEqual(f["RESOLUTION_Y"], 100)

		# PIXEL_SIZE is not explicitly set in the header, but can be calculated
		# from POINT_SIZE and RESOLUTION_Y, so it needn't be set explicitly.
		f["PIXEL_SIZE"] = 999

		self.failUnless("PIXEL_SIZE" not in f)

	def test_property_iteration(self):
		f = model.Font("TestFont", 12, 100,100)

		keys = list(f.property_names())
		keys.sort()

		self.failUnlessEqual(keys, ["FACE_NAME", "POINT_SIZE", "RESOLUTION_X",
				"RESOLUTION_Y"])

	def test_codepoint_iteration(self):
		f = model.Font("TestFont", 12, 100,100)

		# Add glyphs at code-points out-of-order.
		f.new_glyph_from_data("TestGlyph", ["4", "8"], 0,0, 2,2, 3, 5)
		f.new_glyph_from_data("TestGlyph", ["4", "8"], 0,0, 2,2, 3, 16)
		f.new_glyph_from_data("TestGlyph", ["4", "8"], 0,0, 2,2, 3, 37)
		f.new_glyph_from_data("TestGlyph", ["4", "8"], 0,0, 2,2, 3, 93)

		codepoints = list(f.codepoints())
		codepoints.sort()

		self.failUnlessEqual(codepoints, [5,16,37,93])

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

	def test_font_copying(self):
		f = model.Font("TestFont", 12, 100,100)
		g = f.new_glyph_from_data("TestGlyph", ["1", "0", "0", "0", "0", "8"],
				-3,-4, 4,6, 8, 1)

		f2 = f.copy()
		g2 = f2[1]

		self.failUnlessEqual(g2.name, "TestGlyph")
		self.failUnlessEqual(g2.get_data(),
				["10", "00", "00", "00", "00", "80"])
		self.failUnlessEqual(g2.get_bounding_box(), (-3,-4, 4,6))
		self.failUnlessEqual(g2.advance, 8)
		self.failUnlessEqual(g2.codepoint, 1)
		self.failUnlessEqual(f2[g2.codepoint], g2)


class TestGlyph(unittest.TestCase):

	def test_glyph_creation(self):
		f = model.Font("TestFont", 12, 100,100)
		g = f.new_glyph_from_data("TestGlyph", ["1", "0", "0", "0", "0", "8"],
				-3,-4, 4,6, 8, 1)

		self.failUnlessEqual(g.name, "TestGlyph")
		self.failUnlessEqual(g.get_data(),
				["10", "00", "00", "00", "00", "80"])
		self.failUnlessEqual(g.get_bounding_box(), (-3,-4, 4,6))
		self.failUnlessEqual(g.advance, 8)
		self.failUnlessEqual(g.codepoint, 1)
		self.failUnlessEqual(f[g.codepoint], g)

	def test_glyph_data_case(self):
		"""
		gbdfed writes upper-case hex digits, so we should too.
		"""
		f = model.Font("TestFont", 12, 100,100)
		g = f.new_glyph_from_data("TestGlyph",
				["a", "b", "c", "d", "e", "f"],
				bbW=4, bbH=6, advance=5)

		self.failUnlessEqual(g.get_data(),
				["A0", "B0", "C0", "D0", "E0", "F0"])

	def test_glyphs_should_be_zero_padded(self):
		"""
		Each row of the bitmap should be zero-padded to the same length.
		"""
		f = model.Font("TestFont", 12, 100,100)

		# When a glyph is multiple hex-digits wide and a row has no bits set in
		# the left-most columns, a zero should be placed there.
		g = f.new_glyph_from_data("TestGlyph", ["001", "800"],
				bbW=12, bbH=2)
		self.failUnlessEqual(g.get_data(), ["0010", "8000"])

		# When a glyph's width doesn't take up a full number of hex digits, the
		# row width should be rounded up to the nearest integer number of
		# digits, not down.
		g = f.new_glyph_from_data("TestGlyph", ["010", "800"],
				bbW=11, bbH=2)
		self.failUnlessEqual(g.get_data(), ["0100", "8000"])

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
		self.failUnlessEqual(g.get_data(), ["40", "80"])

	def test_glyph_merging_above(self):
		f = model.Font("TestFont", 12, 100,100)
		g = f.new_glyph_from_data("TestGlyph", ["4", "8"], 0,0, 2,2, 3, 1)

		# Draw this glyph onto itself but a few rows higher.
		g.merge_glyph(g, 0,4)

		# The bounding box should be higher.
		self.failUnlessEqual(g.get_bounding_box(), (0,0, 2,6))

		# There should be some blank rows in the bitmap
		self.failUnlessEqual(g.get_data(),
				["40", "80", "00", "00", "40", "80"])

	def test_glyph_merging_below(self):
		f = model.Font("TestFont", 12, 100,100)
		g = f.new_glyph_from_data("TestGlyph", ["4", "8"], 0,0, 2,2, 3, 1)

		# Draw this glyph onto itself but a row lower.
		g.merge_glyph(g, 0,-3)

		# The origin vector should have moved downward, and the height
		# increased to compensate.
		self.failUnlessEqual(g.get_bounding_box(), (0,-3, 2,5))

		# There should be a blank row in the bitmap
		self.failUnlessEqual(g.get_data(), ["40", "80", "00", "40", "80"])

	def test_glyph_merging_left(self):
		f = model.Font("TestFont", 12, 100,100)
		g = f.new_glyph_from_data("TestGlyph", ["4", "8"], 0,0, 2,2, 3, 1)

		# Draw this glyph onto itself a few columns to the left.
		g.merge_glyph(g, -4,0)

		# The origin vector should have moved left, and the width enlarged to
		# compensate.
		self.failUnlessEqual(g.get_bounding_box(), (-4,0, 6,2))

		# The bitmap should be wider.
		self.failUnlessEqual(g.get_data(), ["44", "88"])

	def test_glyph_merging_right(self):
		f = model.Font("TestFont", 12, 100,100)
		g = f.new_glyph_from_data("TestGlyph", ["4", "8"], 0,0, 2,2, 3, 1)

		# Draw this glyph onto itself a few columns to the right.
		g.merge_glyph(g, 3,0)

		# The origin vector should be the same, and the width enlarged.
		self.failUnlessEqual(g.get_bounding_box(), (0,0, 5,2))

		# The bitmap should be wider.
		self.failUnlessEqual(g.get_data(), ["48", "90"])

	def test_glyph_merging_offset_glyph(self):
		"""
		Merging a glyph whose bitmap doesn't start at (0,0)
		"""
		f = model.Font("TestFont", 12, 100,100)
		g = f.new_glyph_from_data("TestGlyph", ["4", "8"], 1,1, 2,2, 3, 1)

		# Draw this glyph onto itself to make a diamond.
		g.merge_glyph(g, -1,1)

		# The origin vector should be the same, and the width enlarged.
		self.failUnlessEqual(g.get_bounding_box(), (0,1, 3,3))

		# The bitmap should be a larger diagonal.
		self.failUnlessEqual(g.get_data(), ["40", "A0", "40"])

	def test_glyph_merging(self):
		f = model.Font("TestFont", 12, 100,100)
		g = f.new_glyph_from_data("TestGlyph", ["4", "8"], 0,0, 2,2, 3, 1)

		# Draw this glyph onto itself at 2,2
		g.merge_glyph(g, 2,2)

		# Check the results
		self.failUnlessEqual(g.get_bounding_box(), (0,0, 4,4))
		self.failUnlessEqual(g.get_data(), ["10", "20", "40", "80"])

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

	def test_glyph_get_ascent_and_descent(self):
		f = model.Font("TestFont", 12, 100,100)

		# For a simple glyph at the origin, ascent and descent should match the
		# bitmap bounding box.
		g = f.new_glyph_from_data("TestGlyph",
				["80", "40"],
				0,0, 2,2, 3, 1)
		self.failUnlessEqual(g.get_ascent(), 2)
		self.failUnlessEqual(g.get_descent(), 0)

		# If the bitmap crosses the baseline, we should get a positive ascent
		# and descent.
		g = f.new_glyph_from_data("TestGlyph",
				["80", "40"],
				0,-1, 2,2, 3, 2)
		self.failUnlessEqual(g.get_ascent(), 1)
		self.failUnlessEqual(g.get_descent(), 1)

		# If the bitmap is well above the baseline, ascent should be positive
		# and descent negative.
		g = f.new_glyph_from_data("TestGlyph",
				["80", "40"],
				0,1, 2,2, 3, 3)
		self.failUnlessEqual(g.get_ascent(), 3)
		self.failUnlessEqual(g.get_descent(), -1)

		# If the bitmap is well below the baseline, ascent should be negative
		# and descent positive.
		g = f.new_glyph_from_data("TestGlyph",
				["80", "40"],
				0,-3, 2,2, 3, 4)
		self.failUnlessEqual(g.get_ascent(), -1)
		self.failUnlessEqual(g.get_descent(), 3)

		# Ascent and descent should be calculated from the actual extents of
		# the character, not the bitmap.

		g = f.new_glyph_from_data("TestGlyph",
				["00", "80", "40", "00"],
				0,-2, 2,4, 3, 5)
		self.failUnlessEqual(g.get_ascent(), 1)
		self.failUnlessEqual(g.get_descent(), 1)
