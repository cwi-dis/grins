__version__ = "$Id$"

# WMP Export Sample
# export a simple scene to wmv

import wmwriter

# wmriter configuartion profile
profile = 20

###########################################

def LoadImageOn(dds, filename):
    import gear32sd
    img = gear32sd.load_file(filename)
    if img>=0:
        cx, cy, bpp = gear32sd.image_dimensions_get(img)
        hdc = dds.GetDC()
        x, y = (w-cx)/2, (h-cy)/2
        rc = x, y, x+cx, y+cy
        gear32sd.device_rect_set(img, rc)
        gear32sd.display_desktop_pattern_set(img,0)
        gear32sd.display_image(img, hdc)
        dds.ReleaseDC(hdc)
        gear32sd.image_delete(img)



###########################################

# viewport dimensions
w = 400
h = 300


###########################################
import ddraw

# create direct draw stuff
ddrawobj = ddraw.CreateDirectDraw()

# we need a window here, so use desktop
import win32ui
Sdk = win32ui.GetWin32Sdk()
ddrawobj.SetCooperativeLevel(Sdk.GetDesktopWindow().GetSafeHwnd(), ddraw.DDSCL_NORMAL)

# create our dd surface
ddsd = ddraw.CreateDDSURFACEDESC()
ddsd.SetFlags(ddraw.DDSD_WIDTH | ddraw.DDSD_HEIGHT | ddraw.DDSD_CAPS)
ddsd.SetCaps(ddraw.DDSCAPS_OFFSCREENPLAIN)
ddsd.SetSize(w,h)
dds = ddrawobj.CreateSurface(ddsd)
pxlfmt = dds.GetPixelFormat()

ddcolor = dds.GetColorMatch((0,0,255))
dds.BltFill((0, 0, w, h), ddcolor)

filename1 = r'D:\ufs\mmdocuments\interop2\interop2\images\frown.jpg'
filename2 = r'D:\ufs\mmdocuments\interop2\interop2\images\smile.jpg'

###########################################
# record manually coded presentation

# create writer
writer = wmwriter.WMWriter(dds, profile)
writer.setOutputFilename("grins.wmv")

# start wmv creation
writer.beginWriting()

LoadImageOn(dds, filename2)
writer.update(3)

LoadImageOn(dds, filename1)
writer.update(8)

# blank screen
dds.BltFill((0, 0, w, h), 0)
writer.update(13)
writer.update(13.1)

# finally:
writer.endWriting()

del writer

###########################################
