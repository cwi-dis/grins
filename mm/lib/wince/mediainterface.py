__version__ = "$Id$"


is_dummy = 0

class Image:
    def __init__(self):
        pass

    def GetSize(self):
        return 100, 100

    def GetDepth(self):
        return 24

# this method should return an object with at least the above Image interface
def get_image(filename, params = 0):
    if is_dummy: return Image()
    import wingdi
    try:
        return wingdi.CreateDIBSurfaceFromFile(params, filename)
    except wingdi.error, arg:
        print arg
        return Image()
