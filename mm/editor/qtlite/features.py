__version__ = "$Id$"

# Features for GRiNS for QT, lite version

from compatibility import *
from FeatureSet import *
import sys

#
version = 'lite'
compatibility = QT
compatibility_short = 'QT'
cmif = 0
lightweight = 1
editor = 1
level = 'lite'
license_features_needed = ('light', sys.platform)
