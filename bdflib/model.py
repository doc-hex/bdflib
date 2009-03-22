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
Classes to represent a bitmap font in BDF format.
"""
# There are more reliable sources than BDF properties for these settings, so
# we'll ignore attempts to set them.
IGNORABLE_PROPERTIES = [
		"FACE_NAME",
		"POINT_SIZE",
		"PIXEL_SIZE",
		"RESOLUTION_X",
		"RESOLUTION_Y",
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

		# How many bytes do we need to represent the bits in each row?
		rowWidth, extraBits = divmod(self.bbW, 8)

		# How many bits of padding do we need to round up to a full byte?
		if extraBits > 0:
			rowWidth += 1
			paddingBits = 8 - extraBits
		else:
			paddingBits = 0

		for row in self.data:
			# rowWidth is the number of bytes, but Python wants the number of
			# nybbles, so multiply by 2.
			res.append("%0*X" % (rowWidth*2, row << paddingBits))

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
		self.data = new_data

	def get_ascent(self):
		res = self.bbY + self.bbH

		# Each empty row at the top of the bitmap should not be counted as part
		# of the ascent.
		for row in self.data[::-1]:
			if row != 0:
				break
			else:
				res -= 1

		return res

	def get_descent(self):
		res =  -1 * self.bbY

		# Each empty row at the bottom of the bitmap should not be counted as
		# part of the descent.
		for row in self.data:
			if row != 0:
				break
			else:
				res -= 1

		return res


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
		if name not in IGNORABLE_PROPERTIES:
			self.properties[name] = value

	def __getitem__(self, key):
		if isinstance(key, str):
			return self.properties[key]
		elif isinstance(key, int):
			return self.glyphs_by_codepoint[key]

	def __delitem__(self, key):
		if key in IGNORABLE_PROPERTIES: return
		elif isinstance(key, str):
			del self.properties[key]
		elif isinstance(key, int):
			g = self.glyphs_by_codepoint[key]
			self.glyphs.remove(g)
			del self.glyphs_by_codepoint[key]

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

	def copy(self):
		"""
		Returns a deep copy of this font.
		"""

		# Create a new font object.
		res = Font(self["FACE_NAME"], self["POINT_SIZE"], self["RESOLUTION_X"],
				self["RESOLUTION_Y"])

		# Copy the comments across.
		for c in self.comments:
			res.add_comment(c)

		# Copy the properties across.
		for p in self.properties:
			res[p] = self[p]

		# Copy the glyphs across.
		for g in self.glyphs:
			res.new_glyph_from_data(g.name, g.get_data(), g.bbX, g.bbY, g.bbW,
					g.bbH, g.advance, g.codepoint)

		return res

	def property_names(self):
		return self.properties.keys()

	def codepoints(self):
		return self.glyphs_by_codepoint.keys()
