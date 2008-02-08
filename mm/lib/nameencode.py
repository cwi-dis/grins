__version__ = "$Id$"

def nameencode(value):
    # Quote a value

    quot = None
    newvalue = []

    for c in value:
        if c == '&':
            newvalue.append('&amp;')
        elif c == '>':
            newvalue.append('&gt;')
        elif c == '<':
            newvalue.append('&lt;')
        elif c == '"':
            if quot is None:
                quot = "'"
            if c == quot:
                newvalue.append('&quot;')
            else:
                newvalue.append(c)
        elif c == "'":
            if quot is None:
                quot = '"'
            if c == quot:
                newvalue.append('&apos;')
            else:
                newvalue.append(c)
        elif 32 <= ord(c) <= 127: # ' ' .. '~', the ASCII characters
            newvalue.append(c)
        else:
            try:
                newvalue.append('&#x%x;' % ord(unicode(c, 'iso-8859-1')))
            except UnicodeError:
                # not correct, but it'll have to do
                newvalue.append('&#x%x;' % ord(c))

    if quot is None:
        quot = '"'

    return quot + ''.join(newvalue) + quot
