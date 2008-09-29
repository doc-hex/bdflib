import unittest
from bdflib import glyph_combining, model

class TestBuildUnicodeDecompositions(unittest.TestCase):

	def test_basic_functionality(self):
		"""
		build_unicode_decompositions should run without crashing.
		"""
		res = glyph_combining.build_unicode_decompositions()

		# It should return a dict.
		self.failUnlessEqual(type(res), dict)

		# It should return a non-empty dict.
		self.failIfEqual(res, {})

		# It should have a decompositions for simple accented letters.
		self.failUnless(u"\N{LATIN CAPITAL LETTER A WITH GRAVE}" in res)

		# It should not have decompositions for complicated things like
		# superscripts.
		self.failIf(u"\N{SUPERSCRIPT TWO}" in res)

		# Decompositions should be iterables of (unicode char, int) tuples.
		for decomposable in res:
			for char, combining_class in res[decomposable]:
				self.failUnlessEqual(type(char), unicode)
				self.failUnlessEqual(len(char), 1)
				self.failUnlessEqual(type(combining_class), int)

	def test_base_dotless_i_and_j(self):
		"""
		Accented "i" should be based on a dotless i.
		"""
		res = glyph_combining.build_unicode_decompositions()

		# If there's an accent above the 'i', the base glyph should be
		# a dotless 'i'.
		components = res[u"\N{LATIN SMALL LETTER I WITH DIAERESIS}"]
		self.failUnlessEqual(components[0],
				(u"\N{LATIN SMALL LETTER DOTLESS I}",0))

		# If the accent is elsewhere, the base glyph should be a dotted 'i'.
		components = res[u"\N{LATIN SMALL LETTER I WITH OGONEK}"]
		self.failUnlessEqual(components[0], (u"i",0))

		# Likewise, a 'j' with an accent above should be based on dotless 'j'
		components = res[u"\N{LATIN SMALL LETTER J WITH CIRCUMFLEX}"]
		self.failUnlessEqual(components[0],
				(u"\N{LATIN SMALL LETTER DOTLESS J}",0))

		# ...and a 'j' with any other accent should be dotted, but the only
		# Unicode characters that decompose to a 'j' and an accent have the
		# accent above, so there's no test we can test here.


class TestFontFiller(unittest.TestCase):

	def setUp(self):

		# Create a simple font with two characters
		self.font = model.Font("TestFont", 12, 100, 100)
		self.font.new_glyph_from_data("a", ["4", "8"], 0,0, 2,2, 3, ord(u'a'))
		self.font.new_glyph_from_data("b", ["8", "4"], 0,0, 2,2, 3, ord(u'b'))

		# Create a dictionary that says how to combine them.
		self.decompositions = {
				# A simple combination of basic characters.
				u'c': [(u'a',0), (u'b',0)],
				# A recursive definition
				u'd': [(u'c',0), (u'a',0), (u'b',0)],
				# A definition that can't be solved with the glyphs in this
				# font.
				u'e': [(u'f',0), (u'g',0)],
				# A definition that involves an unknown combining class
				u'h': [(u'a',0), (u'b',256)],
			}

		self.filler = glyph_combining.FontFiller(self.font,
				self.decompositions)

	def test_basic_functionality(self):
		"""
		We succeed if we have a decomposition and the components.
		"""
		added = self.filler.add_glyph_to_font(u'c')
		self.failUnlessEqual(added, True)

		glyph = self.font[ord(u'c')]

		print glyph
		self.failUnlessEqual(str(glyph),
				"|#.#.\n"
				"#---#"
			)

	def test_recursive_functionality(self):
		"""
		We succeed even if we can only get the components recursively.
		"""
		added = self.filler.add_glyph_to_font(u'd')
		self.failUnlessEqual(added, True)

		glyph = self.font[ord(u'd')]

		print glyph
		self.failUnlessEqual(str(glyph),
				"|#.#...#.#.\n"
				"#---#-#---#"
			)

	def test_character_present(self):
		"""
		We succeed if the char is already in the font.
		"""
		added = self.filler.add_glyph_to_font(u'a')
		self.failUnlessEqual(added, True)

	def test_missing_decomposition(self):
		"""
		We fail if there's no decomposition for the given character.
		"""
		added = self.filler.add_glyph_to_font(u'z')
		self.failUnlessEqual(added, False)

	def test_missing_recursive_decomposition(self):
		"""
		We fail if there's a decomposition but no components for a character.
		"""
		added = self.filler.add_glyph_to_font(u'e')
		self.failUnlessEqual(added, False)

	def test_unknown_combining_class(self):
		"""
		We fail if there's a decomposition but we don't know how to use it.
		"""
		added = self.filler.add_glyph_to_font(u'h')
		self.failUnlessEqual(added, False)

	def test_add_decomposable_glyphs_to_font(self):
		"""
		Add all the glyphs we can to the given font.
		"""

		self.filler.add_decomposable_glyphs_to_font()

		self.failUnless(ord('c') in self.font)
		self.failUnless(ord('d') in self.font)


class TestFontFillerCombiningAbove(unittest.TestCase):

	def _build_composing_above_font(self, set_cap_height=False):
		"""
		Return a font with glyphs useful for testing COMBINING ABOVE.
		"""
		font = model.Font("TestFont", 12, 100, 100)

		# Some glyphs for testing accent placement
		font.new_glyph_from_data("space", [], 0,0, 0,0, 4,
				ord(u' '))
		font.new_glyph_from_data("O", "4 A A 4".split(), 0,0, 3,4, 4,
				ord(u'O'))
		font.new_glyph_from_data("o", "4 A 4".split(), 0,0, 3,3, 4,
				ord(u'o'))
		font.new_glyph_from_data("macron", ["F"], 0,5, 4,1, 4,
				ord(u'\N{COMBINING MACRON}'))
		font.new_glyph_from_data("caron", ["4", "A"], 0,5, 3,2, 4,
				ord(u'\N{COMBINING CARON}'))

		if set_cap_height:
			font["CAP_HEIGHT"] = 4

		decompositions = {
				# Test combining an odd-width base-character with an even-width
				# accent.
				u'I': [(u'O',0),
					(u'\N{COMBINING MACRON}',glyph_combining.CC_A)],
				u'i': [(u'o',0),
					(u'\N{COMBINING MACRON}',glyph_combining.CC_A)],
				# Test combining an odd-width base-character with an odd-width
				# accent.
				u'J': [(u'O',0),
					(u'\N{COMBINING CARON}',glyph_combining.CC_A)],
				u'j': [(u'o',0),
					(u'\N{COMBINING CARON}',glyph_combining.CC_A)],
				u'\N{MACRON}': [(u' ', 0),
					(u'\N{COMBINING MACRON}',glyph_combining.CC_A)],
			}

		glyph_combining.FontFiller(
				font,
				decompositions,
			).add_decomposable_glyphs_to_font()

		return font

	def test_composing_even_above_odd(self):
		font = self._build_composing_above_font()

		O_macron = font[ord(u'I')]
		print O_macron
		self.failUnlessEqual(str(O_macron),
				"####\n"
				"|...\n"
				"|#..\n"
				"#.#.\n"
				"#.#.\n"
				"+#--"
			)

	def test_composing_odd_above_odd(self):
		font = self._build_composing_above_font()

		O_caron = font[ord(u'J')]
		print O_caron
		self.failUnlessEqual(str(O_caron),
				"|#.\n"
				"#.#\n"
				"|..\n"
				"|#.\n"
				"#.#\n"
				"#.#\n"
				"+#-"
			)

	def test_composing_above_without_CAP_HEIGHT(self):

		# Build the font without CAP_HEIGHT set.
		font = self._build_composing_above_font(False)

		# Upper case and lower-case should have the accent at the same place.
		O_caron = font[ord(u'J')]
		print O_caron
		self.failUnlessEqual(str(O_caron),
				"|#.\n"
				"#.#\n"
				"|..\n"
				"|#.\n"
				"#.#\n"
				"#.#\n"
				"+#-"
			)

		o_caron = font[ord(u'j')]
		print o_caron
		self.failUnlessEqual(str(o_caron),
				"|#.\n"
				"#.#\n"
				"|..\n"
				"|..\n"
				"|#.\n"
				"#.#\n"
				"+#-"
			)

	def test_composing_above_with_CAP_HEIGHT(self):
		# Build the font with CAP_HEIGHT set.
		font = self._build_composing_above_font(True)

		# Upper case should be the same.
		O_caron = font[ord(u'J')]
		print O_caron
		self.failUnlessEqual(str(O_caron),
				"|#.\n"
				"#.#\n"
				"|..\n"
				"|#.\n"
				"#.#\n"
				"#.#\n"
				"+#-"
			)

		# The accent should be as high above lowercase as it is above
		# upper-case.

		o_caron = font[ord(u'j')]
		print o_caron
		self.failUnlessEqual(str(o_caron),
				"|#.\n"
				"#.#\n"
				"|..\n"
				"|#.\n"
				"#.#\n"
				"+#-"
			)

	def test_composing_above_blank_base(self):
		"""
		Composing on top of a blank base char should work.
		"""
		# Build the font with CAP_HEIGHT set.
		font = self._build_composing_above_font(True)

		# Macron should be drawn in the usual place.
		macron = font[ord(u'\N{MACRON}')]
		print macron
		self.failUnlessEqual(str(macron),
				"####\n"
				"|...\n"
				"|...\n"
				"|...\n"
				"|...\n"
				"+---"
			)

		# Without CAP_HEIGHT set, the same should happen.
		font = self._build_composing_above_font(False)

		# Macron should be drawn in the usual place.
		macron = font[ord(u'\N{MACRON}')]
		print macron
		self.failUnlessEqual(str(macron),
				"####\n"
				"|...\n"
				"|...\n"
				"|...\n"
				"|...\n"
				"+---"
			)


class TestFontFillerCombiningBelow(unittest.TestCase):

	def _build_composing_below_font(self):
		"""
		Return a font with glyphs useful for testing COMBINING BELOW.
		"""
		font = model.Font("TestFont", 12, 100, 100)

		# Some glyphs for testing accent placement
		font.new_glyph_from_data("space", [], 0,0, 0,0, 4,
				ord(u' '))
		font.new_glyph_from_data("Y", "A A 4 4".split(), 0,0, 3,4, 4,
				ord(u'Y'))
		font.new_glyph_from_data("y", "A A 6 2 D".split(), 0,-2, 3,5, 4,
				ord(u'y'))
		font.new_glyph_from_data("macron_below", ["F"], 0,-2, 4,1, 4,
				ord(u'\N{COMBINING MACRON BELOW}'))
		font.new_glyph_from_data("dot_below", ["8"], 0,-2, 1,1, 1,
				ord(u'\N{COMBINING DOT BELOW}'))

		decompositions = {
				# Test combining an odd-width base-character with an even-width
				# accent.
				u'I': [(u'Y',0),
					(u'\N{COMBINING MACRON BELOW}',glyph_combining.CC_B)],
				u'i': [(u'y',0),
					(u'\N{COMBINING MACRON BELOW}',glyph_combining.CC_B)],
				# Test combining an odd-width base-character with an odd-width
				# accent.
				u'J': [(u'Y',0),
					(u'\N{COMBINING DOT BELOW}',glyph_combining.CC_A)],
				u'j': [(u'y',0),
					(u'\N{COMBINING DOT BELOW}',glyph_combining.CC_B)],
				u'_': [(u' ', 0),
					(u'\N{COMBINING MACRON BELOW}',glyph_combining.CC_B)],
			}

		glyph_combining.FontFiller(
				font,
				decompositions,
			).add_decomposable_glyphs_to_font()

		return font

	def test_composing_even_below_odd(self):
		font = self._build_composing_below_font()

		Y_macron = font[ord(u'I')]
		print Y_macron
		self.failUnlessEqual(str(Y_macron),
				"#.#.\n"
				"#.#.\n"
				"|#..\n"
				"+#--\n"
				"|...\n"
				"####"
			)

	def test_composing_odd_below_odd(self):
		font = self._build_composing_below_font()

		Y_dot = font[ord(u'J')]
		print Y_dot
		self.failUnlessEqual(str(Y_dot),
				"#.#\n"
				"#.#\n"
				"|#.\n"
				"+#-\n"
				"|..\n"
				"|#."
			)

	def test_composing_below_clears_descenders(self):

		font = self._build_composing_below_font()

		# Upper case and lower-case should have the accent at the same place.
		Y_dot = font[ord(u'J')]
		print Y_dot
		self.failUnlessEqual(str(Y_dot),
				"#.#\n"
				"#.#\n"
				"|#.\n"
				"+#-\n"
				"|..\n"
				"|#."
			)

		y_dot = font[ord(u'j')]
		print y_dot
		self.failUnlessEqual(str(y_dot),
				"#.#\n"
				"#.#\n"
				"+##\n"
				"|.#\n"
				"##.\n"
				"|..\n"
				"|#."
			)

	def test_composing_below_blank_base(self):
		"""
		Composing on top of a blank base char should work.
		"""
		font = self._build_composing_below_font()

		# Underscore should be drawn in the usual place.
		underscore = font[ord(u'_')]
		print underscore
		self.failUnlessEqual(str(underscore),
				"+---\n"
				"|...\n"
				"####"
			)
