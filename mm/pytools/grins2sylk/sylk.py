#
# simple SYLK writer
#
# fredrik lundh, january 1999
#
#  fredri-@pythonware.com
# http://www.pythonware.com
#

import operator

def write_sylk(fp, data, id="Python"):
    fp.write("ID;P%s" % id)
    y = 1
    for row in data:
        x = 1
        for item in row:
            if x == 1:
                fp.write("\nC;Y%d;X1;K" % y)
            else:
                fp.write("\nC;X%d;K" % x)
            if operator.isNumberType(item):
                fp.write(str(item))
            else:
                fp.write('"%s"' % item)
            x = x + 1
        y = y + 1
    fp.write("\nE\n")

fp = open("test.slk", "w")
write_sylk(fp, [("a", "b", "c"), (1, 2, 3)])
fp.close()
