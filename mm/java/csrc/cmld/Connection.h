#ifndef INC_CONNECTION
#define INC_CONNECTION

#ifndef INC_DBUF
#include "lib/dbuf.h"
#endif

class SocketServer;
class XMLParser;
class Element;

#define	FLAGS_BLOCKED		0x00000001
#define	FLAGS_DEADSOCKET    0x00000002

// for PyObject
#ifndef Py_PYTHON_H
#include "Python.h"
#endif

class Connection 
	{
	public:
	Connection(SOCKET sock, SocketServer *pss);
	~Connection();

	void putSendQueue(const char *psz){putSendQueue(psz,strlen(psz));}	
	void putSendQueue(const string& s){putSendQueue(s.c_str(),s.length());}
	void putSendQueue(const char *p, int len){sendQ.put(p,len);}
	
	int sendAllWaitingPackets();
	int sendPacket();
	void processRecvCommands();

	int deliverPacket(char *str, int len);
	int	readPacket();

	// called on server quit
	void squit(){};

	// called by the server when a connection has been established
	void onConnect(){}

	// called by the server when a connection can not be established
	void onRefuse(){}

	// called by the server before disconnecting as idle
	void onIdleTimeout(){}
	
	// return true when its idle and should be removed
	const bool isIdle(){ return false;}

	// block and unbolck socket
	void block(){flags |= FLAGS_BLOCKED;}
	void unblock(){flags &= ~FLAGS_BLOCKED;}

	void setDead() {flags |= FLAGS_DEADSOCKET;}
	bool dead() const {return (flags & FLAGS_DEADSOCKET)!=0;}
	bool alive() const {return !dead();}
	
	private:
	// socket descriptor of this connection
	SOCKET sock;

	
	// socket server
	SocketServer *pSocketServer;
	
	// send and receive buffers
	dbuf sendQ;
	dbuf recvQ;

	// recv stream xml parser
	XMLParser *pXMLParser;
	
	// status flags
	unsigned long flags;

	// statistics
	int sendB, recvB;

	// cmd receiver
	PyObject *pListener;

	// cmd handlers
	typedef void (Connection::*CMD_HANDLER)(Element *pe);
	map<string, CMD_HANDLER> cmdHandlers;
	void addCmdHandler(const char *psz, CMD_HANDLER ch){cmdHandlers[psz] = ch;} 

	// dtd commands
	void executeOpenCmd(Element *pe);
	void executeCloseCmd(Element *pe);
	void executePlayCmd(Element *pe);
	void executeStopCmd(Element *pe);
	void executePauseCmd(Element *pe);
	void executeOnClickCmd(Element *pe);

	enum {READ_SIZE=8192};
	static char s_readbuf[READ_SIZE];	
	};


#endif

