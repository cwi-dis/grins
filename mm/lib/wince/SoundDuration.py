__version__ = "$Id$"

# Cache info about sound files

import MMurl

__version__ = "$Id$"

# Cache info about sound files

# Used to get full info
def getfullinfo(url):
    u = MMurl.urlopen(url)
    if u.headers.subtype in ('mp3', 'mpeg', 'x-mp3'):
        import winmm, winuser
        try:
            decoder = winmm.CreateMp3Decoder()
        except winmm.error, msg:
            print msg
            u.close()
            return 0, 8000, []
        decode_buf_size = 8192
        data = u.read(decode_buf_size)
        u.close()
        wfx = decoder.GetWaveFormat(data)
        decbuf = ''
        status = len(data)
        decdata, done, inputpos, status = decoder.DecodeBuffer(data)
        if done>0:
            decbuf = decbuf + decdata[:done]
        while not status:
            decdata, done, status, status = decoder.DecodeBuffer()
            if done>0:
                decbuf = decbuf + decdata[:done]
        if status > 0:
            status = status - 1
        decfactor = 1.137*len(decbuf)/float(decode_buf_size - status)
        filename = MMurl.urlretrieve(url)[0]
        fsize = winuser.GetFileSize(filename)
        dur = (decfactor*fsize)/float(wfx[2])
        dur = 0.001*int(dur*1000.0)
        return dur, 1, []

    import audio
    from MMurl import urlretrieve
    try:
        filename = urlretrieve(url)[0]
        a = audio.reader(filename)
        nframes = a.getnframes()
        framerate = a.getframerate()
        markers = a.getmarkers()
    except (audio.Error, IOError, EOFError), msg:
        print 'error in sound file', url, ':', msg
        return 0, 8000, []
    return nframes, framerate, markers

def get(url):
    nframes, framerate, markers = getfullinfo(url)
    if nframes == 0: nframes = framerate
    duration = float(nframes) / framerate
    return duration

def getmarkers(url):
    nframes, framerate, markers = getfullinfo(url)
    if not markers:
        return []
    xmarkers = []
    invrate = 1.0 / framerate
    for id, pos, name in markers:
        xmarkers.append((id, pos*invrate, name))
    return xmarkers
