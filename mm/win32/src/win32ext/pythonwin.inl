#ifndef INC_PYTHONWIN_INC

// For development read pythonpath from pythonwin.ini 
// located in the program's folder instead of the registry.
// No validation checks
inline const char* getentry(const char* pszSec,const char* pszEntry, char *psz,int len)
	{
	char szBuf[MAX_PATH];
    ::GetModuleFileName(AfxGetInstanceHandle(),szBuf,sizeof(szBuf));
    char *p = strrchr(szBuf,'.');
	*p = '\0';
    lstrcat(szBuf,".ini");
    ::GetPrivateProfileString(pszSec,pszEntry,"",psz,len,szBuf);
	return psz;
	}

inline const char* pythonwinpath(char *psz,int len)
	{
	getentry("GENERAL","PYTHONPATH",psz,len);
	if(!psz[0])
		{
		psz[0]='.';
		psz[1]='\0';
		}
	return psz;
	}


#endif