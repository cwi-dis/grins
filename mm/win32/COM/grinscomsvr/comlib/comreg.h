#ifndef INC_COMREG
#define INC_COMREG

struct COMSERVER_INFO
	{
	const CLSID *pclsid;   
	LPCTSTR pszFriendlyName;
	LPCTSTR pszVerIndProgID;
	LPCTSTR pszProgID;
	bool inProc;
	};
	
bool RegisterServer(HMODULE hModule, COMSERVER_INFO *pcsi);
bool UnregisterServer(COMSERVER_INFO *pcsi);

#endif
