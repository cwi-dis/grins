#ifndef INC_REGKEY
#define INC_REGKEY

class RegKey
	{
	public:
	RegKey(HKEY hKey=0) :	m_hKey(hKey){}
		
	RegKey(HKEY hParent, LPCTSTR lpSubKey, bool bCreate=false)
	:	m_hKey(0)
		{
		LONG res = RegOpenKeyEx(hParent,lpSubKey, 0, KEY_ALL_ACCESS, &m_hKey);
		if(res!=ERROR_SUCCESS && bCreate)
			{
			if(!Create(hParent, lpSubKey)) m_hKey = 0;
			}
		}

	bool Create(HKEY hParent, LPCTSTR lpSubKey)
		{
		if(m_hKey) RegCloseKey(m_hKey);
		LONG res = RegCreateKeyEx(hParent,lpSubKey, 
	                              0, NULL, 
								  REG_OPTION_NON_VOLATILE,
	                              KEY_ALL_ACCESS, NULL, 
	                              &m_hKey, NULL) ;
		return (res==ERROR_SUCCESS);
		}

	~RegKey(){if(m_hKey) RegCloseKey(m_hKey);}
		
	bool SetValueSz(LPCTSTR pszValue, LPCTSTR pszValueName=NULL)
		{
		LONG res = RegSetValueEx(m_hKey, pszValueName, 0, REG_SZ, 
		              (BYTE *)pszValue, 
		              lstrlen(pszValue)+1);
		return (res==ERROR_SUCCESS);
		}
	
	bool SetValueBinary(BYTE *pData, int len, LPCTSTR pszValueName=NULL)
		{
		LONG res = RegSetValueEx(m_hKey, pszValueName, 0, REG_BINARY, 
		              (BYTE *)pData, len);
		return (res==ERROR_SUCCESS);
		}
	
	bool SetValueDword(DWORD data, LPCTSTR pszValueName=NULL)
		{
		LONG res = RegSetValueEx(m_hKey, pszValueName, 0, REG_DWORD, 
		              (BYTE*)&data, sizeof(DWORD));
		return (res==ERROR_SUCCESS);
		}

	LPCTSTR QueryStrValue(LPCTSTR strVal, DWORD size=256)
		{
		static char psz[256]="";
		if(!m_hKey) return psz;
		long res=RegQueryValueEx(m_hKey,strVal,0,0,(BYTE*)psz,&size);
		if(res!=ERROR_SUCCESS) psz[0]='\0';
		return psz;
		}
	
	static bool DeleteKey(HKEY hParent, LPCTSTR lpSubKey)
		{
		RegKey key(hParent, lpSubKey);
		if(!HKEY(key)) return true;
		
		char szBuffer[256];
		DWORD dwSize = 256;
		while(RegEnumKeyEx(key, 0, szBuffer, &dwSize, NULL, NULL, NULL, NULL) == ERROR_SUCCESS)
			{
			if(!DeleteKey(key, szBuffer))
				{
				RegCloseKey(key);
				return false;
				}
			dwSize = 256;
			}
		RegCloseKey(key);
		RegDeleteKey(hParent, lpSubKey);
		return true;
		}
	
	operator HKEY()  {return m_hKey;}
	
	private:
	HKEY m_hKey;
	};


#endif

