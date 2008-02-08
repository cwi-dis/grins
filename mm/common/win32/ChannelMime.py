__version__ = "$Id$"

# mapping from channel type to supported MIME types
ChannelMime = {
        'image': [
                'image/gif',
##         'image/ief',
                'image/jpeg',
                'image/png',
                'image/tiff',
                'image/bmp', ## ++
                'image/x-cmu-raster',
##         'image/x-portable-anymap',
##         'image/x-portable-bitmap',
##         'image/x-portable-graymap',
##         'image/x-portable-pixmap',
                'image/x-rgb',
##         'image/x-xbitmap',
##         'image/x-xpixmap',
##         'image/x-xwindowdump',
                'image/svg-xml',
                'image/x-wmf',
                'image/x-emf',
                ],
        'sound': [
                'application/vnd.rn-realmedia', # but only if it's audio only
                'audio/basic',
                'audio/vnd.rn-realaudio',
                'audio/x-pn-realaudio',
                'audio/x-realaudio',
                'audio/x-aiff',
                'audio/x-wav',
                'audio/mpeg', ## ++
                'audio/x-mp3',          # obsolete (?) MIME type for MP3
                'audio/mp3',
                'audio/x-ms-wma',## ++
                ],
        'video': [
                'application/vnd.rn-realmedia', # but only if it contains video
                'application/x-shockwave-flash',
                'image/vnd.rn-realflash',
                'video/mpeg',
                'video/quicktime',
                'video/vnd.rn-realvideo',
                'image/vnd.rn-realpix',
                'text/vnd.rn-realtext',
                'video/x-msvideo', ## ++
                'video/msvideo',        # some servers erroneously use this
                'video/x-ms-wmv', ## ++
##         'video/x-sgi-movie',
                ],
        'html': ['text/html',],
        'text': ['text/plain',],
##     'RealPix': ['image/vnd.rn-realpix',],
##     'RealText': ['text/vnd.rn-realtext',],
        }

# reverse mapping: from MIME type to channel type
MimeChannel = {}
for key, vals in ChannelMime.items():
    for val in vals:
        if not MimeChannel.has_key(val):
            MimeChannel[val] = []
        MimeChannel[val].append(key)
