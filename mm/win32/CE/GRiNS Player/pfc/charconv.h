#ifndef INC_CHARCONV

#pragma warning(disable: 4786) // long names trunc (debug)
#pragma warning(disable: 4018) // signed/unsigned mismatch
#include <string>
#include <vector>

#ifdef UNICODE
inline WCHAR* toTEXT(const char *p)
	{
	static WCHAR wsz[512];
	MultiByteToWideChar(CP_ACP, 0, p, -1, wsz, 512);
	return wsz;
	}
inline const WCHAR* toTEXT(const WCHAR *p)
	{
	return p;
	}
inline WCHAR* newTEXT(char *p)
	{
	int n = strlen(p)+1;
	WCHAR *wsz = new WCHAR[n];
	MultiByteToWideChar(CP_ACP, 0, p, -1, wsz, n);
	return wsz;
	}
#define text_strchr wcschr
#define text_strrchr wcsrchr
#define text_strtok wcstok
#else // UNICODE

inline const char* toTEXT(const char *p)
	{
	return p;
	}
inline char* toTEXT(WCHAR *p)
	{
	static char buf[512];
	WideCharToMultiByte(CP_ACP, 0, p, -1, buf, 512, NULL, NULL);		
	return buf;
	}
#define text_strchr strchr
#define text_strrchr strrchr
#define text_strtok strtok

#endif // UNICODE

inline const char* toMB(const char *p) {return p;}
inline char* toMB(const WCHAR *p)
	{
	static char buf[512];
	WideCharToMultiByte(CP_ACP, 0, p, -1, buf, 512, NULL, NULL);		
	return buf;
	}

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


#endif // INC_CHARCONV
