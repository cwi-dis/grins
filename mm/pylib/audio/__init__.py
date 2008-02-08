__version__ = "$Id$"

Error = 'audio.Error'

def reader(filename, dstfmts = None, dstrates = None, loop = 1, filetype = None):
    import file, convert
    rdr = file.reader(filename, filetype = filetype)
    return convert.convert(rdr, dstfmts, dstrates, loop)
