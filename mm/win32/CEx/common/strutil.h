
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#ifndef INC_STRUTIL
#define INC_STRUTIL

#pragma warning(disable: 4786) // long names trunc (debug)
#pragma warning(disable: 4018) // signed/unsigned mismatch
#include <string>

#ifndef _WINDOWS_
#include <windows.h>
#endif

#ifndef INC_CHARCONV
#include "charconv.h"
#endif

#include <vector>
class StrRec : public std::vector<TCHAR*>
	{
	public:
    StrRec(const TCHAR* pString,const TCHAR* pDelims)
	:	buf(new TCHAR[lstrlen(pString)+1])
		{
		lstrcpy(buf, pString);
		TCHAR *pLook = text_strtok(buf, pDelims);
		while(pLook)
			{
			push_back(pLook);
			pLook = text_strtok(NULL, pDelims);
			}
		}
    ~StrRec() {delete[] buf;}
	private:
	TCHAR* buf;
	};


inline std::string fixendl(const char *psz)
	{
	std::string str;
	const char *p = psz;
	while(*p)
		{
		if(*p == '\r' && *(p+1) != '\n')
			str += "\r\n";
		else if(*p == '\n' && (p==psz || *(p-1) != '\r'))
			str += "\r\n";
		else
			str += *p;
		p++;
		}
	return str;
	}

#endif // INC_STRUTIL
