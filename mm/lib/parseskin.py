import MMurl, string, Sizes

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
