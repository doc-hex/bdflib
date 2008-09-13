"""
Tools for building glyphs by combining other glyphs.
"""
import sys
import unicodedata

# There are many ways in which one character might be said to be 'made up of'
# other characters. We're only interested in the ones that involve graphically
# drawing one character overlaid on or beside another.
USEFUL_COMPOSITION_TYPES = [
		'<compat>',
		'<noBreak>',
	]

# Combining glyphs can be drawn in different places on the base glyph; the
# combining class determines exactly where.
SUPPORTED_COMBINING_CLASSES = [
		0, # Ordinary spacing characters.
	]

# Combining classes that mean "draw the combining character above the base
# character". These cause characters with the "Soft_Dotted" property to be
# treated specially.
ABOVE_COMBINING_CLASSES = [
		214, # Above attached
		230, # Above
	]

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

		res[curr_char] = components

	return res
