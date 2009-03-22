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
