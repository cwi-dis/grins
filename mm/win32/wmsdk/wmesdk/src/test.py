

import wmeapi

wmeapi.OleInitialize()

print dir(wmeapi)

enc = wmeapi.CreateAsfRTEncoder()

print dir(enc)


# an interface class for AsfRTEncoder dispatch interface
# should be created automatically (see vc studio support)
class AsfRTEncoder:
    def __init__(self):
        self._enc = wmeapi.CreateAsfRTEncoder()
    def start(self):
        self._enc.InvokeMethod('Start')
    def stop(self):
        self._enc.InvokeMethod('Stop')
    def loadASD(self,fn):
        self._enc.LoadASD(fn)
    def setaudio(self,val):
        enc.IntPropertyPut('AllowAudio')
# etc .................................



enc.LoadASD(r'D:\ufs\mm\cmif\win32\wmsdk\wmesdk\bin\aud1.asd')

enc.Start()

print 'AllowAudio', enc.IntPropertyGet('AllowAudio')
print 'AllowVideo', enc.IntPropertyGet('AllowVideo')
print 'Bandwidth', enc.IntPropertyGet('Bandwidth')


print 'AudioFormatTag', enc.IntPropertyGet('AudioFormatTag')
print 'RecordDuration', enc.IntPropertyGet('RecordDuration')

enc.Stop()


wmeapi.OleUninitialize()
