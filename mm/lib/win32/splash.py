_splash=None

def splash(arg=0,version=None):
	print version
	global _splash
	import components
	if not _splash:
		_splash=components.SplashDlg(arg,version)
			
def unsplash():
	global _splash
	if _splash and hasattr(_splash,'DestroyWindow'):
		_splash.DestroyWindow()
	_splash=None
