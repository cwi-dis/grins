__version__ = "$Id$"

import Xm, Xmd, X
from types import *
from XTopLevel import toplevel
from XConstants import error

class _ButtonSupport:
    # helper class to create a button
    # this class calls three methods that are not defined here:
    # _get_acceleratortext, _set_callback, and _set_togglelabels.

    __pixmapcache = {}
    __pixmaptypes = (
            'label',
            'labelInsensitive',
            'select',
            'selectInsensitive',
            'arm',
            )

    def _create_button(self, parent, visual, colormap, entry, extra_callback = None):
        btype = 'p'
        initial = 0
        if type(entry) is TupleType:
            label, callback = entry[:2]
            if len(entry) > 2:
                btype = entry[2]
                if type(btype) is TupleType:
                    btype, initial = btype
        else:
            label, callback = entry, None
        if btype == 't':
            widgettype = Xm.ToggleButton
            callbacktype = 'valueChangedCallback'
            attrs = {'set': initial}
            if type(label) is DictType and label.has_key('select'):
                attrs['indicatorOn'] = 0
        else:
            widgettype = Xm.PushButton
            callbacktype = 'activateCallback'
            attrs = {}
        if type(callback) is ClassType:
            attrs['sensitive'] = 0
            acceleratorText = self._get_acceleratortext(callback)
            if acceleratorText:
                attrs['acceleratorText'] = acceleratorText
        button = parent.CreateManagedWidget('button', widgettype, attrs)
        if callback is not None:
            if type(callback) not in (ClassType, TupleType):
                callback = callback, (label,)
            self._set_callback(button, callbacktype, callback)
        if extra_callback is not None:
            self._set_callback(button, callbacktype, extra_callback)
        if type(label) is StringType:
            button.labelString = label
            return button
        if type(label) is TupleType:
            if btype != 't' or len(label) != 2:
                raise error, 'bad label for menu button'
            self._set_togglelabels(button, label)
            return button
        attrs = {'labelType': Xmd.PIXMAP,
                 'marginHeight': 0,
                 'marginWidth': 0}
        import imgconvert, splash
        # calculate background RGB values in case (some)
        # images are transparent
        bg = button.background
        if visual.c_class == X.PseudoColor:
            r, g, b = colormap.QueryColor(bg)[1:4]
        else:
            s, m = splash._colormask(visual.red_mask)
            r = int(float((bg >> s) & m) / (m+1) * 256)
            s, m = splash._colormask(visual.green_mask)
            g = int(float((bg >> s) & m) / (m+1) * 256)
            s, m = splash._colormask(visual.blue_mask)
            b = int(float((bg >> s) & m) / (m+1) * 256)
        for pmtype in self.__pixmaptypes:
            rdr = label.get(pmtype)
            if rdr is None:
                continue
            if self.__pixmapcache.has_key(rdr):
                pixmap = self.__pixmapcache[rdr]
            else:
                rdr = imgconvert.stackreader(toplevel._imgformat, rdr)
                if hasattr(rdr, 'transparent'):
                    rdr.colormap[rdr.transparent] = r, g, b
                data = rdr.read()
                pixmap = toplevel._main.CreatePixmap(rdr.width,
                                                     rdr.height)
                ximage = visual.CreateImage(
                        visual.depth, X.ZPixmap, 0, data,
                        rdr.width, rdr.height,
                        toplevel._imgformat.descr['align'], 0)
                ximage.byte_order = toplevel._byteorder
                pixmap.CreateGC({}).PutImage(ximage, 0, 0, 0, 0,
                                             rdr.width, rdr.height)
                self.__pixmapcache[label[pmtype]] = pixmap
            attrs[pmtype + 'Pixmap'] = pixmap
        button.SetValues(attrs)
        return button
