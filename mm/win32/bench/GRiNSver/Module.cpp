#include "stdafx.h"

#include "Module.h"


Module::Module(LPCTSTR strName)
:	m_strName(strName),
	m_pVersionInfo(NULL),
	m_verRes(false)
	{
	m_hMod=::LoadLibrary(strName);
	if(m_hMod) m_verRes=getFileVersionInfo();
	}

Module::~Module()
	{
	if(m_hMod)::FreeLibrary(m_hMod);
	if(m_pVersionInfo) delete[] m_pVersionInfo;
	}

void Module::reportOn(ostream& os)
	{
	if(isLoaded())
		{
		os << "Module " << m_strName << " loaded (" << m_modulePathname << ")" << endl;
		}
	else
		{
		os << "Module " << m_strName << " failed to load" << endl;
		return;
		}
	if(m_verRes)
		{
		string s;
        Format(s,"Module %s version: %d.%d.%d.%d",m_strName.c_str(),
                 HIWORD(dwFileVersionMS), LOWORD(dwFileVersionMS),
                 HIWORD(dwFileVersionLS), LOWORD(dwFileVersionLS));
		os << s << endl;
		reportLangOn(os);
		reportFileOSOn(os);
		}
	else
		{
		os << "Failed to get file version for module " << m_strName << endl;
		}
	os << endl;
	}

void Module::reportLangOn(ostream& os)
	{
	if(!m_verRes) return;

	char szLang[256];
	VerLanguageName(m_translation.langID,szLang,256);
	os << szLang << "  ";
	if(m_translation.charset==1200)
		os << "(code page " << m_translation.charset  << " = Unicode)" << endl;
	else if(m_translation.charset==1252)
		os <<  "(code page " << m_translation.charset  << " = ANSI)" << endl;
	else
		os << "(code page " << m_translation.charset  << ")" << endl;
	}

void Module::reportFileOSOn(ostream& os)
	{
	if(!m_verRes) return;
	
	if(dwFileOS==VOS__WINDOWS32) os << "FileOS ID=" << dwFileOS << " (WINDOWS32)" << endl;
	else if(dwFileOS==VOS_NT) os << "FileOS ID=" << dwFileOS << " (NT)" << endl;
	else if(dwFileOS==VOS_UNKNOWN) os << "FileOS ID=" << dwFileOS << " (UNKNOWN)" << endl;
	else os << "FileOS ID=" << dwFileOS << endl;
	}
bool Module::getFileVersionInfo()
	{
	if(!isLoaded()) return false;

	m_translation.charset = 1252;    // default = ANSI code page
	memset((VS_FIXEDFILEINFO*)this, 0, sizeof(VS_FIXEDFILEINFO));

	TCHAR filename[_MAX_PATH];
    DWORD len = GetModuleFileName(m_hMod, filename,
		sizeof(filename)/sizeof(filename[0]));
	if(len<=0) return false;
	m_modulePathname=filename;

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
void Module::VerifyAll(const char* pstr[],ostream& os)
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

// static 
void Module::reportPlatformOn(ostream& os)
	{
	OSVERSIONINFO osvi;
	memset(&osvi,0,sizeof(OSVERSIONINFO));
	osvi.dwOSVersionInfoSize=sizeof(OSVERSIONINFO);
	GetVersionEx(&osvi);

	if(osvi.dwPlatformId == VER_PLATFORM_WIN32_NT)
		os << "Running on Windows NT";

	if((osvi.dwPlatformId == VER_PLATFORM_WIN32_WINDOWS) &&
		( (osvi.dwMajorVersion > 4) ||
		( (osvi.dwMajorVersion == 4) && (osvi.dwMinorVersion > 0) ) ))
		os << "Running on Windows 98";

	if((osvi.dwPlatformId == VER_PLATFORM_WIN32_WINDOWS) && osvi.dwMinorVersion == 0)
		os << "Running on Windows 95";

	os << " (Version " << osvi.dwMajorVersion << "." << osvi.dwMinorVersion <<  ", Build " << osvi.dwBuildNumber << ", "<< osvi.szCSDVersion << ")" << endl;
	os <<  endl;
	}
