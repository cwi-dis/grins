__version__ = "$Id$"

# This file will contain the base objects for the various views.
# There is meant to be one and only one instance of this class;
# All editing classes should be able to share one instance of this class.

# These classes are related to the MMNode hierarchy by association only;
# ideally it would use inheritance but that would interfere too much
# with the rest of the system.

# This module has NOTHING TO DO WITH DRAWING OR INTERACTING with nodes;
# the drawing, clicking and so forth is done in higher-level objects.

# These classes could also form a layer of abstraction with the edit
# manager - the only place the routines in the edit manager need to
# be called from is here.

import MMNode, MMExc, MMTypes
import windowinterface
import features
from usercmd import *

######################################################################
# Editing MMNodes.

class EditableMMNode(MMNode.MMNode):
	# Editable version of an MMNode.
	def __init__(self, type, context, uid):
		MMNode.MMNode.__init__(self, type, context, uid)
		self.showtime = 0

	def GetName(self):
		# I'm used by the event editor dialog.
		# print "DEBUG: GetName"
		try:
			return self.GetAttr('name')
		except MMExc.NoSuchAttrError:
			return 'nameless %s' % self.GetType()
	#def GetType(self) - defined in MMNode.py
	
	def NewBeginEvent(self, othernode, event, editmgr = None):
		# I'm called only from the HierarchyView
		self.__new_beginorend_event('begin', 'beginlist', othernode, event, editmgr)

	def NewEndEvent(self, othernode, event, editmgr = None):
		# I'm called only from the HierarchyView
		self.__new_beginorend_event('end', 'endlist', othernode, event, editmgr)

	def __new_beginorend_event(self, type, attrib, othernode, event, editmgr):
		# Only called from the two methods above; reuse similar code.
		if not editmgr:
			em = self.context.editmgr
			if not em.transaction():
				return
		else:
			em = editmgr
		e = MMNode.MMSyncArc(self, type, srcnode=othernode, event=event, delay=0)
		em.addsyncarc(self, attrib, e)
		if not editmgr:
			em.commit()

	def GetCollapsedParent(self):
		# return the top-most collapsed ancestor, or None if all ancestors are uncollapsed
		# I'm used by the event editor.
		#print "DEBUG: GetCollapsedParent"
		i = self.parent		# Don't return self if I'm collapsed.
		rv = None		# default return value
		while i is not None:
			if i.collapsed == 1:
				rv = i
			i = i.parent
		return rv

	__basictiming = ['beginlist',
			 'duration',
			 'endlist',
			 'loop',
			 'max',
			 'min',
			 'repeatdur']
	__timing = __basictiming + [
		    'fill',
		    'fillDefault',
		    'restart',
		    'restartDefault',
		    'syncBehavior',
		    'syncBehaviorDefault',
		    'syncMaster',
		    'syncTolerance',
		    'syncToleranceDefault',
		    ]
	def getallattrnames(self, withspecials = 0):
		import ChannelMap
		ntype = self.GetType()
		if ntype == 'comment':
			# special case for comment nodes
			if withspecials:
				return ['.values']
			return []
		if ntype == 'foreign':
			return self.attrdict.keys()
		namelist = [
			'name', 'title', 'alt', 'longdesc',
			'system_audiodesc', 'system_bitrate',
			'system_captions', 'system_cpu',
			'system_language', 'system_operating_system',
			'system_overdub_or_caption', 'system_required',
			'system_screen_size', 'system_screen_depth',
			'system_component',
			]
		if features.USER_GROUPS in features.feature_set:
			namelist.append('u_group')
		if withspecials and features.EDIT_TYPE in features.feature_set:
			namelist.append('.type')
		if ntype == 'prefetch':
			namelist.extend(self.__timing)
			namelist.extend(['clipbegin',
					 'clipend',
# XXX disabled for now since implementation is missing completely
##					 'bandwidth',
##					 'mediaSize',
##					 'mediaTime',
					 'file'])
			return namelist
		if ntype == 'animate':
			atag = self.attrdict.get('atag','animate')
			namelist.extend(self.__timing)
			namelist.append('atag')
			if atag not in ('transitionFilter', 'animateMotion'):
				namelist.extend(['attributeName',
						 'attributeType'])
			if atag not in ('set', 'transitionFilter'):
				namelist.extend(['accumulate',
						 'additive',
						 'by',
						 'calcMode',
						 'from',
						 'keySplines',
						 'keyTimes',
						 'values'])
			if atag == 'animateMotion':
				namelist.extend(['path',
						 'origin'])
			if atag == 'transitionFilter':
				namelist.extend(['trtype',
						 'subtype',
						 'mode',
						 'fadeColor',
						 'horzRepeat',
						 'vertRepeat',
						 'borderWidth',
						 'borderColor'])
			namelist.extend(['targetElement',
					 'to',
					 'speed',
					 'accelerate',
					 'decelerate',
					 'autoReverse'])
			return namelist
		if ntype in ('par','seq','excl','prio','imm','ext','brush'):
			namelist.extend(['copyright',
					 'abstract',
					 'author'])
		if ntype == 'prio':
			# special case for prio nodes
			namelist.extend(['higher',
					 'peers',
					 'lower',
					 'pauseDisplay'])
			if withspecials and features.EDIT_TYPE in features.feature_set:
				namelist.append('.type')
			return namelist

		if ntype == 'anchor':
			namelist.extend(self.__basictiming)
			namelist.extend(['accesskey',
					 'acoords',
					 'actuate',
					 'ashape',
					 'fragment',
					 'tabindex'])
			if features.EXPORT_REAL in features.feature_set:
				namelist.append('sendTo')
			return namelist

		ctype = self.GetChannelType()
		if ntype in MMTypes.mediatypes:
			namelist.append('channel')
		if ntype != 'switch':
			namelist.extend(self.__timing)
		if withspecials and ntype in MMTypes.interiortypes:
			namelist.extend(['thumbnail_icon',
					 'dropicon',
					 'empty_icon',
					 'empty_text',
					 'empty_color',
					 'empty_duration',
					 'non_empty_icon',
					 'non_empty_text',
					 'non_empty_color',
					 'thumbnail_scale'])
		if withspecials and ntype in ('par', 'seq', 'excl'):
			namelist.extend(['project_default_region_video',
					 'project_default_region_image',
					 'project_default_region_sound',
					 'project_default_region_text',
					 'project_forcechild'])
		if ntype in MMTypes.mediatypes:
			if ntype != 'brush':
				namelist.extend(['file',
						 'mimetype',
						 'allowedmimetypes'])
			namelist.extend(['readIndex',
					 'erase',
					 'transIn',
					 'transOut'])
			if features.EXPORT_REAL in features.feature_set:
				if ChannelMap.isvisiblechannel(ctype):
					namelist.extend(['backgroundOpacity',
							 'chromaKey',
							 'chromaKeyOpacity',
							 'chromaKeyTolerance',
							 'mediaOpacity'])
				namelist.append('reliable')
				if ctype in ('text','image'):
					namelist.append('strbitrate')
			if ctype in ('sound', 'video'):
				namelist.extend(['clipbegin',
						 'clipend'])
			if ChannelMap.isvisiblechannel(ctype):
				namelist.extend(['left',
						 'width',
						 'right',
						 'top',
						 'height',
						 'bottom',
						 'fit',
						 'regPoint',
						 'regAlign',
						 'z',
						 'sensitivity',
						 'cssbgcolor'])
			# specific time preference
			if features.EXPORT_QT in features.feature_set:
				namelist.extend(['immediateinstantiationmedia',
						 'bitratenecessary',
						 'systemmimetypesupported',
						 'attachtimebase',
						 'qtchapter',
						 'qtcompositemode'])
			if features.EXPORT_REAL in features.feature_set:
				mime = self.GetComputedMimeType()
				if mime and mime.find('real') < 0 and mime != 'image/jpeg' and ctype not in ('text', 'html'):
					namelist.append('project_convert')
					if ctype in ('sound', 'video'):
						namelist.extend(['project_audiotype',
								 'project_targets',
								 'project_perfect',
								 'project_mobile'])
					if ctype == 'video':
						namelist.append('project_videotype')
					if ctype == 'image':
						namelist.append('project_quality')
		if ntype == 'brush' or (features.EXPORT_SMIL2 in features.feature_set and ctype == 'text'):
			namelist.append('fgcolor')
		if withspecials and ntype == 'imm':
			namelist.append('.values')
		if ntype in MMTypes.termtypes:
			namelist.append('terminator')
		if self.context.layouts:
			# no sense bothering the user with an attribute that
			# doesn't do anything...
			namelist.append('layout')
		# Get the channel class (should be a subroutine!)
##		if ChannelMap.channelmap.has_key(ctype):
##			cclass = ChannelMap.channelmap[ctype]
##			# Add the class's declaration of attributes
##			for name in cclass.node_attrs:
##				if name not in namelist:
##					namelist.append(name)
##		# Merge in nonstandard attributes
##		extras = []
##		for name in self.GetAttrDict().keys():
##			if name not in namelist and \
##				     MMAttrdefs.getdef(name)[3] <> 'hidden':
##				extras.append(name)
##		extras.sort()
##		namelist = namelist + extras
##		retlist = []
##		for name in namelist:
##			if name in retlist:
##				continue
##			retlist.append(name)
			
####		if not cmifmode():
####			# cssbgcolor is used instead
####			if 'bgcolor' in retlist: retlist.remove('bgcolor')
####			if 'transparent' in retlist: retlist.remove('transparent')
##		return retlist
		return namelist


######################################################################
	# Commands from the menus.
	# Note that the commands should control the EditMgr - they
	# are essentually macro-level commands that use the methods above. -mjvdg.

	def editcall(self):
		windowinterface.setwaiting()
		import NodeEdit
		NodeEdit.showeditor(self)

	#def anchorcall(self):
	#	if self.focusobj: self.focusobj.anchorcall()

	#def createanchorcall(self):
	#	if self.focusobj: self.focusobj.createanchorcall()

	#def hyperlinkcall(self):
	#	if self.focusobj: self.focusobj.hyperlinkcall()
