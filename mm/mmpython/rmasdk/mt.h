#ifndef INC_MT
#define INC_MT

#ifdef _WIN32

#ifndef _WINDOWS_
#include <windows.h>
#endif

class SyncObject
	{
	public:
	SyncObject()	{::InitializeCriticalSection(&m_sect);}
	~SyncObject()	{::DeleteCriticalSection(&m_sect);}
	bool Lock()		{::EnterCriticalSection(&m_sect); return true;}
	bool Unlock()	{::LeaveCriticalSection(&m_sect); return true;}

	private:
	CRITICAL_SECTION m_sect;
	};

// CEnterLeavePython class
#include "PyWinTypes.h"

#else // NOT _WIN32

class SyncObject
	{
	public:
	SyncObject()	{}
	~SyncObject()	{}
	bool Lock()		{return true;}
	bool Unlock()	{return true;}
	};

class CEnterLeavePython
	{
	public:
	CEnterLeavePython(){}
	~CEnterLeavePython(){}
	};

#endif

#endif // INC_MT
