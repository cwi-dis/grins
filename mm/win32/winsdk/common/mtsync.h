#ifndef INC_MTSYNC
#define INC_MTSYNC

#ifndef _WINDOWS_
#include <windows.h>
#endif

class critical_section
	{
	public:
	critical_section() { InitializeCriticalSection(&m_sec);}
	~critical_section() { DeleteCriticalSection(&m_sec);}

	void enter() { EnterCriticalSection(&m_sec);}
	void leave() { LeaveCriticalSection(&m_sec);}

	CRITICAL_SECTION m_sec;
	};

#endif // INC_MTSYNC
