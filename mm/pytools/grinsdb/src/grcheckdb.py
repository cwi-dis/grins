"""checkdb - check the database and generate a new htpasswd file"""
import os
import string
import whrandom
import crypt
import sys
import time
import rfc822
import grinsdb
import grpasswd


# Keys on which we want to index
KEYS=['email']

class Error(Exception):
    pass

def main():
    if len(sys.argv) > 1:
        print "Usage checkdb"
        sys.exit(1)
    dbase = grinsdb.Database(indexed=0)
    index = grinsdb.Index(keys=KEYS)
    try:
        allids = dbase.search(None, None)
        emaildict = {}
        badids = []
        print 'Checking email addresses and creating index',
        count = 0
        for id in allids:
            count = count + 1
            if count % 100 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()
            obj = dbase.open(id)
            index.update(id, obj)
            if not obj.has_key('email'):
                badids.append(id)
                continue
            email = obj['email']
            if emaildict.has_key(email):
                emaildict[email].append(id)
            else:
                emaildict[email] = [id]
        sys.stdout.write('\n')
        index.close()
        del index
        if badids:
            print 'Bad messages:',
            for id in badids:
                print id,
                obj = dbase.open(id, 'w')
                dbase.remove(obj)
            print
        for email in emaildict.keys():
            if len(emaildict[email]) > 1:
                print 'Multiple:', email,
                for i in emaildict[email]:
                    print i,
                print

        genfiles(dbase)
    finally:
        dbase.close()

def myopen(filename):
    dirname = os.path.join(grinsdb.DATABASE, 'data')
    return open(os.path.join(dirname, filename + '.NEW'), 'w')

def myinstall(filename):
    dirname = os.path.join(grinsdb.DATABASE, 'data')
    name =  os.path.join(dirname, filename)
    os.rename(name + '.NEW', name)

def genfiles(dbase):
    passwd_fp = myopen('htpasswd')
    news_fp = myopen('grins-news')
    edit_fp = myopen('grins-edit-news')

    allids = dbase.search(None, None)
    print 'Generating password and mailinglist files',
    count = 0
    for id in allids:
        count = count + 1
        if count % 100 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()
        obj = dbase.open(id)
        if not obj.has_key('email'):
            print 'Missing email:', id
            continue
        if not obj.has_key('password'):
            print 'Missing password:', id
            continue
        user = obj['email']
        clear = obj['password']
        crypted = crypt_passwd(clear)
        add_passwd(passwd_fp, user, crypted)
        if obj.has_key('want-maillist') and \
           obj['want-maillist'] == 'yes':
            news_fp.write(user+'\n')
        if obj.has_key('want-editor') and \
           obj['want-editor'] == 'yes':
            edit_fp.write(user+'\n')
    sys.stdout.write('\n')
    passwd_fp.close()
    news_fp.close()
    edit_fp.close()
    myinstall('htpasswd')
    myinstall('grins-news')
    myinstall('grins-edit-news')

def crypt_passwd(clear):
    salt = grpasswd.invent_passwd(2)
    return crypt.crypt(clear, salt)

def add_passwd(fp, user, passwd):
    if ':' in user or '\n' in user or ':' in passwd or '\n' in passwd:
        raise Error, "Illegal username/password"
    fp.write('%s:%s\n'%(user, passwd))

main()
