import grins_app_core
resdll = None

class PlayerApp(grins_app_core.GrinsApp):
	def BootGrins(self):
		import exec_cmif
		exec_cmif.Boot(0)

grins_app_core.BootApplication(PlayerApp)
