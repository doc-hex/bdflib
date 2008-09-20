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
