import unittest
from bdflib import glyph_combining

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

		# Decompositions should be iterables of unicode characters.
		for char in res:
			for composition in res[char]:
				for component in composition:
					self.failUnlessEqual(type(component), unicode)
					self.failUnlessEqual(len(component), 1)

	def test_base_dotless_i_and_j(self):
		"""
		Accented "i" should be based on a dotless i.
		"""
		res = glyph_combining.build_unicode_decompositions()

		# If there's an accent above the 'i', the base glyph should be
		# a dotless 'i'.
		components = res[u"\N{LATIN SMALL LETTER I WITH DIAERESIS}"]
		self.failUnlessEqual(components[0],
				u"\N{LATIN SMALL LETTER DOTLESS I}")

		# If the accent is elsewhere, the base glyph should be a dotted 'i'.
		components = res[u"\N{LATIN SMALL LETTER I WITH OGONEK}"]
		self.failUnlessEqual(components[0], u"i")

		# Likewise, a 'j' with an accent above should be based on dotless 'j'
		components = res[u"\N{LATIN SMALL LETTER J WITH CIRCUMFLEX}"]
		self.failUnlessEqual(components[0],
				u"\N{LATIN SMALL LETTER DOTLESS J}")

		# ...and a 'j' with any other accent should be dotted, but the only
		# Unicode characters that decompose to a 'j' and an accent have the
		# accent above, so there's no test we can test here.
