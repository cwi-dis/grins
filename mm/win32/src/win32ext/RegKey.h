#ifndef INC_REGKEY
#define INC_REGKEY

class RegistryKey
	{
	public:
	RegistryKey(HKEY h,LPCTSTR lpSubKey)
		{
		LONG res=RegOpenKeyEx(h,lpSubKey,
					0,KEY_ALL_ACCESS,&hKey);
		if(res!=ERROR_SUCCESS) hKey=0;
		}
	~RegistryKey(){if(hKey)RegCloseKey(hKey);}
	
	CString QueryStrValue(LPCTSTR strVal,DWORD size=256)
		{
		CString str;
		if(!hKey) return str;

		char *psz=str.GetBuffer(size);
		long res=RegQueryValueEx(hKey,strVal,0,0,(BYTE*)psz,&size);
		if(res!=ERROR_SUCCESS) psz[0]='\0';
		str.ReleaseBuffer();
		return str;
		}
	operator HKEY()  {return hKey;}

	private:
	HKEY hKey;
	};

inline int GetIEVersion()
	{
	RegistryKey key(HKEY_LOCAL_MACHINE,"SOFTWARE\\MICROSOFT\\Internet Explorer");
	CString strValue=key.QueryStrValue("Version");
	if strValue.IsEmpty() return 1;
	return atoi(strValue);
	}

#endif // INC_REGKEY