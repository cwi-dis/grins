#ifndef INC_COMMOD
#define INC_COMMOD

#ifndef INC_COMOBJ
#include "comobj.h"
#endif

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

class GRiNSPlayerComModule
	{
	public:	
	GRiNSPlayerComModule(DWORD dwThreadID=0) 
	:	m_dwThreadID(dwThreadID), 
		m_hListenerWnd(0),
		m_pIFactory(NULL),
		m_dwRegID(0),
		m_pyobj(NULL)
		{
		}
	~GRiNSPlayerComModule()
		{
		if(m_dwRegID) CoRevokeClassObject(m_dwRegID);
		if(m_pIFactory) m_pIFactory->Release();
		if(m_dwRegIDMon) CoRevokeClassObject(m_dwRegIDMon);
		if(m_pIFactoryMon) m_pIFactoryMon->Release();
		Py_XINCREF(m_pyobj);
		}

	void lock() {CoAddRefServerProcess();}
	void unlock()
		{
		if(CoReleaseServerProcess()==0)
			PostThreadMessage(m_dwThreadID,WM_QUIT,0,0);
		}

	HRESULT registerClassObjects() 
		{
		HRESULT hr = GetGRiNSPlayerAutoClassObject(&m_pIFactory, this);
		if (SUCCEEDED(hr))
			hr = CoRegisterGRiNSPlayerAutoClassObject(m_pIFactory, &m_dwRegID);
		
		if (SUCCEEDED(hr))
			hr = GetGRiNSPlayerMonikerClassObject(&m_pIFactoryMon, this);
		if (SUCCEEDED(hr))
			hr = CoRegisterGRiNSPlayerMonikerClassObject(m_pIFactoryMon, &m_dwRegIDMon);
		return hr;
		}
		
	void setListenerThreadID(DWORD dwThreadID) {m_dwThreadID = dwThreadID;}
	DWORD getListenerThreadID() const { return m_dwThreadID;}
	
	void setListenerHwnd(HWND hwnd) {m_hListenerWnd=hwnd;}
	HWND getListenerHwnd() const {return m_hListenerWnd;}
	
	void setPyListener(PyObject *obj) {m_pyobj=obj;Py_XINCREF(m_pyobj);}
	PyObject *getPyListener() {return m_pyobj;}

	void adviceNewPeerWnd(int docid, int wndid, int w, int h, const char *title)
		{GRiNSPlayerAutoAdviceNewPeerWnd(docid, wndid, w, h, title);}
	void adviceClosePeerWnd(int docid, int wndid)
		{GRiNSPlayerAutoAdviceClosePeerWnd(docid, wndid);}
	void adviceSetCursor(int id, char *cursor){GRiNSPlayerAutoAdviceSetCursor(id, cursor);}
	void adviceSetDur(int id, double dur){GRiNSPlayerAutoAdviceSetDur(id, dur);}
	void adviceSetFrameRate(int id, int fr){GRiNSPlayerAutoAdviceSetFrameRate(id, fr);}

	private:
	IClassFactory *m_pIFactory;
	DWORD m_dwRegID;	
	
	IClassFactory *m_pIFactoryMon;
	DWORD m_dwRegIDMon;	
	
	DWORD m_dwThreadID;
	HWND m_hListenerWnd;
	PyObject *m_pyobj;
	};

#endif

