__version__ = "$Id$"

# Additional MIME types for the GRiNS player and editor.

mimetypes = {
	'.smi': 'application/smil',
	'.smil': 'application/smil',
	'.cmi': 'application/x-grins-cmif',
	'.cmif': 'application/x-grins-cmif',
	'.grins': 'application/x-grins-project',
	'.xgrins': 'application/x-grins-binary-project',
	'.gskin': 'text/x-grins-skin',

	'.ra': 'audio/vnd.rn-realaudio',
	'.ram': 'audio/x-pn-realaudio',
	'.rmm': 'audio/x-pn-realaudio',
	'.rp': 'image/vnd.rn-realpix',
	'.rt': 'text/vnd.rn-realtext',
	'.rv': 'video/vnd.rn-realvideo',
	'.rf': 'image/vnd.rn-realflash',
	'.swf': 'application/x-shockwave-flash',
	'.rm': 'application/vnd.rn-realmedia',

	'.mp3': 'audio/mpeg',
	'.bmp': 'image/bmp',
	'.asf': 'video/x-ms-asf',
	'.wma': 'audio/x-ms-wma',
	'.wmv': 'video/x-ms-wmv',

	'.svg': 'image/svg-xml',
 	'.wmf': 'image/x-wmf',
 	'.emf': 'image/x-emf'
	}


descriptions = {
	'application/smil': 'SMIL presentations',
	'application/smil+xml': 'SMIL presentations',
	'application/x-grins-cmif': 'CMIF presentations',
	'application/x-grins-project': 'GRiNS Project files',
	'application/x-grins-binary-project': 'GRiNS Binary Project files',
	'image/vnd.rn-realpix': 'RealPix files',
	'text/x-grins-skin': 'GRiNS Skin Description files',
}
