import grins_app_core
resdll = None

class EditorApp(grins_app_core.GrinsApp):
    def BootGrins(self):
        import exec_cmif
        exec_cmif.Boot(1)

grins_app_core.fix_argv()
grins_app_core.BootApplication(EditorApp)
