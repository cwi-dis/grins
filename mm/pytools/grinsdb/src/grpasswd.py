"""grpasswd - Set or print the GRiNS password for a customer"""

import maildb
import grinsdb
from graddfield import addfield, getfield
import sys
import whrandom

def main():
    if len(sys.argv) not in (2,3):
        print "Usage: grpasswd user [passwd]"
        sys.exit(1)
    user = sys.argv[1]
    passwd = None
    if len(sys.argv) > 2:
        passwd = sys.argv[2]
    dbase = grinsdb.Database()
    if not passwd:
        passwd = getfield(dbase, user, 'Password')
        if passwd:
            print 'User: %s'%user
            print 'Password: %s'%passwd
        else:
            print 'User %s has no password'%user
    else:
        if passwd == '-':
            passwd = invent_passwd()
        addfield(dbase, user, 'Password', passwd, override=1)
    dbase.close()

def addpasswd(obj, passwd='-'):
    """Helper for register: add password to a record"""
    if passwd == '-':
        passwd = invent_passwd()
    obj['password'] = passwd


def invent_passwd(length=6):
    """Invent a password. Not industry-strenght but good enough for us"""
    ok = "abcdefghijkmnopqrstuvwxyz023456789"
    rv = ''
    for i in range(length):
        rv = rv + whrandom.choice(ok)
    return rv

if __name__ == '__main__':
    main()
