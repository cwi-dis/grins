# Font stuff.
# Interface:
#	setfont()
#	centerstring(left, top, right, bottom, str)


import string
import gl
import fm


# Tuning constants (set to match FORMS default)
FONTNAME = 'Helvetica'
FONTSIZE = 11

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

# Create a font object
f_font = fm.findfont(FONTNAME)		# The font at point size 1
f_font = f_font.scalefont(FONTSIZE)	# Scale it to the desired size

# Extract the font parameters from it
(f_printermatched, f_fixed_width, f_xorig, f_yorig, f_xsize, f_ysize, \
	f_fontheight, f_nglyphs) = f_font.getfontinfo()

# Calculate the baseline
f_baseline = f_fontheight - f_yorig

# In theory 'ysize' should exclude the leading, but in practice it is
# usually the same as 'fontheight'; we guess that the leading is the
# same as 'yorig'.
f_leading = f_yorig # Hack -- there's no parameter specifying this!

# Print some essential parameters
##print 'yorig =', f_yorig, 'ysize =', f_ysize, 'fontheight =', f_fontheight,
##print 'baseline =', f_baseline
###expected output: yorig = 4 ysize = 20 fontheight = 20 baseline = 16


# Select our font

def setfont():
	f_font.setfont()


# Subroutine to draw a string centered in a box, breaking lines if necessary

def centerstring(left, top, right, bottom, str):
	# This assumes f_font.setfont() has been called already
	width = right - left
	height = bottom - top
	curlines = [str]
	if height >= 2*f_fontheight:
		curlines = calclines([str], f_font.getstrwidth, width)[0]
	nlines = len(curlines)
	needed = nlines * f_fontheight
	if nlines > 1 and needed > height:
		nlines = max(1, height / f_fontheight)
		curlines = curlines[:nlines]
		curlines[-1] = curlines[-1] + '...'
	x0 = (left + right) * 0.5	# x center of box
	y0 = (top + bottom) * 0.5	# y center of box
	y = y0 - nlines * f_fontheight * 0.5 - f_leading
	for i in range(nlines):
		str = string.strip(curlines[i])
		# Get font parameters:
		w = f_font.getstrwidth(str)	# Width of string
		while str and w > width:
			str = str[:-1]
			w = f_font.getstrwidth(str)
		x = x0 - 0.5*w
		y = y + f_fontheight
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
