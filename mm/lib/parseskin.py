__version__ = "$Id$"

error = 'parseskin.error'

# The syntax for a GRiNS skin description file is very simple:
#
# Comments start with the character # and extend to the end of the
# line; empty lines are ignored.
#
# Lines consist of a keyword and parameters, separated from each other
# by white space.  The available keywords and their parameters are:
#
# "image"	URL of image file (relative to skin definition file)
# "display"	4 numbers giving x, y, width, height
# "components"	URL of file containing recognized systemComponents URIs
#		(relative to skin definition file)
# "key"		key shape coordinates
# command	shape coordinates
#
# The key is a single, possibly quoted, character.  If either ", ', or
# a space character needs to be specified, it must be surrounded with
# quotes, eitherwise quotes are optional.  Use ' to quote " and v.v.
#
# The possible commands are:
# "open", "play", "pause", "stop", "exit".
#
# The possible shapes and coordinates are:
# "rect" with 4 numbers giving x, y, width, and height;
# "circle" with 3 numbers giving x, y, and radius;
# "poly" with an even number of numbers, each pair describing the x
# and y coordinates of a point.
#
# Example skin definition file:

import string				# for whitespace
def parsegskin(file):
	dict = {}
	lineno = 0
	while 1:
		line = file.readline()
		if not line:
			break
		lineno = lineno + 1

		# ignore comments and empty lines
		# and strip off white space
		i = line.find('#')
		if i >= 0:
			line = line[:i]
		line = line.strip()
		if not line:
			continue

		# first part is GRiNS command
		line = line.split(None, 1)
		if len(line) == 1:
			raise error, 'syntax error in skin on line %d' % lineno
		cmd, rest = line
		if cmd in ('image', 'components'):
			dict[cmd] = rest.strip()
			continue
		if cmd == 'key':
			quote = None
			backslash = 0
			key = None
			rest = list(rest) # easier to manipiulate list
			while rest:
				c = rest[0]
				del rest[0]
				if quote is not None:
					if c == quote:
						quote = None
					elif backslash:
						if key is None:
							if c == '\\':
								key = '\\'
							elif c == 'r':
								key = '\r'
							elif c == 't':
								key = '\t'
							elif c == 'n':
								key = '\n'
							elif c == 'b':
								key = '\b'
							else:
								key = c
						else:
							raise error, 'syntax error in skin on line %d: only single character allowed for key' % lineno
						backslash = 0
					elif c == '\\':
						backslash = 1
					elif key is None:
						key = c
					else:
						raise error, 'syntax error in skin on line %d: only single character allowed for key' % lineno
				elif c == '"' or c == "'":
					quote = c
				elif c in string.whitespace:
					if key is not None:
						break
				elif backslash:
					if key is None:
						if c == '\\':
							key = '\\'
						elif c == 'r':
							key = '\r'
						elif c == 't':
							key = '\t'
						elif c == 'n':
							key = '\n'
						elif c == 'b':
							key = '\b'
						else:
							key = c
					else:
						raise error, 'syntax error in skin on line %d: only single character allowed for key' % lineno
					backslash = 0
				elif c == '\\':
					backslash = 1
				elif key is None:
					key = c
				else:
					raise error, 'syntax error in skin on line %d: only single character allowed for key' % lineno
			if key is None:
				raise error, 'syntax error in skin on line %d: no key specified' % lineno
			rest = ''.join(rest) # reassemble string
		coords = rest.split()
		if cmd == 'display':
			# display area is always rectangular
			shape = 'rect'
		else:
			shape = coords[0]
			del coords[0]
		try:
			coords = map(lambda v: int(v, 0), coords)
		except ValueError:
			raise error, 'syntax error in skin on line %d' % lineno
		if shape == 'poly' and coords[:2] == coords[-2:]:
			del coords[-2:]
		if (shape != 'rect' or len(coords) != 4) and \
		   (shape != 'circle' or len(coords) != 3) and \
		   (shape != 'poly' or len(coords) < 6 or len(coords) % 2 != 0):
			raise error, 'syntax error in skin on line %d' % lineno
		if cmd == 'key':
			dict[cmd] = shape, coords, key
		else:
			dict[cmd] = shape, coords
	if not dict.has_key('image'):
		raise error, 'image missing from skin description file'
	if not dict.has_key('display'):
		raise error, 'display region missing from skin description file'
	return dict
