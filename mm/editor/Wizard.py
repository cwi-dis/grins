import os
import windowinterface
import string
from types import *

import MMAttrdefs

from MMNode import alltypes, leaftypes, interiortypes

from WizardDialog import WizardDialog

class Wizard(WizardDialog):

	def __init__(self, toplevel, **options):
		self.toplevel = toplevel 
		self.new_dialog = None
		self.new_dialog2 = None
		self.def_anch_dialog = None
		self.history = []
		self.cur_pos = 0
		self.node_list = []
		self.channel_list = []
		self.type = 'ext'
		try:
			self.list_callback = options['ListCallback']
		except KeyError:
			self.list_callback = None
		self.title = self.maketitle()
		WizardDialog.__init__(self, self.title, toplevel.basename)
		self.show_correct_group()

	def __repr__(self):
		return '<Wizard instance>'

	
	def maketitle(self):
		return 'Document Wizard'

	
	def updateform(self):
		self.setname(self.name)

		self.settypes(alltypes, alltypes.index(self.type))

		try:
			i = self.allchannelnames.index(self.channelname)
		except ValueError:
			i = 0		# 'undefined'
		self.setchannelnames(self.allchannelnames, i)

		self.settext(self.immtext)

		print 'READY TO SET FILENAME:', self.filename
		self.setfilename(self.filename)

		self.setchildren(self.children, 0)

		self.show_correct_group()
	
	def show_correct_group(self):
		self.show_group()

	def close(self):
		if self.new_dialog != None:
			self.new_dialog.close()
		if self.new_dialog2 != None:
			self.new_dialog2.close()
		if self.def_anch_dialog != None:
			self.def_anch_dialog.close()
		WizardDialog.close(self)
		del self.new_dialog
		del self.new_dialog2
		del self.def_anch_dialog
		del self.toplevel
		del self.history
		del self.node_list
		del self.channel_list
	
	
	def cancel_callback(self):
		self.close()

	def new_callback(self):
		if self.new_dialog == None:
			import WindowInfoDialog
			from ChannelMap import commonchanneltypes, otherchanneltypes
			ls = []
			for name in commonchanneltypes + otherchanneltypes:
				ls.append(name)
			self.new_dialog = WindowInfoDialog.WindowInfoDialog('Window information', ls, FileCallback = self.setwindow)
		else:
			self.new_dialog.show()


	def new_callback2(self):
		if self.new_dialog2 == None:
			import LevelInfoDialog
			ls = ['paralel','sequencal','bag']
			self.new_dialog2 = LevelInfoDialog.LevelInfoDialog('Level information', ls, TypeCallback = self.setwindowlevel)
			lev = self.level_num + 1
			self.new_dialog2.setlevel(`lev`)
		else:
			lev = self.level_num + 1
			self.new_dialog2.setlevel(`lev`)
			self.new_dialog2.show()

	def def_nodes(self, slist, nlist):
		tmp = slist
		for item in nlist:
			if item[4]:
				if type(item[0]) is IntType:
					s = item[1]
				elif type(item[0]) is TupleType:
					s = item[1]+'.'+item[0][0]
									
				if s in tmp:
					num = 1
					s = s+'.'
					while s+`num` in tmp:
						num = num + 1
					s = s + `num`
				tmp.append(s)
			if type(item[3]) is ListType:
				self.def_nodes(tmp,item[3])
		return tmp

	
	def def_anch_callback(self):
		if self.def_anch_dialog == None:
			import WizardAnchorDialog
			ls = self.def_nodes([],self.node_list)
			if ls == []:
				ls = ['None']
			self.def_anch_dialog = WizardAnchorDialog.WizardAnchorDialog('Anchor Definitions', ls, DefCallback = self.setanchors)
			#lev = self.level_num + 1
			#self.new_dialog2.setlevel(`lev`)
		else:
			#lev = self.level_num + 1
			#self.new_dialog2.setlevel(`lev`)
			self.def_anch_dialog.show()

	
	def get_node_list(self, filelist):
		templist = filelist
		tmp = {}
		int_tmp = {}
		levels = {}
		key  = 1

		for item in templist:
			found = 0
			for x in int_tmp.keys():
				if int_tmp[x]==(item[0],item[3]):
					found = 1
					break
			if not found:
				int_tmp[key]=(item[0],item[3])
				key = key +1
		
		for x in int_tmp.keys():
			tmp[x] = []
		
		for item in templist:
			ind = 0
			for x in int_tmp.keys():
				if int_tmp[x]==(item[0],item[3]):
					ind = x
					break
			
			tmp_l = tmp[ind]
			tmp_l.append(item)
			tmp[ind] = tmp_l
			
		templist = []
		node_cr = 1
		for it in int_tmp.keys():
			tmp_l = tmp[it]
			if len(tmp_l)>1:
				templist.append((tmp_l[0][0],'Created Node '+`node_cr`,'seq',tmp_l,1))
				node_cr = node_cr + 1
			else:
				templist.append(tmp_l[0])
		
		level_dict = {}
		for i in templist:
			if not level_dict.has_key(string.atoi(i[0][0])):
				level_dict[string.atoi(i[0][0])] = []
				levels[string.atoi(i[0][0])] = i[0][1]
		tmp_l = []
		for it in templist:
			tmp_l = level_dict[string.atoi(it[0][0])]
			tmp_l.append(it)
			level_dict[string.atoi(it[0][0])] = tmp_l
		templist = []
		for i in level_dict.keys():
			type = levels[i]
			templist.append(i,'Level '+`i`,type,level_dict[i],1)
		return templist
	
	
	def next_callback(self):
		if self.new_dialog != None:
			self.new_dialog.cancel_callback()
		win = self.getwindow() 
		if self.cur_dialog == 1:
			file = self.getfilename()
			if not file:
				windowinterface.showmessage("You must give a destination filename.", mtype = 'error')
				return
		else:
			file = self.getfilename2() 
		type = self.gettype()
		level = self.getwindowlevel() 
		if self.cur_dialog>1:
			if not win or win == ('None','None'):
				windowinterface.showmessage("You must give a window", mtype = 'error')
				return
			if type == 'ext' and not file:
				windowinterface.showmessage("You must give a filename because type is external", mtype = 'error')
				return
			if level[0] == 'None':
				windowinterface.showmessage("You must create a at list one level.", mtype = 'error')
				return
		name = self.getname()
		t = (win,file,type,level,name)
		if self.cur_pos == len(self.history):
			self.history.append((self.cur_dialog,t))
		else:
			self.history[self.cur_pos] = (self.cur_dialog,t)
		self.cur_pos = self.cur_pos + 1
		if self.cur_pos != len(self.history):
			t = self.history[self.cur_pos][1]
			self.setfilename2(t[1])
			self.setwindow(t[0])
			self.settype(t[2])
			self.setwindowlevel(t[3])
			self.setname(t[4])
		else:
			self.setwindow(win)
			self.setfilename2('')
			#self.settype('ext')
			self.setwindowlevel()
			self.setname('')
		if self.cur_dialog<len(self.dialogs_list)-2:
			self.cur_dialog = self.cur_dialog + 1
			self.show_group()
		


	def back_callback(self):
		title = self.buttons._buttons[2].GetWindowText()
		if title == 'Ok':
			self.buttons._buttons[2].SetWindowText('Finish')
		if self.new_dialog != None:
			self.new_dialog.cancel_callback()
		win = self.getwindow() 
		file = self.getfilename2() 
		type = self.gettype()
		level = self.getwindowlevel()
		name = self.getname() 
		t = (win,file,type,level,name)
		if self.cur_dialog>1 and self.cur_pos < len(self.history):
			if not win:
				windowinterface.showmessage("You must give a window", mtype = 'error')
				return
			if type == 'ext' and not file:
				windowinterface.showmessage("You must give a filename because type is external", mtype = 'error')
				return
			if level[0] == 'None':
				windowinterface.showmessage("You must create a at list one level.", mtype = 'error')
				return
		if (file or type == 'imm') and win[0] and self.cur_pos == len(self.history):
			self.history.append((self.cur_dialog,t))
		elif self.cur_pos < len(self.history):
			self.history[self.cur_pos] = (self.cur_dialog,t)
		if self.cur_pos != 1:
			self.cur_pos = self.cur_pos - 1
		if self.cur_dialog != self.history[self.cur_pos][0]:
			self.cur_dialog = self.history[self.cur_pos][0]
			self.show_group()
		t = self.history[self.cur_pos][1]
		self.setfilename2(t[1])
		self.setwindow(t[0])
		self.settype(t[2])
		if t[3][0] == 'None':
			self.setwindowlevel()
		else:
			self.setwindowlevel(t[3])
		self.setname(t[4])
		
	
	def dir_callback(self):
		directory = self.getdirname()
		if directory <> self.directory:
			self.directory = directory

	def file_callback(self):
		filename = self.getfilename()
		if filename <> self.filename:
			self.filename = filename


	def file_callback2(self):
		filename = self.getfilename()
		if filename <> self.filename:
			self.filename = filename

	def name_callback(self):
		name = self.getname()
		if name <> self.name:
			self.name = name
	
	
	def ok_callback(self):
		
		## Called just in case the filename has changed
		## So the filename is re-retrieved anyway
		## MUADDIB
		self.file_callback()


		self.new = 0
		ok = 1
		if self.changed or self.ch_name() or self.ch_immtext():
			ok = self.setvalues()
		if ok:
			self.close()

	def browser_callback(self):
		dir = self.directory
		file = string.split(self.filename,'\\')[-1]
		windowinterface.FileDialog('Select file', dir, '*', file,
					   self.browserfile_callback, None, 1)
	
	def browser_callback2(self):
		dir = self.directory
		file = ' '
		windowinterface.FileDialog('Select file', dir, '*', file,
					   self.browserfile_callback2, None, 1)
		

	def browserfile_callback(self, pathname):
		self.filename = pathname
		ls = string.split(self.filename,'\\')
		del ls[-1]
		self.directory = string.joinfields(ls,'\\') 
		self.setfilename(pathname)

	def browserfile_callback2(self, pathname):
		self.setfilename2(pathname)

	def finish_callback(self):
		title = self.buttons._buttons[2].GetWindowText()
		if title == 'Finish':
			win = self.getwindow() 
			file = self.getfilename2() 
			type = self.gettype()
			level = self.getwindowlevel()
			name = self.getname() 
			t = (win,file,type,level,name)
			if self.cur_dialog>1 and self.cur_pos < len(self.history):
				if not win:
					windowinterface.showmessage("You must give a window", mtype = 'error')
					return
				if type == 'ext' and not file:
					windowinterface.showmessage("You must give a filename because type is external", mtype = 'error')
					return
				if level[0] == 'None':
					windowinterface.showmessage("You must create a at list one level.", mtype = 'error')
					return
			if (file or type == 'imm') and win[0] and self.cur_pos == len(self.history):
				self.history.append((self.cur_dialog,t))
				self.cur_pos = self.cur_pos + 1
				self.setwindow(win)
				self.setfilename2('')
				self.setwindowlevel()
				self.setname('')
			elif self.cur_pos < len(self.history):
				self.history[self.cur_pos] = (self.cur_dialog,t)
			#if self.cur_dialog != self.history[self.cur_pos][0]:
			#	self.cur_dialog = self.history[self.cur_pos][0]
			#	self.show_group()
			self.cur_dialog = len(self.dialogs_list)-1
			self.buttons._buttons[2].SetWindowText('Ok')
			self.show_correct_group()
			nd_list = []
			nd_nd_anc = []
			tmp = self.history[2:]
			for item in tmp:
				item2 = item[1]
				file = string.splitfields(item2[1], '\\')[-1]
				name = item2[4] #string.splitfields(file, '.')[0]
				type = item2[2] + ' ' + item2[1] #file
				level = item2[3]
				win = item2[0][0]
				get_anc = 0
				if item2[0][1] in ['image','movie','mpeg','label']:
					get_anc = 1
				nd_list.append((level,name,type,win,get_anc))
			self.node_list = self.get_node_list(nd_list)
			return
		else:
			if self.ch_names[0][0] == 'None':
					del self.ch_names[0]
			if self.list_callback:
				apply(self.list_callback, (self.ch_names, self.node_list, self.getanchors(),))
			self.cancel_callback()	
	
	def type_callback(self, type):
		self.settype(type)

	def save_callback(self, yesno):
		self.setsave(yesno)