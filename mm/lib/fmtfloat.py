__version__ = "$Id$"

# this module contains a feww useful functions to deal with floats

# format a floating point number as a string
# never return anything in scientific notation
# optionally add a suffix
# optionally add a sign
# optionally round at a given precision
def fmtfloat(val, suffix = '', withsign = 0, prec = -1):
    if val < 0:
        val = -val
        sign = '-'
    elif withsign:
        sign = '+'
    else:
        sign = ''
    if prec >= 0:
        # round value
        val = val + 0.5 * 10.0 ** -prec
    str = '%g' % val
    if 'e' in str:
        import string
        str, x = string.split(str, 'e')
        strs = string.split(str, '.')
        if len(strs) == 1:
            str1 = strs[0]
            str2 = ''
        else:
            str1, str2 = strs
        if x[0] == '-':
            x = int(x[1:])
            str = '0'*x + str1 + str2
            str = str[:len(str1)] + '.' + str[len(str1):]
        else:
            x = int(x)
            str = str1 + str2 + '0'*x
            str = str[:len(str1) + x] + '.' + str[len(str1) + x:]
    if '.' in str:
        while str[-1] == '0':
            str = str[:-1]
        if str[-1] == '.':
            str = str[:-1]
    if prec >= 0 and '.' in str:
        import string
        str1, str2 = string.split(str, '.')
        if prec == 0:
            str = str1
        else:
            str2 = str2 + '0'*prec
            str = str1 + '.' + str2[:prec]
            # still remove trailing zeros
            while str[-1] == '0':
                str = str[:-1]
            if str[-1] == '.':
                str = str[:-1]
    while len(str) > 1 and str[0] == '0' and str[1] in '0123456789':
        str = str[1:]
    if not str:
        str = '0'
    return sign + str + suffix

# truncate a floating point number to an integer (always towards
# -infinity)
def trunc(x):
    if x < 0:
        return trunc(x + 1024) - 1024
    return int(x)

# round a floating point number to the nearest integer
def round(x):
    return trunc(x + 0.5)

# return the precision of the number represented by str
def getprec(str):
    prec = 0
    if '.' in str:
        while str[-1] == '0':
            str = str[:-1]
        while str[-1] != '.':
            str = str[:-1]
            prec = prec + 1
    return prec
