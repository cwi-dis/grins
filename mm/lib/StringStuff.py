import string

# Draw a string centered in a box, breaking lines if necessary
def centerstring(dlist, left, top, right, bottom, str):
	wx, wy, wid, heig = dlist._window._hWnd.GetClientRect()
	if heig == 0:
		heig = 1
	#fontheight = dlist.fontheight()
	fontheight = dlist._font._pointsize
	baseline = dlist.baseline()
	width = int((right - left)*wid)
	height = int((bottom - top)*heig)
	curlines = [str]
	if height >= 2*fontheight:
		curlines = calclines([str], dlist.strsize, right - left)[0]
	nlines = len(curlines)
	needed = nlines * fontheight
	if nlines > 1 and needed > height:
		nlines = max(1, int(height / fontheight))
		curlines = curlines[:nlines]
		curlines[-1] = curlines[-1] + '...'
	x0 = (left + right) * 0.5	# x center of box
	y0 = (top + bottom) * 0.5	# y center of box
	y = y0 - nlines * fontheight * 0.5/heig
	for i in range(nlines):
		str = string.strip(curlines[i])
		# Get font parameters:
		w = dlist.strsize(str)[0]	# Width of string
		while str and w > right - left:
			str = str[:-1]
			w = dlist.strsize(str)[0]
		x = x0 - 0.5*w
		#y = y + baseline
		#y = y + dlist._font._pointsize/heig
		dlist.setpos(x, y)
		dstx = int(x * wid + 0.5)
		dsty = int(y * heig + 0.5)+dlist._font._pointsize*i
		#dlist.writestr(str)
		dlist.writeText(dlist._font._fontname, dlist._font._pointsize, -1, str, dstx, dsty)


# Calculate a set of lines from a set of paragraphs, given a font and
# a maximum line width.  Also return mappings between paragraphs and
# line numbers and back: (1) a list containing for each paragraph a
# list of triples (lineno, start, end) where start and end are the
# offset into the paragraph, and (2) a list containing for each line a
# triple (parno, start, end)

def calclines(parlist, sizefunc, limit):
	partoline = []
	linetopar = []
	curlines = []
	for parno in range(len(parlist)):
		par = parlist[parno]
		sublist = []
		partoline.append(sublist) # It will grow while in there
		start = 0
		while 1:
			i = fitwords(par, sizefunc, limit)
			n = len(par)
			while i < n and par[i] == ' ': i = i+1
			sublist.append(len(curlines), start, start+i)
			curlines.append(par[:i])
			linetopar.append((parno, start, start+i))
			par = par[i:]
			start = start + i
			if not par: break
	return curlines, partoline, linetopar


# Find last occurence of space in string such that the size (according
# to some size calculating function) of the initial substring is
# smaller than a given number.  If there is no such substrings the
# first space in the string is returned (if any) otherwise the length
# of the string. Assume sizefunc() is additive:
# sizefunc(s + t) == sizefunc(s) + sizefunc(t)

def fitwords(s, sizefunc, limit):
	words = string.splitfields(s, ' ')
	spw = sizefunc(' ')[0]
	okcount = -1
	totsize = 0
	totcount = 0
	for w in words:
		if w:
			addsize = sizefunc(w)[0]
			if totsize > 0 and totsize + addsize > limit:
				break
			totsize = totsize + addsize
			totcount = totcount + len(w)
			okcount = totcount
		# The space after the word
		totsize = totsize + spw
		totcount = totcount + 1
	if okcount < 0:
		return totcount
	else:
		return okcount
