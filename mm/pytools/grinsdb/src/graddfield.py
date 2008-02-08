"""graddfield - Add a field to a record, if it doesn't exist yet"""

import maildb
import grinsdb
import sys

def main():
    if len(sys.argv) not in (3,4):
        print "Usage: graddfield user field [value]"
        sys.exit(1)
    user = sys.argv[1]
    field = sys.argv[2]
    dbase = grinsdb.Database()
    if len(sys.argv) <= 3:
        value = getfield(dbase, user, field)
        print "%s: %s = %s"%(user, field, value)
    else:
        value = sys.argv[3]
        addfield(dbase, user, field, value, override=1)
    dbase.close()

def getfield(dbase, user, field):
    idlist = dbase.search('email', user)
    if not idlist:
        print 'No such user:', user
        sys.exit(1)
    if len(idlist) > 1:
        print 'Multiple matches:',
        for id in idlist:
            print id,
        dbase.close()
        sys.exit(1)
    record = dbase.open(idlist[0])
    if record.has_key(field):
        return record[field]
    return None

def addfield(dbase, user, field, value, override=0):
    idlist = dbase.search('email', user)
    if not idlist:
        print 'No such user:', user
        dbase.close()
        sys.exit(1)
    if len(idlist) > 1:
        print 'Multiple matches:',
        for id in idlist:
            print id,
        dbase.close()
        sys.exit(1)
    record = dbase.open(idlist[0], 'w')
    if not override and record.has_key(field):
        print 'Field already exists:'
        print '    User: %s'%user
        print '    %s: %s'%(field, record[field])
        dbase.save(record)
        return
    record[field] = value
    dbase.save(record)

def delfield(dbase, user, field):
    idlist = dbase.search('email', user)
    if not idlist:
        print 'No such user:', user
        dbase.close()
        sys.exit(1)
    if len(idlist) > 1:
        print 'Multiple matches:',
        for id in idlist:
            print id,
        dbase.close()
        sys.exit(1)
    record = dbase.open(idlist[0], 'w')
    if not record.has_key(field):
        return
    del record[field]
    dbase.save(record)

if __name__ == '__main__':
    main()
