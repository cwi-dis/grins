import grins_app_core
resdll = None

runApp = 1

embedded = 0
commodule = None

class PlayerApp(grins_app_core.GrinsApp):
	def BootGrins(self):
		import exec_cmif
		exec_cmif.Boot(0)

try:
	import grinspapi
except ImportError:
	grinspapi = None

if grinspapi:
	grinspapi.OleInitialize()
	import sys
	for i in range(1, len(sys.argv)):
		arg = sys.argv[i]
		if arg[:1]=='/' or arg[:1]=='-':
			val = arg[1:]
			if val == 'UnregServer':
				grinspapi.UnregisterServer()
				runApp = 0
			elif val == 'RegServer':
				grinspapi.RegisterServer()
				runApp = 0
			elif val == 'Embedding':
				sys.argv = sys.argv[:1]
				embedded = 1
				runApp = 1
	if runApp:
		commodule = grinspapi.CreateComModule()
		if not embedded: commodule.Lock()
	else:
		grinspapi.OleUninitialize()

if runApp:
	grins_app_core.fix_argv()
	grins_app_core.BootApplication(PlayerApp)

