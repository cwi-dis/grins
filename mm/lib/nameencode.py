__version__ = "$Id$"

def nameencode(value):
	"""Quote a value"""

	if '&' in value:
		value = string.join(string.split(value,'&'),'&amp;')
	if '>' in value:
		value = string.join(string.split(value,'>'),'&gt;')
	if '<' in value:
		value = string.join(string.split(value,'<'),'&lt;')
	if '"' in value:
		value = string.join(string.split(value,'"'),'&quot;')

	return '"' + value + '"'
