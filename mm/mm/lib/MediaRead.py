__version__ = "$Id$"

from nameencode import nameencode
from SMILTreeRead import ReadString
from Duration import getintrinsicduration

mediaWrapper = """\
<smil>
  <body>
    <ref%s src=%s/>
  </body>
</smil>"""

def MediaRead(filename, mtype, printfunc):
	if mtype is None or \
		(mtype[:6] != 'audio/' and
		 mtype[:6] != 'video/' and
		 mtype.find('real') < 0):
		dur = ' dur="indefinite"'
	else:
		dur = ''
	root = ReadString(mediaWrapper % (dur, nameencode(filename)), filename, printfunc)
	mediaNode = root.GetChildren()[0]
	dur = getintrinsicduration(mediaNode, 0)
	if dur:
		mediaNode.attrdict['duration'] = dur
	return root
