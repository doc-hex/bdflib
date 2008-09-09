"""
Classes to represent a bitmap font in BDF format.
"""


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

	def __str__(self):
		def padding_char(x,y):
			if x == 0 and y == 0:
				return '+'
			elif x == 0:
				return '|'
			elif y == 0:
				return '-'
			else:
				return '.'

		# What are the extents of this bitmap, given that we always want to
		# include the origin?
		bitmap_min_X = min(0, self.bbX)
		bitmap_max_X = max(0, self.bbX + self.bbW-1)
		bitmap_min_Y = min(0, self.bbY)
		bitmap_max_Y = max(0, self.bbY + self.bbH-1)

		res = []
		for y in range(bitmap_max_Y, bitmap_min_Y - 1, -1):
			res_row = []
			# Find the data row associated with this output row.
			if self.bbY <= y < self.bbY + self.bbH:
				data_row = self.data[y - self.bbY]
			else:
				data_row = 0
			for x in range(bitmap_min_X, bitmap_max_X + 1):
				# Figure out which bit controls (x,y)
				bit_number = self.bbW - (x - self.bbX) - 1
				# If we're in a cell covered by the bitmap and this particular
				# bit is set...
				if self.bbX <= x < self.bbX + self.bbW and (
						data_row >> bit_number & 1):
					res_row.append('#')
				else:
					res_row.append(padding_char(x,y))
			res.append("".join(res_row))

		return "\n".join(res)

	def _set_data(self, data):
		self.data = []
		for row in data:
			paddingbits = len(row) * 4 - self.bbW
			self.data.append(int(row, 16) >> paddingbits)

		# Make the list indices match the coordinate system
		self.data.reverse()

	def get_data(self):
		res = []

		# How many hex digits do we need to represent each row?
		rowWidth, extraBits = divmod(self.bbW, 4)

		# How many bits of padding do we need to round up to a full hex digit?
		if extraBits == 0:
			paddingBits = 0
		else:
			paddingBits = 4 - extraBits

		for row in self.data:
			res.append("%*X" % (rowWidth, row << paddingBits))

		# self.data goes bottom-to-top like any proper coordinate system does,
		# but res wants to be top-to-bottom like any proper stream-output.
		res.reverse()

		return res

	def get_bounding_box(self):
		return (self.bbX, self.bbY, self.bbW, self.bbH)

	def merge_glyph(self, other, atX, atY):
		# Calculate the new metrics
		new_bbX = min(self.bbX, atX + other.bbX)
		new_bbY = min(self.bbY, atY + other.bbY)
		new_bbW = max(self.bbX + self.bbW,
				atX + other.bbX + other.bbW) - new_bbX
		new_bbH = max(self.bbY + self.bbH,
				atY + other.bbY + other.bbH) - new_bbY
		new_advance = max(self.advance, atX + other.advance)

		# Calculate the new data
		new_data = []
		for y in range(new_bbY, new_bbY + new_bbH):
			# If the old glyph has a row here...
			if self.bbY <= y < self.bbY + self.bbH:
				old_row = self.data[y-self.bbY]

				# If the right-hand edge of the bounding box has moved right,
				# we'll need to left shift the old-data to get more empty space
				# to draw the new glyph into.
				right_edge_delta = (new_bbX + new_bbW) - (self.bbX + self.bbW)
				if right_edge_delta > 0:
					old_row <<= right_edge_delta
			else:
				old_row = 0
			# If the new glyph has a row here...
			if atY + other.bbY <= y < atY + other.bbY + other.bbH:
				new_row = other.data[y - other.bbY - atY]

				# If the new right-hand-edge ofthe bounding box
				if atX + other.bbX + other.bbW < new_bbX + new_bbW:
					new_row <<= ((new_bbX + new_bbW)
							- (atX + other.bbX + other.bbW))
			else:
				new_row = 0
			new_data.append(old_row | new_row)

		# Update our properties with calculated values
		self.bbX = new_bbX
		self.bbY = new_bbY
		self.bbW = new_bbW
		self.bbH = new_bbH
		self.advance = new_advance
		self.data = new_data


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

	def __contains__(self, key):
		if isinstance(key, str):
			return key in self.properties
		elif isinstance(key, int):
			return key in self.glyphs_by_codepoint

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
