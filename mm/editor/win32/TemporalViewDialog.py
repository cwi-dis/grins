__version__ = "$Id$"

class TemporalViewDialog(ViewDialog):
	adornments = {}

	def __init__(self):
		ViewDialog.__init__(self, 'cview_')

	def show(self, title):
		title = 'Temporal View (' + self.toplevel.basename + ')'
		print "TODO"

	
