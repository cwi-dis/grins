__version__ = "$Id$"

# These flag bits are used in all grins code
# each bit is corresponding to a specific compatibility
# actualy there 6 flags witch corresponding to:
#
# FLAG_G2_LIGHT: g2 light version
# FLAG_QT_LIGHT: qt light version
# etc ...
#
# Actualy, these flags are used for both menu templates and attrdefs file.
#
# In the menu templates and attrdefs, all flags that are on must be present in the
# set of flags that is returned by curflags().  In other words, the
# test that is done is '(flags & curflags()) != 0'.  This means
# that in the menu templates you should set a combinaison of LIGHT_G2_LIGHT,
# FLAG_G2_PRO, FLAG_QT_LIGHT, FLAG_QT_PRO, FLAG_CMIF, FLAG_SMIL_1_0, DBG.
# The predefinated combinaison flags are:
# FLAG_G2, FLAG_QT and FLAG_ALL
#
# in the attrdefs file, flags are set in the same way for specify the visible attributes in formularies,
# according to the grins version.

FLAG_G2_LIGHT = 0x0001
FLAG_G2_PRO = 0x0002
FLAG_QT_LIGHT = 0x0004
FLAG_QT_PRO = 0x0008

FLAG_CMIF = 0x0010
FLAG_SMIL_1_0 = 0x0020
FLAG_BOSTON = 0x0040

FLAG_TEMPLATE = 0x2000
FLAG_ADVANCED = 0x4000
FLAG_DBG = 0x8000



# some abbreviations
FLAG_G2 = FLAG_G2_LIGHT | FLAG_G2_PRO
FLAG_QT = FLAG_QT_LIGHT | FLAG_QT_PRO
FLAG_PRO = FLAG_G2_PRO | FLAG_QT_PRO | FLAG_SMIL_1_0 | FLAG_BOSTON
FLAG_ALL = FLAG_G2 | FLAG_QT | FLAG_CMIF | FLAG_SMIL_1_0 | FLAG_BOSTON

_curflags = None

def curflags():
    global _curflags
    if _curflags is None:
        import settings
        import features
        flags = FLAG_BOSTON
        if hasattr(features, 'feature_set'):
            if features.EXPORT_REAL in features.feature_set:
                flags = flags | FLAG_G2
            if features.EXPORT_QT in features.feature_set:
                flags = flags | FLAG_QT
            if features.EXPORT_SMIL2 in features.feature_set:
                flags = flags | FLAG_BOSTON
        elif features.compatibility == features.G2:
            if features.lightweight:
                flags = flags | FLAG_G2_LIGHT
            else:
                flags = flags | FLAG_G2_PRO
        elif features.compatibility == features.QT:
            if features.lightweight:
                flags = flags | FLAG_QT_LIGHT
            else:
                flags = flags | FLAG_QT_PRO
        elif features.compatibility == features.SMIL10:
            flags = flags | FLAG_SMIL_1_0
        elif features.compatibility == features.Boston:
            flags = flags | FLAG_BOSTON
        if settings.get('cmif'):
            flags = flags | FLAG_CMIF
        if settings.get('debug'):
            flags = flags | FLAG_DBG
        _curflags = flags
    return _curflags
