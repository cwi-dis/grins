__version__ = "$Id$"
import sys, string
from patchlevel import patchlevel
import features

shortversion = 'grins%s-%s-%s-1.5.1'%(features.level, features.compatibility_short, sys.platform)
version = '%sfor %s, v1.5.1 %s' % (features.level and (string.capitalize(features.level) + ' '), features.compatibility, patchlevel)
macpreffilename = 'GRiNS-%s%s%s-1.5 Prefs' % (features.level, (features.level and '-'), features.compatibility_short)
