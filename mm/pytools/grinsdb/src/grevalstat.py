"""grevalstat - Get evaluation key statistics"""
import os
import string
import whrandom
import crypt
import sys
import time
import rfc822
import grinsdb
import grpasswd

MONTHS={'jan':1, 'feb':2, 'mar':3, 'apr':4, 'may':5, 'jun':6, 'jul':7,
        'aug':8, 'sep':9, 'oct':10, 'nov':11, 'dec':12}

Error="grcheckdb.Error"

def main():
    if len(sys.argv) > 1:
        print "Usage grevalstat"
        sys.exit(1)
    try:
        dbase = grinsdb.Database()
        allids = dbase.search(None, None)
        ddict = {}
        for id in allids:
            obj = dbase.open(id)
            if not obj.has_key('eval-license-req'):
                continue
            dates = obj['eval-license-req']
            date = string.strip(string.split(dates, ',')[-1])
            pdate = parsedate(date)
            if ddict.has_key(pdate):
                ddict[pdate] = ddict[pdate] + 1
            else:
                ddict[pdate] = 1
        pdates = ddict.keys()
        pdates.sort()
        pdates.reverse()
        for pdate in pdates:
            print pdate[3], ddict[pdate]
    finally:
        dbase.close()

def parsedate(date):
    [dd, mmstr, yy] = string.split(date, '-')
    mm = MONTHS[string.lower(mmstr)]
    return (yy, mm, dd, date)

main()
