all:		prepimg showprep

prepimg:	prepimg.o
		$(CC) prepimg.o -limage -o prepimg

showprep:	showprep.o
		$(CC) showprep.o -lgl_s -o showprep

# Not needed any more...
showimg:	showimg.o
		$(CC) showimg.o -limage -lgl_s -o showimg
