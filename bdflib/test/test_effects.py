import unittest

from bdflib import model, effects

class TestEmbolden(unittest.TestCase):

	def _build_test_font(self):
		f = model.Font("TestFont", 12, 100,100)
		f.new_glyph_from_data("TestGlyph", ["4", "8"], 0,0, 2,2, 3, 1)

		return f

	def test_basic_operation(self):
		f = self._build_test_font()
		f2 = effects.embolden(f)

		self.failIfEqual(f, f2)

		g = f2[1]
		self.failUnlessEqual(g.bbX, 0)
		self.failUnlessEqual(g.bbY, 0)
		self.failUnlessEqual(g.bbW, 3)
		self.failUnlessEqual(g.bbH, 2)
		self.failUnlessEqual(g.get_data(), ["60", "C0"])


	def test_maintaining_spacing(self):
		f = effects.embolden(self._build_test_font(), True)

		g = f[1]

		self.failUnlessEqual(g.advance, 4)

	def test_without_maintaining_spacing(self):
		f = effects.embolden(self._build_test_font(), False)

		g = f[1]

		self.failUnlessEqual(g.advance, 3)


class TestMerge(unittest.TestCase):

	def test_basic_operation(self):
		base_font = model.Font("BaseFont", 12, 100,100)
		base_font.new_glyph_from_data("base1", ["4", "8"], 0,0, 2,2, 3, 1)
		base_font.new_glyph_from_data("base2", ["8", "4"], 0,0, 2,2, 3, 2)

		cust_font = model.Font("CustomFont", 12, 100,100)
		cust_font.new_glyph_from_data("cust2", ["8", "8"], 0,0, 2,2, 3, 2)
		cust_font.new_glyph_from_data("cust3", ["4", "4"], 0,0, 2,2, 3, 3)

		# Start by merging the custom font on top of the base font.
		merged1 = effects.merge(base_font, cust_font)

		# We should get an entirely new font.
		self.failIfEqual(merged1, base_font)
		self.failIfEqual(merged1, cust_font)

		# The new font should have cust* characters in preference to base
		# characters.
		self.failUnlessEqual(merged1[1].name, "base1")
		self.failUnlessEqual(merged1[2].name, "cust2")
		self.failUnlessEqual(merged1[3].name, "cust3")

		# If we merge things the other way around...
		merged2 = effects.merge(cust_font, base_font)

		# ...the new font should prefer base* characters.
		self.failUnlessEqual(merged2[1].name, "base1")
		self.failUnlessEqual(merged2[2].name, "base2")
		self.failUnlessEqual(merged2[3].name, "cust3")
