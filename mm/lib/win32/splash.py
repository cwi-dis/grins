__version__ = "$Id$"

""" @win32doc|splash
This module contains the interface to create and
destroy the splash screen displayed atapplication startup. 
The actual implementation class
of the splash is SplashDlg in lib/win32/components.py
It consists of just two simple functions.
"""

# Create and display the splash screen
def splash(arg=0,version=None):
	global _splash
	import components
	if not _splash:
		_splash=components.SplashDlg(arg,version)

# Destroy the splash screen		
def unsplash():
	global _splash
	if _splash:_splash.close()
	_splash=None

_splash=None
