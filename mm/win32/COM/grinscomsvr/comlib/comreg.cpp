#include "stdafx.h"

#include "comreg.h"

#include "regkey.h"

LPCTSTR toString(const CLSID& clsid)
	{
	enum {CLSID_STRING_SIZE = 39};
	static char pszCLSID[CLSID_STRING_SIZE];
	LPOLESTR pwszCLSID = NULL ;
	HRESULT hr = StringFromCLSID(clsid, &pwszCLSID) ;
	wcstombs(pszCLSID, pwszCLSID, CLSID_STRING_SIZE);
	CoTaskMemFree(pwszCLSID) ;
	return pszCLSID;
	}

LPCTSTR toPath(char *dst,LPCTSTR src1, LPCTSTR src2) 
	{
	dst[0]='\0';
	if(src1)strcpy(dst, src1);
	if(src2){strcat(dst, "\\");strcat(dst, src2);}
	return dst;
	}

bool setKeyAndValue(LPCTSTR pszKey, LPCTSTR pszSubkey, LPCTSTR szValue)
	{
	char szKeyBuf[1024] ;
	RegKey key(HKEY_CLASSES_ROOT, toPath(szKeyBuf,pszKey,pszSubkey), true);
	if(HKEY(key)) return key.SetValueSz(szValue);
	return false;
	}

bool subkeyExists(LPCTSTR pszKey, LPCTSTR pszSubkey)
	{
	char szKeyBuf[1024] ;
	RegKey key(HKEY_CLASSES_ROOT, toPath(szKeyBuf,pszKey,pszSubkey), false);
	return HKEY(key)!=0;
	}

bool RegisterServer(HMODULE hModule, COMSERVER_INFO *pcsi)
	{
	char szModule[512];
	GetModuleFileName(hModule, szModule, sizeof(szModule)/sizeof(char));
	char szKey[64];
	strcpy(szKey, "CLSID\\");
	const char *pszCLSID = toString(*pcsi->pclsid);
	strcat(szKey, pszCLSID);
	setKeyAndValue(szKey, NULL, pcsi->pszFriendlyName);
	if(pcsi->inProc)
		setKeyAndValue(szKey,"InprocServer32",szModule);		
	else
		setKeyAndValue(szKey,"LocalServer32",szModule);
	setKeyAndValue(szKey,"ProgID",pcsi->pszProgID);
	setKeyAndValue(szKey,"VersionIndependentProgID",pcsi->pszVerIndProgID);
	setKeyAndValue(pcsi->pszVerIndProgID,NULL, pcsi->pszFriendlyName); 
	setKeyAndValue(pcsi->pszVerIndProgID,"CLSID", pszCLSID);
	setKeyAndValue(pcsi->pszVerIndProgID,"CurVer", pcsi->pszProgID);
	setKeyAndValue(pcsi->pszProgID, NULL, pcsi->pszFriendlyName); 
	setKeyAndValue(pcsi->pszProgID, "CLSID", pszCLSID);
	return true;
	}

bool UnregisterServer(COMSERVER_INFO *pcsi)
	{
	char szKey[80];
	strcpy(szKey, "CLSID\\");
	const char *pszCLSID = toString(*pcsi->pclsid);
	strcat(szKey, pszCLSID);
	if(pcsi->inProc?subkeyExists(szKey,"InprocServer32"):subkeyExists(szKey,"LocalServer32"))
		{
		if(pcsi->inProc)strcat(szKey, "\\InprocServer32");
		else strcat(szKey, "\\LocalServer32");
		RegKey::DeleteKey(HKEY_CLASSES_ROOT, szKey);
		}
	else
		{
		RegKey::DeleteKey(HKEY_CLASSES_ROOT, szKey);
		RegKey::DeleteKey(HKEY_CLASSES_ROOT, pcsi->pszVerIndProgID);
		RegKey::DeleteKey(HKEY_CLASSES_ROOT, pcsi->pszProgID);
		}
	return true;
	}

