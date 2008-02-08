"""HTML elements.

Clases representing SMIL elements, subclassed from DOM.core.Element.
"""

from xml.dom.pydom import makeElementClass, Element
import string

def makeAll():
    empties = ['BR', 'HR', 'IMG']
    non_empties = [
            'SMIL',
            'HEAD', 'META', 'LAYOUT',
            'BODY',
##         'ROOT-LAYOUT',
            'REGION',
            'ANIMATION', 'AUDIO', 'VIDEO', 'TEXT', 'TEXTSTREAM',
            'IMG', 'REF',
            'PAR', 'SEQ', 'SWITCH',
            'A', 'ANCHOR'
    ]

    for name in empties:
        c = makeElementClass(string.lower(name))
        c.is_empty = 1
        globals()[name] = c

    for name in non_empties:
        c = makeElementClass(string.lower(name))
        globals()[name] = c

class ROOT_LAYOUT(Element): tagName = GI = "root-layout"

makeAll()
del makeAll

if __name__ == '__main__':
    t = SMIL(HEAD(LAYOUT(ROOT_LAYOUT(title='Title'), REGION(id='one'))),
             BODY(PAR(IMG(src="test.jpg"),AUDIO(src="test.au"))))


    print t.getChildren()
    from xml.dom.writer import XmlWriter

    l = XmlWriter()
    l.write(t)
