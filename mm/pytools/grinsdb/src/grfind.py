import sys
import grinsdb
import getopt

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'k:v')
	except getopt.error:
		print 'Usage: grfind [-k keyname] [-v] value ...'
		sys.exit(0)
	key = 'email'
	verbose = 0
	for o, a in opts:
		if o == '-k':
			key = a
		if o == '-v':
			verbose = 1
	dbase = grinsdb.Database()
	allids = []
	for value in args:
		ids = dbase.search(key, value)
		for id in ids:
			if not id in allids:
				allids.append(id)
	for id in allids:
		if verbose:
			obj = dbase.open(id)
			print '%s\t%s'%(id, obj['email'])
		else:
			print id

if __name__ == '__main__':
	main()
	
