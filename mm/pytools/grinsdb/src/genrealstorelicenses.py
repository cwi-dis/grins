"""genrealstorelicenses - Generate a file with licenses for the real store"""
import grlicense
import sys
import posix
import string

def main():
	if not (3 <= len(sys.argv) <= 4):
		print "Usage %s count outputfile [ product ]"%sys.argv[0]
		print "  Generates count licenses and stores them in the"
		print "  (dos-linefeeds) outputfile"
		sys.exit(1)
	count = string.atoi(sys.argv[1])
	fp = open(sys.argv[2], "w")
	posix.chmod(sys.argv[2], 0444) # So we don't override it
	if len(sys.argv) > 3:
		product = sys.argv[3]
	else:
		product = None
	for i in range(count):
		license = grlicense.gencommerciallicense(product)
		fp.write(license+'\r\n')
	fp.close()

main()

