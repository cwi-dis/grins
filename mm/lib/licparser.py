__version__ = "$Id$"

# Lowlevel handling of licenses (shared between editor and generating
# programs)
import string
import sys

FEATURES={
        "editor": 0x01,
        "light":0x02,
        "pro": 0x04,
        "smil2player": 0x100,
        "smil2light": 0x200,
        "smil2pro": 0x400,
        "embeddedplayer": 0x800,
        "smil2real": 0x1000,
        "ALLPRODUCTS": 0x1f07,

        # Special bit that signifies that this license
        # was registered when generated.
        "preregistered": 0x2000,

        # Bits that signify this is an upgrade license
        "upgradefromsmil2real": 0x4000,
        "upgradefromsmil1editor": 0x8000,
        "UPGRADEBITS": 0xc000,

        # platform bits. The names are sys.platform values.
        # Multiple names mapping to 1 bit is ok.
        "win32": 0x08,
        "mac": 0x10,
        "irix6": 0x20,
        "sunos5": 0x40, # untested
        "linux2": 0x80, # untested
        "ALLPLATFORMS": 0xf8,

}

MAGIC=13

Error="license.error"

NOTYET="Not licensed yet"
EXPIRED="Your evaluation copy has expired"

class Features:
    def __init__(self, license, args):
        self.license = license
        self.args = args

    def __del__(self):
        apply(self.license._release, self.args)
        del self.license
        del self.args

class License:
    def __init__(self, features, newlicense=None, user="", organization=""):
        # Obtain a license, and state that we need at least one
        # of the features given
        import settings
        if newlicense:
            lic = newlicense
        else:
            lic = settings.get('license')
        self.__available_features, self.__licensee, self.__moredays = \
                                   _parselicense(lic)
        for f in self.__available_features:
            if f[:7] == 'upgrade':
                is_upgrade = 1
                break
        else:
            is_upgrade = 0
        if is_upgrade:
            msg = self.getbaselicense()
            if msg:
                raise Error, msg
        if not user:
            user = settings.get('license_user')
            if user[-18:] == ' (evaluation copy)':
                user = user[:-18]
        if not organization:
            organization = settings.get('license_organization')
        # If this is a personalized license force the user/organization
        if self.__licensee:
            if ',' in self.__licensee:
                lfields = string.split(self.__licensee, ',')
                user = lfields[0]
                organization = string.join(lfields[1:], ',')
            else:
                # One field: force only organization
                organization = self.__licensee
        for f in features:
            if not self.have(f):
                if f == sys.platform:
                    raise Error, "License not valid for this OS/platform"
                else:
                    raise Error, "License not valid for this program"
        if not user and not organization:
            raise Error, "You must specify user or organization name"

        self.msg = ""
        if type(self.__moredays) == type(0):
            if self.__moredays < 0:
                raise Error, EXPIRED
            self.msg = "Evaluation copy, %d more days left"%self.__moredays
        if newlicense:
            settings.set('license', newlicense)
            if self.__moredays:
                user = user + ' (evaluation copy)'
            settings.set('license_user', user)
            settings.set('license_organization', organization)
            if not settings.save():
                import windowinterface
                windowinterface.showmessage(
                        'Cannot save license! (File permission problems?)')
            if not self.__licensee:
                if user and organization:
                    self.__licensee = user + ', ' + organization
                elif user:
                    self.__licensee = user + ', '
                else:
                    self.__licensee = organization
        else:
            if self.__moredays:
                user = user + ' (evaluation copy)'
            settings.set('license_user', user)
            settings.set('license_organization', organization)

    def have(self, *features):
        # Check whether we have the given features
        for f in features:
            if not f in self.__available_features:
                return 0
        return 1

    def need(self, *features):
        # Obtain a locked license for the given features.
        # The features are released when the returned object is
        # freed
        if not apply(self.have, features):
            raise Error, "Required license feature not available"
        return Features(self, features)

    def userinfo(self):
        # If this license is personal return the user name/company
        return self.__licensee

    def _release(self, features):
        pass

    def is_evaluation_license(self):
        return type(self.__moredays) == type(0)

    def getbaselicense(self):
        import settings
        basefeaturewanted = []
        baseproductnames = []
        for f in self.__available_features:
            if f == "upgradefromsmil2real":
                basefeaturewanted.append("smil2real")
                baseproductnames.append("GRiNS/RealOne")
            if f == "upgradefromsmil1editor":
                basefeaturewanted.append("editor")
                basefeaturewanted.append("light")
                basefeaturewanted.append("pro")
                baseproductnames.append("any GRiNS 1 authoring product")
        baseproductnames = string.join(baseproductnames, " or ")
        self._baselicense = settings.get('baselicense')
        if not self._baselicense:
            import windowinterface
            windowinterface.InputDialog("Old license key:", "", self.cb_oldkey)
        if not self._baselicense:
            return "Need existing license for %s" % baseproductnames
        try:
            old_features, old_licensee, old_moredays = _parselicense(self._baselicense)
        except Error:
            settings.set('baselicense', '')
            return "Invalid old license, please check again"
        if old_moredays:
            return "Cannot upgrade evaluation license"
        for f in basefeaturewanted:
            if f in old_features:
                break
        else:
            settings.set('baselicense', '')
            return "Only upgrades licenses for %s" % baseproductnames
        settings.set('baselicense', self._baselicense)
        return None

    def cb_oldkey(self, value):
        value = string.strip(value)
        self._baselicense = value

_CODEBOOK="ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
_DECODEBOOK={}
for _ch in range(len(_CODEBOOK)):
    _DECODEBOOK[_CODEBOOK[_ch]] = _ch

def _decodeint(str):
    value = 0
    shift = 0
    for ch in str:
        try:
            next = _DECODEBOOK[ch]
        except KeyError:
            raise Error, "Invalid license"
        value = value | (next << shift)
        shift = shift + 5
    return value

def _decodestr(str):
    rv = ''
    if (len(str)&1):
        raise Error, "Invalid license"
    for i in range(0, len(str), 2):
        rv = rv + chr(_decodeint(str[i:i+2]))
    return rv

def _decodedate(str):
    if len(str) != 5:
        raise Error, "Invalid license"
    yyyy= _decodeint(str[0:3])
    mm = _decodeint(str[3])
    dd = _decodeint(str[4])
    if yyyy < 3000:
        return yyyy, mm, dd
    return None

def _codecheckvalue(items):
    value = 1L
    fullstr = string.join(items, '')
    for i in range(len(fullstr)):
        thisval = (MAGIC+ord(fullstr[i])+i)
        value = value * thisval + ord(fullstr[i]) + i
    return int(value & 0xfffffL)

def _decodelicense(str):
    all = string.split(str, '-')
    check = all[-1]
    all = all[:-1]
    if not len(all) in (4,5) or all[0] != 'A':
        raise Error, "This does not look like a license"
    if _codecheckvalue(all) != _decodeint(check):
        raise Error, "Invalid license, possibly a typing error"
    uniqid = _decodeint(all[1])
    date = _decodedate(all[2])
    features = _decodeint(all[3])
    if len(all) > 4:
        user = _decodestr(all[4])
    else:
        user = ""
    return uniqid, date, features, user

def _parselicense(str):
    if not str:
        raise Error, ""
    uniqid, date, features, user = _decodelicense(str)
    if user:
        user = "Licensed to: " + user
    if date and date[0] < 3000:
        import time
        t = time.time()
        values = time.localtime(t)
        today = mkdaynum(values[:3])
        expiry = mkdaynum(date)
        moredays = expiry - today
        if moredays == 0:
            moredays = 1    # Don't want to return zero
    else:
        moredays = None
    fnames = []
    for name, value in FEATURES.items():
        if (features & value) == value:
            fnames.append(name)
    return fnames, user, moredays

def mkdaynum((year, month, day)):
    import calendar
    # Januari 1st, in 0 A.D. is arbitrarily defined to be day 1,
    # even though that day never actually existed and the calendar
    # was different then...
    days = year*365                 # years, roughly
    days = days + (year+3)/4        # plus leap years, roughly
    days = days - (year+99)/100     # minus non-leap years every century
    days = days + (year+399)/400    # plus leap years every 4 centirues
    for i in range(1, month):
        if i == 2 and calendar.isleap(year):
            days = days + 29
        else:
            days = days + calendar.mdays[i]
    days = days + day
    return days

def GetLicenseFromFile(filename):
    try:
        fp = open(filename)
    except:
        raise Error, "Cannot open license file"
    firstline = 1
    while 1:
        line = fp.readline()
        if not line:
            raise Error, "File does not contain a recognizable license"
        if firstline:
            # Treat first line special: this may be a file with only a license in it
            attempt = string.strip(line)
            try:
                _decodelicense(attempt)
            except Error:
                pass
            else:
                return attempt
        firstline = 0
        # For other lines we only look for "bla bla bla: licensekey"
        if not ":" in line:
            continue
        fields = string.split(line, ":")
        if len(fields) != 2:
            continue
        attempt = string.strip(fields[1])
        try:
            _decodelicense(attempt)
        except Error:
            continue
        return attempt
