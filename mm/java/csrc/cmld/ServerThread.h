#ifndef INC_SERVERTHREAD
#define INC_SERVERTHREAD

#ifndef INC_SOCKAPI
#include "sockserver/sockapi.h"
#endif

#ifndef INC_SOCKETSERVER
#include "sockserver/SocketServer.h"
#endif

#ifndef INC_DBUF
#include "lib/dbuf.h"
#endif

#ifndef INC_THREAD
#include "lib/Thread.h"
#endif

// for PyObject
#ifndef Py_PYTHON_H
#include "Python.h"
#endif

class ServerThread : public Thread
	{
	public:
	ServerThread(int port)
	:	m_port(port), m_pListener(NULL) {}
	~ServerThread();

	void SetCmdListener(PyObject *pListener);
	virtual UINT Run();

	private:
	int m_port;
	PyObject *m_pListener;
	};

inline ServerThread::~ServerThread()
	{
	Py_XDECREF(m_pListener);
	}

inline void ServerThread::SetCmdListener(PyObject *pListener){
	Py_XDECREF(m_pListener);
	m_pListener=pListener;
	Py_XINCREF(m_pListener);
	}


inline UINT ServerThread::Run()
	{
	if(!sockapi::startup())
		return 1;

	SocketServer *pServer = new SocketServer(u_short(m_port), (void*)m_pListener);
	
	if(!pServer->start())
		{
		delete pServer;
		return 1;
		}

	while(!m_bStopFlag)
		{
		pServer->execute();
		::WaitForSingleObject(m_hStopEv,50);
		}
	
	pServer->stop();
	delete pServer;

	sockapi::cleanup();
	
	return 0;
	}

#endif
