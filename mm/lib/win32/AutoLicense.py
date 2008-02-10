from licparser import *
import features
import version
import time
import win32reg
import win32con

# This class has the same interface as licparser.License
# It represents an evaluation license that is automatically
# created when first running the program.
# The Windows version does this by putting some stuff in the
# registry. The "Ajax" is there so we can find them back (for
# debugging), it's a word we should be able to remember while
# it isn't connected to Oratrix/GRiNS.

REGKEY=r"CLSID\%s"
REGCONTENT=r"""
[HKEY_CLASSES_ROOT\CLSID\%s]
"Name"="Ajax"
"Cookie"="%d"
"""

def daynum():
    t = time.time()
    t = t / (24*60*60)
    return int(t)

class AutoEvaluateLicense:
    def __init__(self):
        if 0:   # expired
            raise Error, EXPIRED
        key = REGKEY % version.guid
        if not win32reg.hasKey(key, win32con.HKEY_CLASSES_ROOT):
            self._create()
        data = win32reg.getKeyValue(key, "Cookie",
                win32con.HKEY_CLASSES_ROOT)
        try:
            expdaynum = eval(data)
            expdaynum = eval(expdaynum)
        except:
            raise Error, "Could not obtain evaluation license"
        self.__moredays = expdaynum - daynum()
        if self.__moredays <= 0:
            raise Error, EXPIRED
        self.msg = 'Evaluation copy, %d more days left' \
                % self.__moredays

    def _create(self):
        stopday = daynum() + features.auto_evaluate_period
        data = REGCONTENT % (version.guid, stopday)
        win32reg.register(data)

    def have(self, *feat):
        return 1

    def need(self, *feat):
        return None

    def userinfo(self):
        return ''

    def is_evaluation_license(self):
        return 1
