import grins_app_core
resdll = None

class PlayerApp(grins_app_core.GrinsApp):
	def BootGrins(self):
		import exec_cmif
		exec_cmif.Boot(0)

try:
	import grinspapi
except ImportError:
	grinspapi = None

runApp = 1

if grinspapi:
	import sys
	grinspapi.OleInitialize()
	for i in range(1, len(sys.argv)):
		arg = sys.argv[i]
		if arg[:1]=='/' or arg[:1]=='-':
			val = arg[1:]
			if val == 'UnregServer':
				grinpapi.UnregisterServer()
				runApp = 0
			elif val == 'RegServer':
				grinpapi.RegisterServer()
				runApp = 0
			elif val == 'Embedding':
				sys.argv = sys.argv[:1]
				runApp = 1
		
if not runApp:
	grinspapi.OleUninitialize()
else:
	grins_app_core.fix_argv()
	grins_app_core.BootApplication(PlayerApp)

