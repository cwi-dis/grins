#ifndef INC_WINDOWINTERFACE
#define INC_WINDOWINTERFACE

#ifndef _WINDOWS_
#include <windows.h>
#endif

#ifndef INC_EXTRA_TYPES
#include "extra_types.h"
#endif

class messagebox
	{
	public:
	messagebox(const TCHAR *text, const char *mtype = "message", 
		v_callback_v ok = 0, v_callback_v cancel = 0);
	
	int getresult() const { return m_res;}

	private:
	int m_res;
	};

inline messagebox showmessage(const TCHAR *text, const char *mtype = "message", 
		v_callback_v ok = 0, v_callback_v cancel = 0)
	{
	return messagebox(text, mtype, ok, cancel);
	}

#endif // 	 INC_WINDOWINTERFACE
