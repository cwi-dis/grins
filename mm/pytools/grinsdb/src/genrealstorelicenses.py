"""genrealstorelicenses - Generate a file with licenses for the real store"""
import grlicense
import sys
import posix
import string
import getopt

def main():
    opts, args = getopt.getopt(sys.argv[1:], 'u:o:')
    if not (2 <= len(args) <= 4):
        print "Usage %s [-u user ] [ -o organization ] count outputfile [ product [ platform ] ]"%sys.argv[0]
        print "  Generates count licenses and stores them in the"
        print "  (dos-linefeeds) outputfile"
        print "  Default product",`grlicense.PRODUCT_TO_FEATURE[None]`
        print "    Pick from", grlicense.PRODUCT_TO_FEATURE.keys()
        print "  Default platform",`grlicense.PLATFORM_TO_PLATFORM[None]`
        print "    Pick from", grlicense.PLATFORM_TO_PLATFORM.keys()
        sys.exit(1)
    user = organization = None
    for o, a in opts:
        if o == '-u':
            user = a
        if o == '-o':
            organization = a
    count = string.atoi(args[0])
    fp = open(args[1], "w")
    posix.chmod(args[1], 0444) # So we don't override it
    if len(args) > 2:
        product = args[2]
    else:
        product = None
    if len(args) > 3:
        platform = args[3]
    else:
        platform = None
    for i in range(count):
        license = grlicense.gencommerciallicense(version=product, platform=platform,user=user, organization=organization)
        fp.write(license+'\r\n')
    fp.close()

main()
