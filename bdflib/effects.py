"""
Various cosmetic effects for fonts.
"""

def embolden(font, maintain_spacing=True):
	res = font.copy()

	for cp in res.codepoints():
		g = res[cp]
		g.merge_glyph(g, 1,0)
		if maintain_spacing:
			g.advance += 1

	return res


def merge(base, custom):
	res = custom.copy()

	for cp in base.codepoints():
		if cp not in res:
			old_glyph = base[cp]
			res.new_glyph_from_data(old_glyph.name, old_glyph.get_data(),
					old_glyph.bbX, old_glyph.bbY, old_glyph.bbW, old_glyph.bbH,
					old_glyph.advance, old_glyph.codepoint)

	return res
