error = 'audiodev.error'

def AudioDev(qsize = None):
	try:
		import al, Audio_SGI
	except ImportError:
		try:
			import sunaudiodev, Audio_sun
		except ImportError:
			try:
				import Audio_mac
			except ImportError:
				raise error, 'no audio device'
			else:
				return Audio_mac.Play_Audio_mac(qsize = qsize)
		else:
			return Audio_sun.Play_Audio_sun(qsize = qsize)
	else:
		return Audio_SGI.Play_Audio_sgi(qsize = qsize)

def test(fn = 'f:just samples:just.aif'):
	import aifc
	af = aifc.open(fn, 'r')
	print fn, af.getparams()
	p = AudioDev()
	p.setoutrate(af.getframerate())
	p.setsampwidth(af.getsampwidth())
	p.setnchannels(af.getnchannels())
	BUFSIZ = af.getframerate()/af.getsampwidth()/af.getnchannels()
	while 1:
		data = af.readframes(BUFSIZ)
		if not data: break
		print len(data)
		p.writeframes(data)
	p.wait()

if __name__ == '__main__':
	test()
