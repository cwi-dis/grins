__version__ = "$Id$"

image_cache = {}

def resolveImage(widget, src, noload = 0):
    import MMurl, X, img, imgformat, windowinterface
    visual = widget.visual
    if visual.c_class == X.TrueColor and visual.depth == 8:
        format = windowinterface.toplevel._imgformat
    else:
        format = imgformat.xcolormap
    dict = image_cache.get((src, format))
    if dict is not None:
        return dict
    if noload:
        return
    try:
        filename, info = MMurl.urlretrieve(src)
    except IOError:
        return
    try:
        reader = img.reader(format, filename)
    except:
        return
    is_transparent = 0
    if hasattr(reader, 'transparent') and \
       hasattr(reader, 'colormap'):
        is_transparent = 1
        reader.colormap[reader.transparent] = windowinterface.toplevel._colormap.QueryColor(widget.background)[1:4]
    if format is imgformat.xcolormap:
        colors = map(None, reader.colormap)
    else:
        colors = range(256)
        colors = map(None, colors, colors, colors)
    dict = {'width': reader.width, 'height': reader.height,
            'image_data': reader.read(), 'colors': colors}
    if not is_transparent:
        # only cache non-transparent images since the
        # background can be different next time we use
        # the image
        image_cache[(src, format)] = dict
    return dict
