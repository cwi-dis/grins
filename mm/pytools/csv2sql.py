# Disable licenses that have been revoked.
#
# The input is a comma-separated file (which has originally come
# from Real as a textfile, and has been cleaned up a little and
# passed through Excel) with records of the form
# XXXXX
# The output is a file of SQL statements that will look up the
# keys with status XXX in the sales database and set their XXX to XXX.
#
# Jack Jansen, Oratrix, December 2000
import string
import sys
import re

STRIPQUOTES=re.compile('"[^"]*"')

SQLSTMT="""
update licenses
        set active=False
        where licensekey='%s';
update ostransactions
        set transaction_state='revoke'
        from licenses
        where licenses.licensekey='%s'
          and licenses.transactid=ostransactions.transactid;
"""


def parseline(srcline):
    """Split a line into its constituent fields. Strip whitespace.
    We also remove quoted strings (not used in the fields we need)."""
    line = STRIPQUOTES.sub('', srcline)
    while line != srcline:
        srcline = line
        line = STRIPQUOTES.sub('', srcline)
    values = string.split(line, ',')
    return map(string.strip, values)

def outputsql(file, record):
    status, date, firstname, lastname, email, qty, platform, key = record
    if status == 'Type': # Header line
        pass
    elif status == 'SHP': # Shipped. Ignore.
        pass
    elif status in ('CREDIT', 'CHRGBK', 'CNCL'):
        stmt = SQLSTMT%(key, key)
        file.write(stmt)
    else:
        raise 'Unknown status field', record

def main():
    if len(sys.argv) == 1:
        file = sys.stdin
    elif len(sys.argv) == 2:
        file = open(sys.argv[1])
    else:
        sys.stderr.write("Usage: %s [filename]"%sys.argv[0])
        sys.exit(1)
    while 1:
        line = file.readline()
        if not line:
            break
        record = parseline(line)
        outputsql(sys.stdout, record)

if __name__ == '__main__':
    main()
