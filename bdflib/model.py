"""
Classes to represent a bitmap font in BDF format.
"""
import math

REQUIRED_PROPERTIES = [
		"FONT_ASCENT",
		"FONT_DESCENT",
		"DEFAULT_CHAR",
	]


class GlyphExists(Exception):
	pass


class Glyph(object):
	"""
	Represents a font glyph and associated properties.
	"""

	def __init__(self, name, data=None, bbX=0, bbY=0, bbW=0, bbH=0, 
			advance=0, codepoint=None):
		"""
		Initialise this glyph object.
		"""
		self.name = name
		self.bbX = bbX
		self.bbY = bbY
		self.bbW = bbW
		self.bbH = bbH
		if data is None:
			self.data = []
		else:
			self._set_data(data)
		self.advance = advance
		if codepoint is None:
			self.codepoint = -1
		else:
			self.codepoint = codepoint

	def _set_data(self, data):
		self.data = []
		for row in data:
			paddingbits = len(row) * 4 - self.bbW
			self.data.append(int(row, 16) >> paddingbits)

	def get_data(self):
		res = []

		# How many bits of padding do we need?
		rowWidth, paddingBits = divmod(self.bbW, 4)
		for row in self.data:
			res.append("%*x" % (rowWidth, row << paddingBits))

		return res

	def get_bounding_box(self):
		return (self.bbX, self.bbY, self.bbW, self.bbH)

	def merge_glyph(self, other, atX, atY):

		# Calculate the new bounding box
		new_bbX = min(self.bbX, atX)
		new_bbY = min(self.bbY, atY)
		new_bbW = max(self.bbX + self.bbW, atX + other.bbW) - new_bbX
		new_bbH = max(self.bbY + self.bbH, atY + other.bbH) - new_bbY
		new_advance = max(self.advance, atX + other.advance)

		# Update our properties with calculated values
		self.bbX = new_bbX
		self.bbY = new_bbY
		self.bbW = new_bbW
		self.bbH = new_bbH
		self.advance = new_advance

class Font(object):
	"""
	Represents the entire font and font-global properties.
	"""

	def __init__(self, name, ptSize, xdpi, ydpi):
		"""
		Initialise this font object.
		"""
		self.properties = {
				"FACE_NAME": str(name),
				"POINT_SIZE": ptSize,
				"PIXEL_SIZE": math.ceil(ydpi * ptSize / 72.0),
				"RESOLUTION_X": xdpi,
				"RESOLUTION_Y": ydpi,
			}
		self.glyphs = []
		self.glyphs_by_codepoint = {}
		self.comments = []

	def add_comment(self, comment):
		lines = str(comment).split("\n")
		self.comments.extend(lines)

	def get_comments(self):
		return self.comments

	def __setitem__(self, name, value):
		assert isinstance(name, str)
		self.properties[name] = value

	def __getitem__(self, key):
		if isinstance(key, str):
			return self.properties[key]
		elif isinstance(key, int):
			return self.glyphs_by_codepoint[key]

	def new_glyph_from_data(self, name, data=None, bbX=0, bbY=0, bbW=0, bbH=0,
			advance=0, codepoint=None):
		g = Glyph(name, data, bbX, bbY, bbW, bbH, advance, codepoint)
		self.glyphs.append(g)
		if codepoint >= 0:
			if codepoint in self.glyphs_by_codepoint:
				raise GlyphExists("A glyph already exists for codepoint %r" 
						% codepoint)
			else:
				self.glyphs_by_codepoint[codepoint] = g
		return g
