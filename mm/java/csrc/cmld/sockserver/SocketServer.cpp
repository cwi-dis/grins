#include "stdafx.h"

#include "SocketServer.h"

#include "Connection.h"

SocketServer::SocketServer(u_short port)
:	m_connStatusChanged(false), m_port(port)
	{
	}

SocketServer::~SocketServer()
	{
	}

bool SocketServer::start()
	{
	m_listeningSocket = newListeningSocket(NULL,m_port);
	if(m_listeningSocket == INVALID_SOCKET)
		{
		cout << "Failed to create listening socket" << endl;
		WSACleanup();
		return false;
		}
	return true;
	}

void SocketServer::execute()
	{
	serveListeningSocket();
	serveConnections();
	serveListeningSocket();
	processConnections();
	printStatistics();
	}

void SocketServer::squit()
	{
	for(map<SOCKET, Connection*>::iterator it=m_connections.begin();it!=m_connections.end();it++)
		(*it).second->squit();
	serveConnections();
	}
	
bool SocketServer::stop()
	{
	// ready to stop
	for(map<SOCKET, Connection*>::iterator it=m_connections.begin();it!=m_connections.end();it++)
		delete (*it).second;
	
	int err = closesocket(m_listeningSocket);
	if(err!=0)
		{
		fprintf(stderr,"closesocket() failed with error %d\n",WSAGetLastError());
		return false;
		}	
	return true;
	}

void SocketServer::serveListeningSocket()
	{
	SOCKET& s = m_listeningSocket;
	fd_set readfds;
	FD_ZERO(&readfds);
	FD_SET(s, &readfds);
	TIMEVAL timout = {0, 1000};
	int n = select(FD_SETSIZE, &readfds, NULL, NULL, &timout);
	if(n!=0 && n!=SOCKET_ERROR && FD_ISSET(s, &readfds))
		{
		Sleep(10);
		SOCKET conn = accept(s, NULL, NULL);
		setNonBlocking(conn);
		Connection *p = new Connection(conn, this);
		if(m_connections.size()<MAX_CLIENTS-1)
			{
			m_connections[conn] = p;
			p->onConnect();
			m_connStatusChanged = true;
			}
		else
			{
			p->onRefuse();
			p->sendAllWaitingPackets();
			delete p;
			}
		}
	}

void SocketServer::serveConnections()
	{
	map<SOCKET, Connection*>& ms = m_connections;
	
	if(ms.size()==0) return;
	
	fd_set readfds, writefds, exceptfds;
	FD_ZERO(&readfds);
	FD_ZERO(&writefds);
	FD_ZERO(&exceptfds);
	TIMEVAL timeout = {0, 1000};
	int nfds = 0;

	list<SOCKET> idlesocks;
	for(map<SOCKET, Connection*>::iterator it=ms.begin();it!=ms.end();it++)
		{
		if((*it).second->isIdle())
			{
			idlesocks.push_back((*it).first);
			}
		else 
			{
			SOCKET s = (*it).first;
			FD_SET(s, &readfds);
			FD_SET(s, &writefds);
			FD_SET(s, &exceptfds);
			nfds++;
			}
		}
	
	if(idlesocks.size()>0) m_connStatusChanged = true;
	for(list<SOCKET>::iterator ii=idlesocks.begin();ii!=idlesocks.end();ii++)
		{
		map<SOCKET, Connection*>::iterator it=m_connections.find(*ii);
		if(it!=m_connections.end())
			{
			Connection *p = (*it).second;
			m_connections.erase(it);
			p->onIdleTimeout();
			p->sendAllWaitingPackets();
			delete p;
			}
		}
	
	if(nfds==0) return; // None to do
	
	int n = select(FD_SETSIZE, &readfds, &writefds, &exceptfds, &timeout);
	if(n==SOCKET_ERROR)
		{
		int err = WSAGetLastError();
		if(err==WSAEINPROGRESS)
			cout << "WSAEINPROGRESS" << endl;
		else
			cout << "serveConnections failed" << endl;
		return;
		}
	else if(n==0){
		cout << "select timeout" << endl;
		return;
		}
	
	Sleep(10);

	for(u_short i=0;i<readfds.fd_count;i++)
		{
		Connection *p = m_connections[readfds.fd_array[i]];
		if(p->readPacket()==SOCKET_ERROR)
			{
			SOCKET s = readfds.fd_array[i];
			map<SOCKET, Connection*>::iterator it=m_connections.find(s);
			if(it!=m_connections.end())
				{
				Connection *p = (*it).second;
				m_connections.erase(it);
				delete p;
				}
			FD_CLR(s, &writefds);
			FD_CLR(s, &exceptfds);
			m_connStatusChanged = true;
			}
		}
	
	for(i=0;i<writefds.fd_count;i++)
		{
		Connection *p = m_connections[writefds.fd_array[i]];
		p->unblock();
		if(p->sendPacket()==SOCKET_ERROR)
			{
			SOCKET s = writefds.fd_array[i];
			map<SOCKET, Connection*>::iterator it=m_connections.find(s);
			if(it!=m_connections.end())
				{
				Connection *p = (*it).second;
				m_connections.erase(it);
				delete p;
				}
			FD_CLR(s, &exceptfds);
			m_connStatusChanged = true;
			}
		}

	// If processing a connect call (nonblocking), connection attempt failed. 
	// OR OOB data is available for reading (only if SO_OOBINLINE is disabled). 
	// for(i=0;i<exceptfds.fd_count;i++){}
	}

void SocketServer::processConnections()
	{
	map<SOCKET, Connection*>& ms = m_connections;	
	if(ms.size()==0) return;
	for(map<SOCKET, Connection*>::iterator it=ms.begin();it!=ms.end();it++)
		(*it).second->processRecvCommands();
	}

void SocketServer::printStatistics()
	{
	if(m_connStatusChanged)
		cout << m_connections.size() << " connections" << endl;
	m_connStatusChanged = false;
	}

int	SocketServer::newListeningSocket(LPCTSTR server, u_short port)
	{
	sockaddr_in local;
	ZeroMemory(&local,sizeof(local));	
	local.sin_family = AF_INET;
	if(!server)
		local.sin_addr.s_addr = INADDR_ANY; // inet_addr("127.1.1.1"); 
	else
		local.sin_addr.s_addr = inet_addr(server);
	local.sin_port = htons(port);
	SOCKET s = socket(AF_INET,SOCK_STREAM,0); // request a TCP socket
	if(s == INVALID_SOCKET) 
		{
		fprintf(stderr,"socket() failed with error %d\n",WSAGetLastError());
		return INVALID_SOCKET;
		}
	if (bind(s,(struct sockaddr*)&local,sizeof(local)) == SOCKET_ERROR) 
		{
		fprintf(stderr,"bind() failed with error %d\n",WSAGetLastError());
		closesocket(s);
		return INVALID_SOCKET;
		}
	if(listen(s,SOMAXCONN) == SOCKET_ERROR) 
		{
		fprintf(stderr,"listen() failed with error %d\n",WSAGetLastError());
		closesocket(s);
		return INVALID_SOCKET;
		}
	return s;
	}

void SocketServer::setNonBlocking(SOCKET s)
	{
	u_long arg=1;
	if(ioctlsocket(s, FIONBIO, &arg)==SOCKET_ERROR)
		{
		cout << "ioctlsocket failed: " << WSAGetLastError() << endl;
		}
	}

void SocketServer::onSocketProcessing()
	{
	serveListeningSocket();
	
	map<SOCKET, Connection*>& ms = m_connections;
	
	if(ms.size()==0) return;
	
	fd_set readfds, writefds, exceptfds;
	FD_ZERO(&readfds);
	FD_ZERO(&writefds);
	FD_ZERO(&exceptfds);
	TIMEVAL timeout = {0, 1000};
	int nfds = 0;

	for(map<SOCKET, Connection*>::iterator it=ms.begin();it!=ms.end();it++)
		{
		SOCKET s = (*it).first;
		FD_SET(s, &readfds);
		FD_SET(s, &writefds);
		FD_SET(s, &exceptfds);
		nfds++;
		}
	int n = select(FD_SETSIZE, &readfds, &writefds, &exceptfds, &timeout);
	if(n==SOCKET_ERROR)
		{
		int err = WSAGetLastError();
		if(err==WSAEINPROGRESS)
			cout << "WSAEINPROGRESS" << endl;
		else
			cout << "serveConnections failed" << endl;
		return;
		}
	else if(n==0){
		cout << "select timeout" << endl;
		return;
		}
	
	Sleep(10);

	for(u_short i=0;i<readfds.fd_count;i++)
		{
		Connection *p = m_connections[readfds.fd_array[i]];
		if(p->readPacket()==SOCKET_ERROR)
			{
			SOCKET s = readfds.fd_array[i];
			map<SOCKET, Connection*>::iterator it=m_connections.find(s);
			if(it!=m_connections.end())
				{
				Connection *p = (*it).second;
				p->setDead();
				}
			FD_CLR(s, &writefds);
			FD_CLR(s, &exceptfds);
			}
		}
	
	for(i=0;i<writefds.fd_count;i++)
		{
		Connection *p = m_connections[writefds.fd_array[i]];
		p->unblock();
		if(p->sendPacket()==SOCKET_ERROR)
			{
			SOCKET s = writefds.fd_array[i];
			map<SOCKET, Connection*>::iterator it=m_connections.find(s);
			if(it!=m_connections.end())
				{
				Connection *p = (*it).second;
				p->setDead();
				}
			FD_CLR(s, &exceptfds);
			}
		}
	}
