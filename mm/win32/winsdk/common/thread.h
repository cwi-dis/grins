#ifndef INC_THREAD
#define INC_THREAD

class Thread
	{
	public:
	Thread()
	:	m_hStopEvent(CreateEvent(NULL, TRUE, FALSE, NULL)),
		m_hThread(NULL),
		m_idThread(0),
		m_idParentThread(GetCurrentThreadId())
		{
		}

	virtual ~Thread()
		{
		if(m_hThread != NULL) Stop();
		if(m_hStopEvent) CloseHandle(m_hStopEvent);
		}

	bool Start()
		{
		if(m_hThread != NULL) return false;
		ResetEvent(m_hStopEvent);
		m_hThread = CreateThread(NULL, 0, &Thread::threadproc, this, 0, &m_idThread);
		return m_hThread != NULL;
		}

	void Stop()
		{
		if(m_hThread != NULL)
			{
			SetEvent(m_hStopEvent);
			WaitForSingleObject(m_hThread, INFINITE);
			CloseHandle(m_hThread);
			m_hThread = NULL;
			}
		}
	
	HANDLE GetStopHandle() const { return m_hStopEvent;}

	protected:
	virtual DWORD Run() = 0;

	private:
	static DWORD __stdcall threadproc(LPVOID pParam)
		{
		Thread* p = static_cast<Thread*>(pParam);
		return p->Run();
		}

	HANDLE m_hStopEvent;
	HANDLE m_hThread;
	DWORD m_idThread;
	DWORD m_idParentThread;
	};

#endif // INC_THREAD