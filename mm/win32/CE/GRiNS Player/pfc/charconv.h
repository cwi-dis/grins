#ifndef INC_CHARCONV

#pragma warning(disable: 4786)
#pragma warning(disable: 4284)
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
	:	apBuf(new TCHAR[lstrlen(pString)+1])
		{
		TCHAR *pBuf = apBuf.get();
		lstrcpy(pBuf,pString);
		TCHAR *pLook = text_strtok(pBuf,pDelims);
		while(pLook)
			{
			push_back(pLook);
			pLook = text_strtok(NULL,pDelims);
			}
		}
	private:
	std::auto_ptr<TCHAR> apBuf;
	};

#endif // INC_CHARCONV
