# bdflib, a library for working with BDF font files
# Copyright (C) 2009, Timothy Alle
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Tools for building glyphs by combining other glyphs.
"""
import sys
import unicodedata
from bdflib.util import Tally

# There are many ways in which one character might be said to be 'made up of'
# other characters. We're only interested in the ones that involve graphically
# drawing one character overlaid on or beside another.
USEFUL_COMPOSITION_TYPES = [
		'<compat>',
		'<noBreak>',
	]

# Combining class names. Summarised from
# http://unicode.org/Public/UNIDATA/UCD.html#Canonical_Combining_Class_Values
CC_SPACING			= 0		# Spacing, split, enclosing, reordrant, etc.
CC_OVERLAY			= 1		# Overlays and interior
CC_NUKTAS			= 7		# Nuktas
CC_VOICING_MARKS	= 8		# Hiragana/Katakana voicing marks
CC_VIRAMAS			= 9		# Viramas
CC_BL_ATTACHED		= 200	# Bottom-left attached
CC_B_ATTACHED		= 202	# Bottom attached
CC_BR_ATTACHED		= 204	# Bottom-right attached
CC_L_ATTACHED		= 208	# Left attached
CC_R_ATTACHED		= 210	# Right attached
CC_AL_ATTACHED		= 212	# Above-left attached
CC_A_ATTACHED		= 214	# Above attached
CC_AR_ATTACHED		= 216	# Above-right attached
CC_BL				= 218	# Below-left
CC_B				= 220	# Below
CC_BR				= 222	# Below-right
CC_L				= 224	# Left
CC_R				= 226	# Right
CC_AL				= 228	# Above-left
CC_A				= 230	# Above
CC_AR				= 232	# Above-right
CC_B_DOUBLE			= 233	# Double below
CC_A_DOUBLE			= 234	# Double above
CC_IOTA_SUBSCRIPT	= 240	# Below (iota subscript)

# Combining glyphs can be drawn in different places on the base glyph; the
# combining class determines exactly where.
SUPPORTED_COMBINING_CLASSES = [
		CC_SPACING,
		CC_A,
		CC_B,
		CC_B_ATTACHED,
	]

# Combining classes that mean "draw the combining character above the base
# character". These cause characters with the "Soft_Dotted" property to be
# treated specially.
ABOVE_COMBINING_CLASSES = [CC_A, CC_A_ATTACHED]

# Characters with the "Soft_Dotted" property are treated specially a combining
# character is drawn above them; the dot is not drawn. Since Python's
# unicodedata module won't tell us what properties a character has, we'll have
# to hard-code the list ourselves.
SOFT_DOTTED_CHARACTERS = {
		u"i": u"\N{LATIN SMALL LETTER DOTLESS I}",
		u"j": u"\N{LATIN SMALL LETTER DOTLESS J}",
	}


def build_unicode_decompositions():
	"""
	Returns a dictionary mapping unicode chars to their component glyphs.
	"""
	res = {}

	for codepoint in range(0, sys.maxunicode + 1):
		curr_char = unichr(codepoint)
		hex_components = unicodedata.decomposition(curr_char).split()

		if hex_components == []:
			# No decomposition at all, who cares?
			continue

		# If this combining-char sequence has a special type...
		if hex_components[0].startswith('<'):
			composition_type = hex_components[0]
			# ...is it a type we like?
			if composition_type in USEFUL_COMPOSITION_TYPES:
				# Strip the type, use the rest of the sequence
				hex_components = hex_components[1:]
			else:
				# This sequence is no good to us, let's move on.
				continue

		# Convert ['aaaa', 'bbbb'] to [u'\uaaaa', u'\ubbbb'].
		components = [unichr(int(cp,16)) for cp in hex_components]

		# Handle soft-dotted characters.
		if components[0] in SOFT_DOTTED_CHARACTERS and len(components) > 1:
			above_components = [c for c in components[1:]
					if unicodedata.combining(c) in ABOVE_COMBINING_CLASSES]
			# If there are any above components...
			if len(above_components) > 0:
				# ...replace the base character with its undotted equivalent.
				components[0] = SOFT_DOTTED_CHARACTERS[components[0]]

		# Look up the combining classes, too
		res[curr_char] = [(char, unicodedata.combining(char))
				for char in components]

	return res


class FontFiller(object):
	"""
	Utility class for filling out a font based on combining characters.
	"""

	def __init__(self, font, decompositions):
		self.font = font
		self.decompositions = decompositions
		self.missing_chars = Tally("Missing combinable characters", "char")
		self.unknown_classes = Tally("Unknown combining classes")

	def add_glyph_to_font(self, char):
		"""
		Add the glyph representing char to the given font, if it can be built.
		"""

		if ord(char) in self.font:
			# It's already there!
			return True

		if char not in self.decompositions:
			# We don't know how to build it.
			return False

		components = self.decompositions[char]
		for component_char, combining_class in components:
			if combining_class not in SUPPORTED_COMBINING_CLASSES:
				# We don't know how to combine this with other characters.
				self.unknown_classes.record(combining_class)
				return False

			if not self.add_glyph_to_font(component_char):
				# We don't know how to build one of the required components.
				self.missing_chars.record(component_char)
				return False

		# Now we have all the components, let's put them together!
		glyph = self.font.new_glyph_from_data("char%d" % ord(char),
				codepoint=ord(char))

		# Draw on the base char.
		base_char = components[0][0]
		base_combining_class = components[0][1]
		assert (base_combining_class == CC_SPACING,
				"base char should be a spacing char")
		base_glyph = self.font[ord(base_char)]
		glyph.merge_glyph(base_glyph, 0,0)
		glyph.advance = base_glyph.advance

		for component_char, combining_class in components[1:]:
			other_glyph = self.font[ord(component_char)]

			if combining_class == CC_SPACING:
				# Draw other_glyph beside the current glyph
				glyph.merge_glyph(other_glyph, glyph.advance,0)
				glyph.advance += other_glyph.advance

			elif combining_class == CC_A:
				# Draw other_glyph centred above the current glyph
				y_offset = 0
				x_offset = 0

				if "CAP_HEIGHT" in self.font and glyph.bbH > 0:
					# We assume combining glyphs are drawn above the
					# CAP_HEIGHT.
					y_offset = glyph.get_ascent() - self.font["CAP_HEIGHT"]

				if glyph.bbW > 0:
					x_offset = int(
							float(glyph.advance)/2
							- float(other_glyph.advance)/2
						)

				glyph.merge_glyph(other_glyph, x_offset,y_offset)
			elif combining_class in (CC_B, CC_B_ATTACHED):
				# Draw other_glyph centred below the current glyph
				y_offset = -glyph.get_descent()
				x_offset = 0

				if glyph.bbW > 0:
					x_offset = int(
							float(glyph.advance)/2
							- float(other_glyph.advance)/2
						)

				glyph.merge_glyph(other_glyph, x_offset,y_offset)
			else:
				raise RuntimeError("Unsupported combining class %d" %
						(combining_class,))

		return True

	def add_decomposable_glyphs_to_font(self):
		"""
		Adds all the glyphs that can be built to the given font.
		"""
		for char in self.decompositions:
			self.add_glyph_to_font(char)
