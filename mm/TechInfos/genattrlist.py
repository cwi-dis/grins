import sys
import os
sys.path.append(os.path.join(os.pardir, 'lib'))
import SMIL

fp = open('smil2-attribute-support-new.txt', 'w')
taglist = SMIL.SMIL.attributes.items()
taglist.sort()
for tag, dict in taglist:
	if tag[:5] == 'http:':
		continue
	fp.write("Tag %s:\n"%tag)
	attrlist = dict.keys()
	attrlist.sort()
	for attr in attrlist:
		if attr[:5] == 'http:':
			continue
		fp.write("\tAttribute %s:\n"%attr)
		fp.write("\t\tto be supplied\n")
fp.close()
