
def ExportPowerPoint(filename, outdir = None):
    import pptauto
    try:
        if outdir:
            nslides = pptauto.Export(filename, outdir)
        else:
            nslides = pptauto.Export(filename)
    except pptauto.error, arg:
        print arg
        return -1
    else:
        return nslides


if __name__ == '__main__':
    filename = r'D:\ufs\mm\cmif\win32\PowerPoint\testdata\test1.ppt'
    nslides = ExportPowerPoint(filename)
    if nslides >= 0:
        print nslides, 'slides exported'
