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
Useful classes and functions that don't fit anywhere else.
"""

class Tally(object):
	"""
	Keeps count of things and prints a pretty list.
	"""

	def __init__(self, caption="", itemname="item"):
		self.counter = {}
		self.caption = caption
		self.itemname = itemname

	def record(self, item):
		"""
		Record that we've seen one more instance of the given item.

		item should be a hashable.
		"""
		if item in self.counter:
			self.counter[item] += 1
		else:
			self.counter[item] = 1

	def show(self, formatter=None):
		"""
		Print the result of the tally.

		formatter should be a callable that takes an item and returns a pretty
		string. If not supplied, repr() is used.
		"""
		if formatter is None:
			formatter = repr

		data = [(value, key) for key,value in self.counter.items()]
		data.sort()

		if len(data) == 0:
			return
		
		if self.caption:
			print self.caption
		print "count %s" % self.itemname
		for count, item in data:
			print "%5d %s" % (count, formatter(item))
