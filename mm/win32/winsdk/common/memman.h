#ifndef INC_MEMMAN
#define INC_MEMMAN

#ifndef _WINDOWS_
#include <windows.h>
#endif

#include <map>	

class memman
	{
	public:
	static BYTE* alloc(DWORD& capacity);
	static void free(BYTE *p, DWORD capacity);
	static void clear();
	static std::multimap<DWORD, BYTE*> s_freepages;
	};

#endif // INC_MEMMAN

