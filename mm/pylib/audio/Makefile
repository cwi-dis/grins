
# Customizations -- you *may* have to edit these

DOCDIR=		../../../python/Doc

# Where are the various programs?
LATEX=		latex
BIBTEX=		bibtex
EMACS=		emacs
DVIPS=		dvips -f
MAKEINDEX=	makeindex
PYTHON=		python
MAKEINFO=	makeinfo
L2H=		/ufs/guido/l2h/latex2html
L2HARGS=	-address $$USER@`domainname` -dont_include myformat

# Install destination -- not used now but might be useful some time...
DESTDIR=	/usr/local
LIBDESTDIR=	$DESTDIR/lib
LIBDEST=	$LIBDESTDIR/python
DOCDESTDIR=	$LIBDEST/doc

# Ideally, you shouldn't need to edit beyond this point

# Main target
lib:	lib.dvi

# Dependencies
lib.dvi: boilerplate.tex copyright.tex

boilerplate.tex:
	ln -s $(DOCDIR)/texinputs/boilerplate.tex .

copyright.tex:
	ln -s $(DOCDIR)/texinputs/copyright.tex .

LIBFILES=libaudio.tex

lib.dvi: $(LIBFILES)
	$(DOCDIR)/tools/newind.py > lib.ind
	TEXINPUTS=:$(DOCDIR)/texinputs $(LATEX) lib
	$(DOCDIR)/tools/fix_hack lib.idx
	$(MAKEINDEX) lib
	TEXINPUTS=:$(DOCDIR)/texinputs $(LATEX) lib
	$(DVIPS) lib >lib.ps

# Housekeeping targets

# Remove temporary files
clean:
	rm -f @* *~ *.aux *.idx *.ilg *.ind *.log *.toc *.blg *.bbl *.pyc
	rm -f *.bak *.orig
	# Sources: .tex, .bib, .sty
	# Useful results: .dvi, .ps, .texi, .info

# Remove temporaries as well as final products
clobber: clean
	 rm -f *.dvi *.ps *.texi *.info *.info-[0-9]*

PYFILES = __init__.py aifc.py au.py convert.py dev.py devmac.py devsgi.py \
	devsun.py devwin.py file.py format.py merge.py select.py wav.py what.py
DOCFILES = boilerplate.tex lib.tex libaudio.tex
dist:	$(PYFILES) $(DOCFILES) Makefile
	tar cf - $(PYFILES) $(DOCFILES) Makefile | gzip > audio.tar.gz
