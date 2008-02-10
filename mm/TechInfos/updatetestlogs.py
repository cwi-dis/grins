import sys
import os
import string

TESTLOGS=["testlog_mac.txt", "testlog_unix.txt", "testlog_win.txt"]

def getsmilfiles(dirname):
    allfiles = os.listdir(dirname)
    rv = []
    for file in allfiles:
        if file[-4:] == '.smi' or file[-5:] == '.smil':
            rv.append(file)
    rv.sort()
    return rv

def updatetestlog(logfilename, testfilelist):
    fp = open(logfilename, 'r')
    loglines = fp.readlines()
    output = []
    while loglines and testfilelist:
        loglinefilename = string.split(loglines[0])[0]
        if loglinefilename == '#':
            # Comment: pass through
            output.append(loglines[0])
            del loglines[0]
        elif loglinefilename < testfilelist[0]:
            # A file that has disappeared from te testset. Save as comment
            output.append('# ' + loglines[0])
            del loglines[0]
        elif loglinefilename == testfilelist[0]:
            # Normal case: existing test
            output.append(loglines[0])
            del loglines[0]
            del testfilelist[0]
        else:
            # A new test
            output.append(testfilelist[0]+'\n')
            del testfilelist[0]
    output = output + loglines
    for fn in testfilelist:
        output.append(fn + '\n')
    del fp
    os.rename(logfilename, logfilename+'.BAK')
    fp = open(logfilename, "w")
    fp.writelines(output)

def main():
    if len(sys.argv) != 2:
        if sys.platform == 'mac':
            import macfs
            fss, ok = macfs.GetDirectory("Where are the interop documents?")
            if not ok:
                sys.exit(0)
            dirname = fss.as_pathname()
        else:
            print >>sys.stderr, "Usage: %s interopdirname"%sys.argv[0]
            sys.exit(1)
    else:
        dirname = sys.argv[1]
    files = getsmilfiles(dirname)
    for testlog in TESTLOGS:
        updatetestlog(testlog, files[:])

if __name__ == '__main__':
    main()
