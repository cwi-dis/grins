#ifndef INC_MODULE
#define INC_MODULE

#pragma comment(lib, "version.lib")

class Module : public VS_FIXEDFILEINFO 
	{
	public:
	Module(LPCTSTR strName);
	void reportOn(ostream& os);

	~Module();

	static void VerifyAll(const char* pstr[],ostream& os);

	private:
	bool isLoaded() const {return m_hMod!=NULL;}
	bool getFileVersionInfo();
	struct TRANSLATION 
		{
		WORD langID;        
		WORD charset;
		} m_translation;
	BYTE* m_pVersionInfo;
	HINSTANCE m_hMod;
	string m_strName;
	bool m_verRes;
	};


////////////////////////////////////////////
inline Module::Module(LPCTSTR strName)
:	m_strName(strName),
	m_pVersionInfo(NULL),
	m_verRes(false)
	{
	m_hMod=::LoadLibrary(strName);
	if(m_hMod) m_verRes=getFileVersionInfo();
	}

inline Module::~Module()
		{
		if(m_hMod)::FreeLibrary(m_hMod);
		if(m_pVersionInfo) delete[] m_pVersionInfo;
		}

inline void Module::reportOn(ostream& os)
	{
	if(isLoaded())
		{
		os << "Module " << m_strName << " loaded" << endl;
		}
	else
		{
		os << "Module " << m_strName << " failed to load" << endl;
		return;
		}
	if(m_verRes)
		{
		string s;
        Format(s,"Module %s version: %d.%d.%d.%d\n",m_strName.c_str(),
                 HIWORD(dwFileVersionMS), LOWORD(dwFileVersionMS),
                 HIWORD(dwFileVersionLS), LOWORD(dwFileVersionLS));
		os << s << endl;
		}
	else
		{
		os << "Failed to get file version for module " << m_strName << endl;
		}
	}

inline bool Module::getFileVersionInfo()
	{
	if(!isLoaded()) return false;

	m_translation.charset = 1252;    // default = ANSI code page
	memset((VS_FIXEDFILEINFO*)this, 0, sizeof(VS_FIXEDFILEINFO));

	TCHAR filename[_MAX_PATH];
    DWORD len = GetModuleFileName(m_hMod, filename,
		sizeof(filename)/sizeof(filename[0]));
	if(len<=0) return false;

	// read file version info
	DWORD dwDummyHandle; // will always be set to zero
	len = GetFileVersionInfoSize(filename, &dwDummyHandle);
	if (len <= 0) return false;

	m_pVersionInfo = new BYTE[len]; // allocate version info
	if (!::GetFileVersionInfo(filename, 0, len, m_pVersionInfo))
		return false;

	LPVOID lpvi;
	UINT iLen;
	if (!VerQueryValue(m_pVersionInfo, "\\", &lpvi, &iLen))
		return false;

	// copy fixed info to myself, which am derived from VS_FIXEDFILEINFO
	*(VS_FIXEDFILEINFO*)this = *(VS_FIXEDFILEINFO*)lpvi;

	// Get translation info
	if (VerQueryValue(m_pVersionInfo,"\\VarFileInfo\\Translation", &lpvi, &iLen) && iLen >= 4) 
		m_translation = *(TRANSLATION*)lpvi;

	return dwSignature == VS_FFI_SIGNATURE;
	}


//static 
inline void Module::VerifyAll(const char* pstr[],ostream& os)
	{
	int i=0;
	while(pstr[i] && lstrlen(pstr[i])>0)
		{
		Module mod(pstr[i]);
		mod.reportOn(cout);
		mod.reportOn(os);
		i++;
		}
	}

#endif // INC_MODULE
