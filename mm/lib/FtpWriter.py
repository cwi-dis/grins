"""FtpWriter - Class that looks file-like and writes to ftp server"""
import ftplib
from ftplib import all_errors, error_perm
import string

class FtpWriter:
	def __init__(self,
		     host,
		     file,
		     user='anonymous',
		     passwd='',
		     dir='',
		     ascii=0,
		     debuglevel=0):
		self.ftp = None
		self.ftpdata = None
		self.ftp = ftplib.FTP()
		if debuglevel:
			self.ftp.set_debuglevel(debuglevel)
		self.ftp.connect(host)
		self.ftp.login(user, passwd)
		if dir:
			self.ftp.cwd(dir)
		self.ascii = ascii
		if ascii:
			self.ftp.voidcmd('TYPE A')
		else:
			self.ftp.voidcmd('TYPE I')
		self.ftpdata = self.ftp.transfercmd('STOR '+file)

	def __del__(self):
		self.close()

	def close(self):
		if self.ftpdata:
			self.ftpdata.close()
			self.ftp.voidresp()
			self.ftpdata = None
		if self.ftp:
			self.ftp.quit()
			self.ftp = None

	def write(self, data):
		if self.ascii:
			lines = string.split(data, '\n')
			for line in lines[:-1]:
				self.ftpdata.send(line+'\r\n')
			if lines[-1]:
				self.ftpdata.send(lines[-1])
		else:
			self.ftpdata.send(data)
					
def _test():
	import getopt
	import sys
	try:
		options, args = getopt.getopt(sys.argv[1:], 'u:p:d:a')
		if len(args) != 2:
			raise getopt.error
	except getopt.error:
		print 'Usage: %s [-u user] [-p passwd] [-d dir] [-a] host file < inputfile'%sys.argv[0]
		sys.exit(1)
	host = args[0]
	file = args[1]
	user = ''
	passwd = ''
	dir = ''
	ascii = 0
	for o, a in options:
		if o == '-u':
			user = a
		if o == '-p':
			passwd = a
		if o == '-d':
			dir = a
		if o == '-a':
			ascii = 1
	ofp = FtpWriter(host, file, user=user, passwd=passwd, dir=dir, ascii=ascii, debuglevel=1)
	while 1:
		data = sys.stdin.read()
		if not data:
			break
		ofp.write(data)

if __name__ == '__main__':
	_test()
