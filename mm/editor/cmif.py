# This module provides a public interface to the function findfile
# defined in main.py.  Dependent on how the program was started (with
# main.py as standard input or with "import main") we find the
# function in __main__ or in main.
#
# (We can't define the function here and import it from main, because
# main must *use* it to patch up the Python search path!)

import sys

for mod in ('main', 'grins', 'cmifed', '__main__'):
	if sys.modules.has_key(mod) and hasattr(sys.modules[mod], 'findfile'):
		findfile = sys.modules[mod].findfile
		break
	else:
		raise ImportError('no module named cmif')
