#ifndef INC_SOCKETSERVER
#define INC_SOCKETSERVER

class Connection;

class SocketServer
	{
	public:
	SocketServer(u_short port, void *pContext=NULL);
	~SocketServer();

	bool start();
	void execute();
	void squit();
	bool stop();

	void onSocketProcessing();

	void setContext(void *pContext){m_pContext=pContext;}
	void *getContext(){return m_pContext;}
	
	private:
	u_short m_port;
	void *m_pContext;
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

