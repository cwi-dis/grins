# Font stuff.
# Interface:
#  f = FontOject().init(fontname, fontsize)
#  f.setfont()
#  f.centerstring(left, top, right, bottom, str)
# This writes in the current GL window


# Some technical terms
#.......................+.............+.............+..................#
#                       |             |             |leading           #
#......ff...............|.............|.............+..................#
#     f                 |             |                                #
#....ffff..pppp.........|baseline.....|fontheight...+..................#
#     f    p   p        |             | ==          |                  #
#     f    p   p        |             |ysize        |(x-height)        #
#     f    p   p        |             |             |                  #
#.....f....pppp........ +..+..........|.............+..................#
#          p               |yorig     |                                #
#..........p...............+..........+................................#


import string
import gl
import fm


class FontObject:

	# Create a new font object
	def init(self, fontname, fontsize):
		self.fontname = fontname
		self.fontsize = fontsize

		# Create a font object
		font1 = fm.findfont(self.fontname)
			# The font at point size 1
		self.font = font1.scalefont(self.fontsize)
			# Scale it to the desired size

		# Extract the font parameters from it
		(self.printermatched, self.fixed_width, self.xorig, \
		 self.yorig, self.xsize, self.ysize, self.fontheight, \
		 self.nglyphs) = self.font.getfontinfo()

		# Calculate the baseline
		self.baseline = self.fontheight - self.yorig

		# In theory 'ysize' should exclude the leading, but in
		# practice it is usually the same as 'fontheight'; we
		# guess that the leading is the same as 'yorig'.
		self.leading = self.yorig
			# Hack -- there's no parameter specifying this!

		# Print some essential parameters
		##print 'yorig =', self.yorig, 'ysize =', self.ysize,
		##print 'fontheight =', self.fontheight,
		##print 'baseline =', self.baseline
		##expected output:
		##yorig = 4 ysize = 20 fontheight = 20 baseline = 16

		return self

	# Select our font
	def setfont(self):
		self.font.setfont()

	# Calculate the width of a string using our font
	def getstrwidth(self, str):
		return self.font.getstrwidth(str)

	# Draw a string centered in a box, breaking lines if necessary
	def centerstring(self, left, top, right, bottom, str):
		# This assumes self.setfont() has been called already
		width = right - left
		height = bottom - top
		curlines = [str]
		if height >= 2*self.fontheight:
		   curlines = calclines([str], self.font.getstrwidth, width)[0]
		nlines = len(curlines)
		needed = nlines * self.fontheight
		if nlines > 1 and needed > height:
			nlines = max(1, height / self.fontheight)
			curlines = curlines[:nlines]
			curlines[-1] = curlines[-1] + '...'
		x0 = (left + right) * 0.5	# x center of box
		y0 = (top + bottom) * 0.5	# y center of box
		y = y0 - nlines * self.fontheight * 0.5 - self.leading
		for i in range(nlines):
			str = string.strip(curlines[i])
			# Get font parameters:
			w = self.font.getstrwidth(str)	# Width of string
			while str and w > width:
				str = str[:-1]
				w = self.font.getstrwidth(str)
			x = x0 - 0.5*w
			y = y + self.fontheight
			gl.cmov2(x, y)
			fm.prstr(str)


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
	spw = sizefunc(' ')
	okcount = -1
	totsize = 0
	totcount = 0
	for w in words:
		if w:
			addsize = sizefunc(w)
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


# --- Backward compatibility ---

f_forms = FontObject().init('Helvetica', 10)
f_fontheight = f_forms.fontheight
setfont = f_forms.setfont
centerstring = f_forms.centerstring
