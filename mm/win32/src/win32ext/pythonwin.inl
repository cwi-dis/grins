#ifndef INC_PYTHONWIN_INC

// For development read pythonpath from pythonwin.ini 
// located in the program's folder instead of the registry.
// No validation checks
inline const char* pythonwinpath(char *psz,int len)
	{
	char szBuf[MAX_PATH];
    ::GetModuleFileName(AfxGetInstanceHandle(),szBuf,sizeof(szBuf));
    char *p = strrchr(szBuf,'.');
	*p = '\0';
    lstrcat(szBuf,".ini");
    ::GetPrivateProfileString("GENERAL","PYTHONPATH",".",psz,len,szBuf);
	return psz;
	}

#endif