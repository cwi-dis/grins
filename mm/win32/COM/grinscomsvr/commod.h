#ifndef INC_COMMOD
#define INC_COMMOD

class GRiNSPlayerComModule
	{
	public:
	GRiNSPlayerComModule(DWORD dwThreadID=0) 
	:	m_dwThreadID(dwThreadID), 
		m_hListenerWnd(0) 
		{
		}
	void lock() {CoAddRefServerProcess();}
	void unlock()
		{
		if(CoReleaseServerProcess()==0)
			PostThreadMessage(m_dwThreadID,WM_QUIT,0,0);
		}
	void setListenerThreadID(DWORD dwThreadID) {m_dwThreadID = dwThreadID;}
	DWORD getListenerThreadID() const { return m_dwThreadID;}
	
	void setListenerHwnd(HWND hwnd) {m_hListenerWnd=hwnd;}
	HWND getListenerHwnd() const {return m_hListenerWnd;}
	
	private:
	DWORD m_dwThreadID;
	HWND m_hListenerWnd;
	};

#endif

