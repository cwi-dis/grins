
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#ifndef INC_PLATFORM
#define INC_PLATFORM

#include <windows.h>

namespace platform {

inline int open(const TCHAR *filename)
	{
	HANDLE hf = CreateFile(filename,  
		GENERIC_READ,  
		FILE_SHARE_READ,  // 0 = not shared or FILE_SHARE_READ  
		0,  // lpSecurityAttributes 
		OPEN_EXISTING,  
		FILE_ATTRIBUTE_READONLY,  
		NULL); 
	if(hf == INVALID_HANDLE_VALUE) 
		return -1;
	return int(hf);
	}

inline void close(int handle)
	{
	CloseHandle(HANDLE(handle));
	}

enum {f_begin = FILE_BEGIN, f_current = FILE_CURRENT, f_end = FILE_END};
inline void seek(int handle, unsigned int pos, int move)
	{
	SetFilePointer(HANDLE(handle), pos, 0, move);
	}
	
inline int read(int handle, void *buffer, unsigned int count)
	{
	unsigned long bytesRead = 0;
	if(!ReadFile(HANDLE(handle), buffer, count, &bytesRead, NULL)) 
		return -1;
	return bytesRead;
	}


} // namespace platform


#endif  // INC_PLATFORM
