__version__ = "$Id$"

import sys

mediaWrapper = """\
<smil>
  <body>
    <ref%s src="%s"/>
  </body>
</smil>"""

def MediaRead(filename, mtype, printfunc):
	import SMILTreeRead
	if mtype is None or \
		(mtype[:6] != 'audio/' and
		mtype[:6] != 'video/'):
		dur = ' dur="indefinite"'
	else:
		dur = ''
	root = SMILTreeRead.ReadString(mediaWrapper % (dur, filename), filename, printfunc)
	if sys.platform == 'win32':
		mediaNode = root.GetChildren()[0]
		import Duration
		dur = Duration.getintrinsicduration(mediaNode, 0)
		if dur:
			mediaNode.attrdict['duration'] = dur
	return root