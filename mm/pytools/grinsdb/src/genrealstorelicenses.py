"""genrealstorelicenses - Generate a file with licenses for the real store"""
import grlicense
import sys
import posix
import string

def main():
	if not (3 <= len(sys.argv) <= 5):
		print "Usage %s count outputfile [ product [ platform ] ]"%sys.argv[0]
		print "  Generates count licenses and stores them in the"
		print "  (dos-linefeeds) outputfile"
		print "  Default product",`grlicense.PRODUCT_TO_FEATURE[None]`
		print "    Pick from", grlicense.PRODUCT_TO_FEATURE.keys()
		print "  Default platform",`grlicense.PLATFORM_TO_PLATFORM[None]`
		print "    Pick from", grlicense.PLATFORM_TO_PLATFORM.keys()
		sys.exit(1)
	count = string.atoi(sys.argv[1])
	fp = open(sys.argv[2], "w")
	posix.chmod(sys.argv[2], 0444) # So we don't override it
	if len(sys.argv) > 3:
		product = sys.argv[3]
	else:
		product = None
	if len(sys.argv) > 4:
		platform = sys.argv[4]
	else:
		platform = None
	for i in range(count):
		license = grlicense.gencommerciallicense(product, platform)
		fp.write(license+'\r\n')
	fp.close()

main()

