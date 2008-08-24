"""
Tools to write a Font object to a BDF File.
"""

def quote_property_value(val):

	if isinstance(val, int):
		return str(val)
	else:
		return '"%s"' % (str(val).replace('"', '""'),)

def write_bdf(font, stream):
	stream.write("STARTFONT 2.1\n")
	stream.write("FONT %s\n" % (font.name,))
	stream.write("SIZE %d %d %d\n" % (font.ptSize, font.xdpi, font.ydpi))
	stream.write("FONTBOUNDINGBOX %d %d %d %d\n" 
			% (font.bbW, font.bbH, font.bbX, font.bbY))

	if len(font.properties):
		stream.write("STARTPROPERTIES %d\n" % (len(font.properties),))
		for key, value in font.properties.items():
			stream.write("%s %s\n" % (key, quote_property_value(value)))
		stream.write("ENDPROPERTIES\n")

	if len(font.glyphs):
		stream.write("CHARS %d\n" % (len(font.glyphs),))
		for glyph in font.glyphs:
			stream.write("STARTCHAR %s\n" % (glyph.name,))
			stream.write("ENCODING %d\n" % (glyph.codepoint,))
			stream.write("SWIDTH %d %d\n"
					% (glyph.swidthX, glyph.swidthY))
			stream.write("DWIDTH %d %d\n"
					% (glyph.dwidthX, glyph.dwidthY))
			stream.write("BBX %d %d %d %d\n"
					% (glyph.bbW, glyph.bbH, glyph.bbX, glyph.bbY))
			stream.write("BITMAP\n")
			for row in glyph.data:
				stream.write("%s\n" % (row.encode("hex"),))
			stream.write("ENDCHAR\n")

	stream.write("ENDFONT\n")
