"""genrealstorelicenses - Generate a file with licenses for the real store"""
import grlicense
import sys
import posix
import string

def main():
	if len(sys.argv) != 3:
		print "Usage %s count outputfile"%sys.argv[0]
		print "  Generates count licenses and stores them in the"
		print "  (dos-linefeeds) outputfile"
		sys.exit(1)
	count = string.atoi(sys.argv[1])
	fp = open(sys.argv[2], "w")
	posix.chmod(sys.argv[2], 0444) # So we don't override it
	for i in range(count):
		license = grlicense.gencommerciallicense()
		fp.write(license+'\r\n')
	fp.close()

main()

