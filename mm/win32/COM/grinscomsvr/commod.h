#ifndef INC_COMMOD
#define INC_COMMOD

#ifndef INC_COMOBJ
#include "comobj.h"
#endif

class GRiNSPlayerComModule
	{
	public:	
	GRiNSPlayerComModule(DWORD dwThreadID=0) 
	:	m_dwThreadID(dwThreadID), 
		m_hListenerWnd(0),
		m_pIFactory(NULL),
		m_dwRegID(0)
		{
		}
	~GRiNSPlayerComModule()
		{
		if(m_dwRegID) CoRevokeClassObject(m_dwRegID);
		if(m_pIFactory) m_pIFactory->Release();
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
		return hr;
		}
		
	void setListenerThreadID(DWORD dwThreadID) {m_dwThreadID = dwThreadID;}
	DWORD getListenerThreadID() const { return m_dwThreadID;}
	
	void setListenerHwnd(HWND hwnd) {m_hListenerWnd=hwnd;}
	HWND getListenerHwnd() const {return m_hListenerWnd;}

	void adviceSetSize(int id, int w, int h){GRiNSPlayerAutoAdviceSetSize(id, w, h);}
	void adviceSetCursor(int id, char *cursor){GRiNSPlayerAutoAdviceSetCursor(id, cursor);}
	void adviceSetDur(int id, double dur){GRiNSPlayerAutoAdviceSetDur(id, dur);}
	void adviceSetPos(int id, double pos){GRiNSPlayerAutoAdviceSetDur(id, pos);}
	void adviceSetSpeed(int id, double speed){GRiNSPlayerAutoAdviceSetSpeed(id, speed);}
	void adviceSetState(int id, int st){GRiNSPlayerAutoAdviceSetState(id, st);}
	
	private:
	IClassFactory *m_pIFactory;
	DWORD m_dwRegID;		
	DWORD m_dwThreadID;
	HWND m_hListenerWnd;
	};

#endif

