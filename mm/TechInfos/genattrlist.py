import sys
import os
sys.path.append(os.path.join(os.pardir, 'lib'))
import SMIL

oldattrs = {}
try:
    fp = open('smil2-attribute-support.txt', 'r')
except IOError:
    pass
else:
    while 1:
        line = fp.readline()
        if not line:
            break
        if line[:1] == '#':
            line = line[1:]
        if line[:4] == 'Tag ':
            tag = line[4:-2]
            oldattrs[tag] = {}
        elif line[:11] == '\tAttribute ':
            attr = line[11:-2]
        elif line[:2] == '\t\t':
            oldattrs[tag][attr] = line[2:-1]
        else:
            print 'cannot parse line',`line[:-1]`
    fp.close()

fp = open('smil2-attribute-support-new.txt', 'w')
taglist = SMIL.SMIL.attributes.items()
taglist.sort()
for tag, dict in taglist:
    if tag[:5] == 'http:':
        continue
    fp.write("Tag %s:\n"%tag)
    attrlist = dict.keys()
    if oldattrs.has_key(tag):
        for key in oldattrs[tag].keys():
            if key not in attrlist:
                attrlist.append(key)
    attrlist.sort()
    for attr in attrlist:
        if attr[:5] == 'http:':
            continue
        if dict.has_key(attr):
            comment = ''
        else:
            comment = '#'
        if oldattrs.has_key(tag) and oldattrs[tag].has_key(attr):
            val = oldattrs[tag][attr]
        else:
            val = 'to be supplied'
        if comment == '#' and val == 'to be supplied':
            continue
        fp.write("%s\tAttribute %s:\n"%(comment,attr))
        fp.write("%s\t\t%s\n" % (comment, val))
fp.close()
