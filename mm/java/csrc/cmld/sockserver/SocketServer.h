#ifndef INC_SOCKETSERVER
#define INC_SOCKETSERVER

class Connection;

class SocketServer
	{
	public:
	SocketServer(u_short port);
	~SocketServer();

	bool start();
	void execute();
	void squit();
	bool stop();

	void onSocketProcessing();
	
	private:
	u_short m_port;
	SOCKET m_listeningSocket;
	map<SOCKET, Connection*> m_connections;
	bool m_connStatusChanged;
		
	void serveListeningSocket();
	void serveConnections();
	void processConnections();
	void printStatistics();

	static int newListeningSocket(LPCTSTR server, u_short port);
	static void setNonBlocking(SOCKET s);
	
	enum {MAX_CLIENTS=FD_SETSIZE-4};
	};


#endif

