__version__ = "$Id$"

# License dialog
import string
import sys
from licparser import *
from LicenseDialog import LicenseDialog, EnterkeyDialog
import settings
import features

class WaitLicense(LicenseDialog):
    def __init__(self, callback, feat):
        self.can_try = 0
        self.can_eval = 0

        self.callback = callback
        self.features = feat
        self.secondtime = 0
        self.dialog = None

        self._user = ''
        self._org = ''
        self._licensestr = ''

        if self.accept_license():
            self.do_callback()
        else:
            LicenseDialog.__init__(self)
            self.setdialoginfo()
            self.show()

    def accept_license(self, newlicense=None, user="", organization=""):
        if newlicense:
            self._licensestr = newlicense
        try:
            self.license = License(self.features, newlicense, user, organization)
            if not self.license.msg:
                return 1        # Everything fine, permanent license
            # Evaluation license
            self.msg = self.license.msg
            self.can_try = 1
            self.can_eval = 0
            return 0
        except Error, arg:
            pass
        self.msg = arg
        self.can_try = 0
        if arg == "" and \
           hasattr(features, 'AUTO_EVALUATE') and hasattr(features, 'feature_set') and \
           features.AUTO_EVALUATE in features.feature_set:
            # No license. If auto-evaluate is available
            # in this product we attempt to create an
            # auto-evaluate license
            from AutoLicense import AutoEvaluateLicense
            self.can_eval = 0
            try:
                self.license = AutoEvaluateLicense()
                self.msg = self.license.msg
                self.can_try = 1
            except Error, arg:
                self.msg = arg
        elif arg == EXPIRED:
            self.can_eval = 0
        else:
            self.can_eval = 1
        return 0

    def cb_quit(self):
        self.close()
        import sys
        sys.exit(0)

    def cb_try(self):
        self.close()
        self.do_callback()

    def cb_buy(self):
        import Help
        Help.givehelp('buy', web=1)

    def cb_eval(self):
        import Help
        Help.givehelp('eval', web=1)

    def cb_open(self):
        import windowinterface
        windowinterface.FileDialog("Select file containing license key", "", "", "",
                        self.cb_open_ok, None, 1)

    def cb_open_ok(self, filename):
        try:
            license = GetLicenseFromFile(filename)
        except Error, arg:
            self.msg = arg
            self.setdialoginfo()
        else:
            self.ok_callback(license)

    def cb_enterkey(self, license=''):
        if not self._user:
            self._user = settings.get('license_user')
            if self._user is None:
                self._user = ''
            if self._user[-18:] == ' (evaluation copy)':
                self._user = self._user[:-18]
        if not self._org:
            self._org = settings.get('license_organization')
            if self._org is None:
                self._org = ''
        if self._licensestr is None:
            self._licensestr = ''
        EnterkeyDialog(self.ok_callback, user=self._user, org=self._org, license=self._licensestr)

    def ok_callback(self, str, name=None, organization=None):
        str = string.strip(str)
        if not name is None:
            self._user = name
        if self._user[-18:] == ' (evaluation copy)':
            self._user = self._user[:-18]
        if not organization is None:
            self._org = organization
        if self.accept_license(str, name, organization):
            self.close()
            self.do_callback()
        else:
            self.setdialoginfo()

    def do_callback(self):
        license = self.license
        callback = self.callback
        del self.license
        del self.callback
        callback(license)
