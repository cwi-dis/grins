__version__ = "$Id$"

# @win32doc|win32ig
# The ImageLib class defined in this module
# offers to other modules image decompression
# and display facilities.
# To achive this it loads and uses the ig module
# that exports the Accusoft Image Gear library


## ###########################

class ImageLib:
    def __init__(self):
        import gear32sd
        self.lib = gear32sd
        self._imglist = []
        self._transpdict = {}

    # Delete resources
    def deltemp(self):
        for img in self._imglist:
            if img>=0:
                self.lib.image_delete(img)
        self._imglist=[]
        self._transpdict = {}

    # Load image
    # 1. use abs filenames
    # 2. use temp files for gif
    # 3. use cash for gif conversion
    def load(self,filename):
        filename=self.toabs(filename)
        if self.islibexcept(filename):
            from windowinterface import error
            raise error, 'Not an image'
## BEGIN_INCLUDE_GIF
        img,gif_trans,trans_rgb=self.lib.load_gif(filename)
        if img>=0:
            if gif_trans>=0:
                self._transpdict[img]=trans_rgb
        else:
            img = self.lib.load_file(filename)
## BEGIN_NOT_INCLUDE_GIF
##         img = self.lib.load_file(filename)
## END_INCLUDE_GIF
        if img < 0:
            errcodes = []
            for i in range(self.lib.error_check()):
                errcodes.append(`self.lib.error_get(i)`)
            from windowinterface import error
            from string import join
            raise error, 'failed to load image, errcode(s) = %s' % join(errcodes, ', ')
        self._imglist.append(img)
        return img

    # Returns image size
    def size(self,img):
        if img<0: return 10,10,8
        return self.lib.image_dimensions_get(img)

    def gettransp(self, img):
        return self._transpdict.get(img)

    def read(self, img, crop = None):
        if crop is None:
            data = self.lib.area_get(img)
        else:
            data = self.lib.area_get(img, crop)
        return data

    def color_promote(self, img, flag):
        self.lib.color_promote(img, flag)

    # Render image
    def render(self, hdc, bgcolor, mask, img, src_x, src_y,dest_x, dest_y, width, height,
                       rcKeep, aspect = 'default'):
        if img<0: return

        if aspect == 'none':
            aspect = self.lib.IG_ASPECT_NONE
        else:
            aspect = self.lib.IG_ASPECT_DEFAULT

        if img not in self._imglist:
            # image already deleted?
            # XXXX this is a quick hack, since the image
            # shouldn't have been deleted if it was still
            # being used.
            print 'warning: win32 image management bug'
            return
        rc=(dest_x, dest_y, dest_x+width, dest_y+height)
        try:
            self.lib.ip_crop(img,rcKeep)
        except:
            errcodes = []
            for i in range(self.lib.error_check()):
                errcodes.append(`self.lib.error_get(i)`)
            from windowinterface import error
            from string import join
            raise error, 'failed to load image, errcode(s) = %s' % join(errcodes, ', ')
        if self._transpdict.has_key(img):
            trans_rgb = self._transpdict[img]
            self.lib.display_transparent_set(img,trans_rgb,1)
        rc = self.lib.display_adjust_aspect(img, rc, aspect)
        self.lib.device_rect_set(img,rc)
        self.lib.display_desktop_pattern_set(img,0)
        self.lib.display_image(img,hdc)

    # Delete image (release resources)
    def delete(self,img):
        if img<0:return
        self.lib.image_delete(img)
        if img in self._imglist:
            self._imglist.remove(img)
        if self._transpdict.has_key(img):
            del self._transpdict[img]

    # Create a DDB
    def createDDB(self,img, w=0, h=0):
        if img<0:return
        if w==0 or h==0:
            w,h,d=self.size(img)
        hbmp,hpal=self.lib.image_create_ddb(img,w,h)
        import win32ui
        bmp = win32ui.CreateBitmapFromHandle(hbmp)
        win32ui.GetWin32Sdk().DeleteObject(hpal)
        return bmp

    # Return the absolute filename
    def toabs(self,filename):
        import os,ntpath
        if os.path.isfile(filename):
            if not os.path.isabs(filename):
                filename=os.path.join(os.getcwd(),filename)
                filename=ntpath.normpath(filename)
        return filename


    # Accusoft gets grazy when it sees the following sig(s)
    # (enters an infinite loop consuming all available sys memory)
    def islibexcept(self,filename):
        lfn = filename
        lfn.lower()
        if lfn.find('.mpeg')>=0 or lfn.find('.mpg')>=0:
            return 1
        try:
            file = open(filename, 'rb')
            formdata = file.read(4)
            file.close()
        except:
            formdata = ''
        if formdata == '.RMF':
            return 1
        return 0


win32ig=ImageLib()
