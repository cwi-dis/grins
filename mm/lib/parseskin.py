__version__ = "$Id$"

import MMurl, string, Sizes

error = 'parseskin.error'

def parseskin(file):
	dict = {}
	buttons = {}
	while 1:
		line = file.readline()
		if not line:
			break
		i = line.find('#')
		if i >= 0:
			line = line[:i]
		line = line.strip()
		if not line:
			continue
		keyval = line.split('=', 1)
		if len(keyval) != 2:
			continue
		key, val = keyval
		key = key.strip()
		val = val.strip()
		if key[:4] == 'File':
			val = MMurl.pathname2url(val)
		elif key[-5:] == 'Color':
			val = tuple(map(lambda v: int(v, 0), val.split(',')))
		elif key[:7] == 'Element':
			val = map(string.strip, val.split(','))
			button = val[0]
			val = map(lambda v: int(v, 0), val[1:])
			buttons[button] = tuple(val)
			continue
		dict[key] = val
	return dict, buttons

if __debug__:
	# Code to generate a SMIL file from a skin definition.
	# Not used in GRiNS.
	anchor = '''\
        <area id="%(id)s" coords="%(x0)d,%(y0)d,%(x1)d,%(y1)d"/>'''
	smil = '''\
<smil xmlns="http://www.w3.org/2001/SMIL20/Language">
  <head>
    <layout>
      <root-layout id="%(Name)s" backgroundColor="#%(r)02x%(g)02x%(b)02x" width="%(width)d" height="%(height)d"/>
      <region id="skin">
        <region id="LCD" left="%(x)d" top="%(y)d" width="%(w)d" height="%(h)d">
        </region>
      </region>
    </layout>
  </head>
  <body>
    <par>
      <img region="skin" dur="indefinite" src="%(file)s">
%(anchors)s
      </img>
    </par>
  </body>
</smil>'''
	defbg = (255,255,255)

	def skinsmil(url):
		file = MMurl.urlopen(url)
		url = file.geturl()
		dict, buttons = parseskin(file)
		skin = MMurl.basejoin(url, dict['File1x'])
		width, height = Sizes.GetSize(skin)
		anchors = []
		for key, val in buttons.items():
			if key == 'LCD':
				continue
			anchors.append(anchor % {'id': key, 'x0': val[0], 'y0': val[1], 'x1': val[0]+val[2], 'y1': val[1]+val[3]})
		anchors = '\n'.join(anchors)
		return smil % {'Name': dict.get('Name', 'Skin'), 'r': dict.get('BackgroundColor', defbg)[0], 'g': dict.get('BackgroundColor', defbg)[1], 'b': dict.get('BackgroundColor', defbg)[2], 'width': width, 'height': height, 'x': buttons['LCD'][0], 'y': buttons['LCD'][1], 'w': buttons['LCD'][2], 'h': buttons['LCD'][3], 'file': skin, 'anchors': anchors}

# The syntax for a GRiNS skin description file is very simple:
# Comments start with the character # and extend to the end of the
# line; empty lines are ignored.
# Lines consist of a keyword and parameters, separated from each other
# by white space.  The available keywords and their parameters are:
# "image"	URL of image file (relative to skin definition file)
# "display"	4 numbers giving x, y, width, height
# command	shape and coordinates
# The possible commands are:
# "play", "stop", "open", "exit".
# The possible shapes and coordinates are:
# "rect" with 4 numbers giving x, y, width, and height;
# "circle" with 3 numbers giving x, y, and radius;
# "poly" with an even number of numbers, each pair describing the x
# and y coordinates of a point.

def parsegskin(file):
	dict = {}
	while 1:
		line = file.readline()
		if not line:
			break

		# ignore comments and empty lines
		# and strip off white space
		i = line.find('#')
		if i >= 0:
			line = line[:i]
		line = line.strip()
		if not line:
			continue

		# first part is GRiNS command
		line = line.split(' ', 1)
		if len(line) == 1:
			raise error, 'syntax error in skin'
		cmd, rest = line
		if cmd == 'image':
			dict[cmd] = rest.strip()
		else:
			coords = line.split(' ')
			if cmd == 'display':
				# display area is always rectangular
				shape = 'rect'
			else:
				shape = coords[0]
				del coords[0]
			try:
				coords = map(lambda v: int(v, 0), coords)
			except ValueError:
				raise error, 'syntax error in skin'
			if shape == 'poly' and coords[:2] == coords[-2:]:
				del coords[-2:]
			if (shape != 'rect' or len(coords) != 4) and \
			   (shape != 'circle' or len(coords) != 3) and \
			   (shape != 'poly' or len(coors) < 6 or len(coords) % 2 != 0):
				raise error, 'syntax error in skin'
			dict[cmd] = shape, coords
	if not dict.has_key('image'):
		raise error, 'image missing from skin description file'
	if not dict.has_key('display'):
		raise error, 'display region missing from skin description file'
	return dict
