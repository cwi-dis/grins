#include "stdafx.h"

#include "Registrar.h"

LONG Registrar::RegisterServer(
						HMODULE hModule,            
						const CLSID& clsid,         
						const char* szFriendlyName, 
						const char* szVerIndProgID, 
						const char* szProgID,
						bool InProc)       
	{
	// Get server location.
	char szModule[512] ;
	DWORD dwResult = ::GetModuleFileName(hModule, 
		                    szModule,
		                    sizeof(szModule)/sizeof(char)) ;
	assert(dwResult != 0) ;

	// Convert the CLSID into a char.
	char szCLSID[CLSID_STRING_SIZE] ;
	CLSIDtochar(clsid, szCLSID, sizeof(szCLSID)) ;

	// Build the key CLSID\\{...}
	char szKey[64] ;
	strcpy(szKey, "CLSID\\") ;
	strcat(szKey, szCLSID) ;
  
	// Add the CLSID to the registry.
	setKeyAndValue(szKey, NULL,szFriendlyName) ;

	// Add the server filename subkey under the CLSID key.
	if(InProc)
		setKeyAndValue(szKey,"InprocServer32",szModule) ;		
	else
		setKeyAndValue(szKey,"LocalServer32",szModule) ;

	// Add the ProgID subkey under the CLSID key.
	setKeyAndValue(szKey,"ProgID",szProgID) ;

	// Add the version-independent ProgID subkey under CLSID key.
	setKeyAndValue(szKey,"VersionIndependentProgID",szVerIndProgID) ;

	// Add the version-independent ProgID subkey under HKEY_CLASSES_ROOT.
	setKeyAndValue(szVerIndProgID,NULL, szFriendlyName) ; 
	setKeyAndValue(szVerIndProgID,"CLSID", szCLSID) ;
	setKeyAndValue(szVerIndProgID,"CurVer", szProgID) ;

	// Add the versioned ProgID subkey under HKEY_CLASSES_ROOT.
	setKeyAndValue(szProgID, NULL, szFriendlyName) ; 
	setKeyAndValue(szProgID, "CLSID", szCLSID) ;

	return ERROR_SUCCESS;
	}

// Remove the component from the registry.
LONG Registrar::UnregisterServer(
						const CLSID& clsid,         
						const char* szVerIndProgID, 
						const char* szProgID,
						bool  InProc)       
	{
	// Convert the CLSID into a char.
	char szCLSID[CLSID_STRING_SIZE] ;
	CLSIDtochar(clsid, szCLSID, sizeof(szCLSID)) ;

	// Build the key CLSID\\{...}
	char szKey[80] ;
	strcpy(szKey, "CLSID\\") ;
	strcat(szKey, szCLSID) ;

	// Check for a another server for this component.
	if(InProc?SubkeyExists(szKey,"InprocServer32"):SubkeyExists(szKey,"LocalServer32"))
		{
		// Delete only the path for this server.
		if(InProc)
			strcat(szKey, "\\InprocServer32");
		else
			strcat(szKey, "\\LocalServer32") ;
		LONG lResult = recursiveDeleteKey(HKEY_CLASSES_ROOT, szKey) ;
		assert(lResult == ERROR_SUCCESS) ;
		}
	else
		{
		// Delete all related keys.
		// Delete the CLSID Key - CLSID\{...}
		LONG lResult = recursiveDeleteKey(HKEY_CLASSES_ROOT, szKey) ;
		assert((lResult == ERROR_SUCCESS) ||
		       (lResult == ERROR_FILE_NOT_FOUND)) ; // Subkey may not exist.

		// Delete the version-independent ProgID Key.
		lResult = recursiveDeleteKey(HKEY_CLASSES_ROOT, szVerIndProgID) ;
		assert((lResult == ERROR_SUCCESS) ||
		       (lResult == ERROR_FILE_NOT_FOUND)) ; // Subkey may not exist.

		// Delete the ProgID key.
		lResult = recursiveDeleteKey(HKEY_CLASSES_ROOT, szProgID) ;
		assert((lResult == ERROR_SUCCESS) ||
		       (lResult == ERROR_FILE_NOT_FOUND)) ; // Subkey may not exist.
		}
	return S_OK ;
	}


void Registrar::CLSIDtochar(const CLSID& clsid,char* szCLSID,int length)
	{
	assert(length >= CLSID_STRING_SIZE);

	// Get CLSID
	LPOLESTR wszCLSID = NULL ;
	HRESULT hr = StringFromCLSID(clsid, &wszCLSID) ;
	assert(SUCCEEDED(hr)) ;

	// Covert from wide characters to non-wide.
	wcstombs(szCLSID, wszCLSID, length) ;

	// Free memory.
	CoTaskMemFree(wszCLSID) ;
	}

// Delete a key and all of its descendents.
LONG Registrar::recursiveDeleteKey(HKEY hKeyParent,const char* lpszKey)  
	{
	// Open the child.
	HKEY hKey;
	LONG lRes = RegOpenKeyEx(hKeyParent, lpszKey,0,
	                         KEY_ALL_ACCESS,&hKey) ;
	if (lRes != ERROR_SUCCESS)return lRes;

	// Enumerate all of the decendents of this child.
	FILETIME time ;
	char szBuffer[256] ;
	DWORD dwSize = 256 ;
	while (RegEnumKeyEx(hKey, 0, szBuffer, &dwSize, NULL,
	                    NULL, NULL, &time) == S_OK)
		{
		// Delete the decendents of this child.
		lRes = recursiveDeleteKey(hKey, szBuffer) ;
		if (lRes != ERROR_SUCCESS)
			{
			// Cleanup before exiting.
			RegCloseKey(hKey) ;
			return lRes;
			}
		dwSize = 256 ;
		}

	// Close the child.
	RegCloseKey(hKey) ;

	// Delete this child.
	return RegDeleteKey(hKeyParent,lpszKey);
	}

// Determine if a particular subkey exists.
bool Registrar::SubkeyExists(const char* pszPath,const char* szSubkey)   
	{
	HKEY hKey ;
	char szKeyBuf[80] ;

	// Copy keyname into buffer.
	strcpy(szKeyBuf, pszPath) ;

	// Add subkey name to buffer.
	if (szSubkey != NULL)
		{
		strcat(szKeyBuf, "\\") ;
		strcat(szKeyBuf, szSubkey ) ;
		}

	// Determine if key exists by trying to open it.
	LONG lResult = ::RegOpenKeyEx(HKEY_CLASSES_ROOT, 
	                              szKeyBuf,
	                              0,
	                              KEY_ALL_ACCESS,
	                              &hKey) ;
	if (lResult == ERROR_SUCCESS)
		{
		RegCloseKey(hKey) ;
		return true ;
		}
	return false ;
	}


// Create a key and set its value.
bool Registrar::setKeyAndValue(
					const char* szKey,
                    const char* szSubkey,
                    const char* szValue)
	{
	HKEY hKey;
	char szKeyBuf[1024] ;

	// Copy keyname into buffer.
	strcpy(szKeyBuf, szKey) ;

	// Add subkey name to buffer.
	if (szSubkey != NULL)
		{
		strcat(szKeyBuf, "\\") ;
		strcat(szKeyBuf, szSubkey ) ;
		}

	// Create and open key and subkey.
	long lResult = RegCreateKeyEx(HKEY_CLASSES_ROOT ,
	                              szKeyBuf, 
	                              0, NULL, REG_OPTION_NON_VOLATILE,
	                              KEY_ALL_ACCESS, NULL, 
	                              &hKey, NULL) ;
	if (lResult != ERROR_SUCCESS)
		return false;

	// Set the Value.
	if (szValue != NULL)
		{
		RegSetValueEx(hKey, NULL, 0, REG_SZ, 
		              (BYTE *)szValue, 
		              strlen(szValue)+1) ;
		}

	RegCloseKey(hKey);
	return true;
	}
