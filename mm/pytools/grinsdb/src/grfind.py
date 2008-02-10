import sys
import grinsdb
import getopt

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'k:vlf')
    except getopt.error:
        print 'Usage: grfind [-k keyname] [-v] value ...'
        sys.exit(0)
    key = 'email'
    verbose = 0
    long = 0
    fullname = 0
    for o, a in opts:
        if o == '-k':
            key = a
        if o == '-v':
            verbose = 1
        if o == '-l':
            long = 1
        if o == '-f':
            fullname = 1
    dbase = grinsdb.Database()
    allids = []
    for value in args:
        ids = dbase.search(key, value)
        for id in ids:
            if not id in allids:
                allids.append(id)
        if verbose and not ids:
            print '** Not found:', value
    for id in allids:
        if long:
            print "(Record %s)"%id
            fp = dbase.openfp(id)
            sys.stdout.write(fp.read())
        elif verbose:
            obj = dbase.open(id)
            print '%s\t%s'%(id, obj['email'])
        elif fullname:
            print dbase.filename(id)
        else:
            print id
    dbase.close()
    if not allids:
        sys.exit(1)

if __name__ == '__main__':
    main()
