__version__ = "$Id$"

def GetImageSize(file):
    import img
    try:
        rdr = img.reader(None, file)
    except img.error:
        return 0, 0
    else:
        return rdr.width, rdr.height
