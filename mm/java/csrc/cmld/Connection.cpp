#include "stdafx.h"

#include "Connection.h"

#include "XMLParser.h"

#include "sockserver/SocketServer.h"

#include "mtpycall.h"

#include "lib/StrRec.h"

char Connection::s_readbuf[8192];

Connection::Connection(SOCKET s, SocketServer *pss)
:	sock(s), 
	flags(0),
	sendB(0),
	recvB(0),
	pXMLParser(NULL),
	pSocketServer(pss),
	pListener((PyObject*)pss->getContext())
	{
	pXMLParser = new XMLParser("cml");
	pXMLParser->beginParsing();	
	addCmdHandler("open", &Connection::executeOpenCmd);	
	addCmdHandler("close", &Connection::executeCloseCmd);	
	addCmdHandler("play", &Connection::executePlayCmd);	
	addCmdHandler("stop", &Connection::executeStopCmd);	
	addCmdHandler("pause", &Connection::executePauseCmd);	
	addCmdHandler("onClick", &Connection::executeOnClickCmd);	
	}

Connection::~Connection() 
	{
	delete pXMLParser;	
	closesocket(sock);
	}

int Connection::sendAllWaitingPackets()
	{
	while(true)
		{
		int len = sendQ.get(s_readbuf,READ_SIZE);
		if(len==0) break;
		int ret=deliverPacket(s_readbuf, len);
		if(ret==SOCKET_ERROR)
			return SOCKET_ERROR;
		else if(ret==0)
			return 0;
		}
	return 1;
	}

int Connection::sendPacket()
	{
	int len = sendQ.get(s_readbuf,READ_SIZE);
	if(len==0) return 1;
	int ret=deliverPacket(s_readbuf, len);
	if(ret==SOCKET_ERROR)
		return SOCKET_ERROR;
	else if(ret==0)
		return 0;
	return 1;
	}

int Connection::deliverPacket(char *str, int len)
	{
	WSASetLastError(0);
	int retval = ::send(sock, str, len, 0);
	if(retval==SOCKET_ERROR)
		{
		int err = WSAGetLastError();
		if(err==WSAEWOULDBLOCK || err==WSAENOBUFS)
			{
			block();
			return 0;
			}
		return SOCKET_ERROR;
		}
	sendB += retval;
	unblock();
	return retval;
	}

int	Connection::readPacket()
	{
	WSASetLastError(0);
	int	length = ::recv(sock, s_readbuf, READ_SIZE, 0);
	if(length>0)
		{
		recvB+=length;
		recvQ.put(s_readbuf,length);
		return length;
		}
	else if(length==0)
		{
		//cout << "USER_RESET" << endl;
		return SOCKET_ERROR; // close socket
		}

	// length == SOCKET_ERROR
	int err = WSAGetLastError();
	if(err==WSAEWOULDBLOCK)
		return 0; // success

	/*
	if(err==WSAESHUTDOWN)
		cout << "WSAESHUTDOWN" << endl;
	else if(err==WSAECONNRESET)
		cout << "WSAECONNRESET" << endl;
	*/
	
	return SOCKET_ERROR; // close socket
	}

void Connection::processRecvCommands()
	{
	// parse commands
	while(true)
		{
		int len = recvQ.get(s_readbuf,READ_SIZE);
		if(len==0) break;
		pXMLParser->parse(s_readbuf, len);
		}	

	list<Element*>& cmds = pXMLParser->getCommands();

	// execute cmds
	while(cmds.size()>0)
		{
		Element *cmd = cmds.front();
		map<string, CMD_HANDLER>::iterator it = cmdHandlers.find(cmd->getName());
		if(it!=cmdHandlers.end())
			{
			(this->*(*it).second)(cmd);
			}
		delete cmd;
		cmds.erase(cmds.begin());
		}
	}


// <open src="" />
void Connection::executeOpenCmd(Element *pe)
	{
	if(pListener==NULL) return;
	
	string src = pe->getAttribute("src");
	if(src.length()==0) return;
	
	CallbackHelper helper("Open",pListener);
	if(helper.cancall())
		{
		PyObject *arg = Py_BuildValue("(s)", src.c_str());
		helper.call(arg);
		}
	}

// <close/>
void Connection::executeCloseCmd(Element *pe)
	{
	if(pListener==NULL) return;
	CallbackHelper helper("Close",pListener);
	if(helper.cancall())
		{
		PyObject *arg = Py_BuildValue("()");
		helper.call(arg);
		}
	}


// <play/>
void Connection::executePlayCmd(Element *pe)
	{
	if(pListener==NULL) return;
	CallbackHelper helper("Play",pListener);
	if(helper.cancall())
		{
		PyObject *arg = Py_BuildValue("()");
		helper.call(arg);
		}
	}

// <stop/>
void Connection::executeStopCmd(Element *pe)
	{
	if(pListener==NULL) return;
	CallbackHelper helper("Stop",pListener);
	if(helper.cancall())
		{
		PyObject *arg = Py_BuildValue("()");
		helper.call(arg);
		}
	}

// <pause/>
void Connection::executePauseCmd(Element *pe)
	{
	if(pListener==NULL) return;
	CallbackHelper helper("Pause",pListener);
	if(helper.cancall())
		{
		PyObject *arg = Py_BuildValue("()");
		helper.call(arg);
		}
	}

// <onClick position="10,10"/>
void Connection::executeOnClickCmd(Element *pe)
	{
	string pos = pe->getAttribute("position");
	if(pos.length()==0) return;
	StrRec sr(pos.c_str(),",");
	if(sr.size()!=2) return;
	CallbackHelper helper("OnClick",pListener);
	if(helper.cancall())
		{
		PyObject *arg = Py_BuildValue("(ii)", atoi(sr[0]),atoi(sr[1]));
		helper.call(arg);
		}
	
	}

