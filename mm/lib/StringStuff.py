__version__ = "$Id$"

import string

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
            sublist.append((len(curlines), start, start+i))
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
    words = string.split(s, ' ')
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
