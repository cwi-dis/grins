# Minimal player application, mainly for testing.

import sys
import audio, audio.dev

def play(file):
    dev = audio.dev.writer()             # open output device
    # open the audio file and convert to an acceptable format
    rdr = audio.reader(file, dev.getformats(), dev.getframerates())
    # tell device about format and frame rate
    dev.setformat(rdr.getformat())
    dev.setframerate(rdr.getframerate())
    # read and play the file
    while 1:
        data, nf = rdr.readframes(10000) # read and convert 10,000 audio frames
        if not data:                     # if no data, we reached the end
            break
        dev.writeframes(data)            # send data to device
    dev.wait()                           # wait for output to drain
    
if __name__ == '__main__':
	if not sys.argv[1:]:
		print 'Usage: %s audiofile ...' % sys.argv[0]
		sys.exit(1)
	for file in sys.argv[1:]:
		print 'Playing %s...' % file
		play(file)
		
