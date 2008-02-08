__version__ = "$Id$"

import win32api

import win32con

class Version:
    major, minor, build, platform, servpack  = win32api.GetVersionEx()

    platformstr = {win32con.VER_PLATFORM_WIN32_WINDOWS:'Win9x', win32con.VER_PLATFORM_WIN32_NT:'NT'}

    def __repr__(self):
        return '%d, %d, %d, %s, %s ' % (Version.major, Version.minor, Version.build, \
                Version.platformstr[Version.platform], Version.servpack)

    def isWin9x(self):
        return Version.platform == win32con.VER_PLATFORM_WIN32_WINDOWS and \
                Version.major == 4 and Version.minor in (0, 10, 90)

    def isNT(self):
        return Version.platform == win32con.VER_PLATFORM_WIN32_NT

    def isWin95(self):
        return Version.platform == win32con.VER_PLATFORM_WIN32_WINDOWS and\
                Version.major == 4 and Version.minor == 0

    def isWin98(self):
        return Version.platform == win32con.VER_PLATFORM_WIN32_WINDOWS and\
                Version.major == 4 and Version.minor == 10

    def isWinMe(self):
        return Version.platform == win32con.VER_PLATFORM_WIN32_WINDOWS and\
                Version.major == 4 and Version.minor == 90

    def isNT4(self):
        return Version.platform == win32con.VER_PLATFORM_WIN32_NT and\
                Version.major == 4 and Version.minor == 0

    def isWin2k(self):
        return Version.platform == win32con.VER_PLATFORM_WIN32_NT and\
                Version.major == 5 and Version.minor == 0

    def isWinXP(self):
        return Version.platform == win32con.VER_PLATFORM_WIN32_NT and\
                Version.major == 5 and Version.minor == 1


osversion = Version()
