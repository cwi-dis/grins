#ifndef INC_REGISTRY
#define INC_REGISTRY

class RegistryKey
	{
	public:
	RegistryKey(HKEY h,LPCTSTR lpSubKey)
		: m_strSubKey(lpSubKey)
		{
		LONG res=::RegOpenKeyEx(h,lpSubKey,
					0,KEY_ALL_ACCESS,&m_hKey);
		if(res!=ERROR_SUCCESS) m_hKey=0;
		}
	~RegistryKey(){if(m_hKey)::RegCloseKey(m_hKey);}
	
	string QueryStrValue(LPCTSTR strVal,DWORD size=512)
		{
		if(!m_hKey) return string("");

		char *psz=new char[size];
		long res=::RegQueryValueEx(m_hKey,strVal,0,0,(BYTE*)psz,&size);
		if(res!=ERROR_SUCCESS) psz[0]='\0';
		string str(psz);
		delete[] psz;
		return str;
		}
	operator HKEY()  {return m_hKey;}
	void reportOn(ostream& os);
	void reportOn(ostream& os, LPCTSTR str);

	static void reportOn(ostream& os,HKEY hkey,LPCTSTR strSubKey);
	static void reportOn(ostream& os,HKEY hkey,LPCTSTR strSubKey, LPCTSTR strName);

	private:
	HKEY m_hKey;
	string m_strSubKey;
	};


inline void RegistryKey::reportOn(ostream& os)
	{
	if(m_hKey)
		{
		os << "Registry key " << m_strSubKey << " opened." << endl;
		}
	else
		{
		os << "Registry key " << m_strSubKey << " failed to open." << endl;
		return;
		}
	}
inline void RegistryKey::reportOn(ostream& os, LPCTSTR str)
	{
	if(m_hKey)
		{
		os << "Registry key " << m_strSubKey << " opened." << endl;
		}
	else
		{
		os << "Registry key " << m_strSubKey << " failed to open" << endl;
		return;
		}
	string strVal=QueryStrValue(str);
	string strName;
	if(!str) strName="Default";
	else strName=str;
	os << strName << ": " << strVal << endl;
	os << endl;
	}

// static
inline void RegistryKey::reportOn(ostream& os,HKEY hkey,LPCTSTR strSubKey, LPCTSTR strName)
	{
	RegistryKey key(hkey,strSubKey);
	key.reportOn(os,strName);
	key.reportOn(cout,strName);
	}
// static
inline void RegistryKey::reportOn(ostream& os,HKEY hkey,LPCTSTR strSubKey)
	{
	RegistryKey key(hkey,strSubKey);
	key.reportOn(os);
	key.reportOn(cout);
	}

#endif // INC_REGKEY