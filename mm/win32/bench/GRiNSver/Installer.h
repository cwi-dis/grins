#ifndef INC_INSTALLER
#define INC_INSTALLER

#pragma comment(lib, "version.lib")

// Needed info to use installer:
// 1. source file name +  is_it_shared? + source folder
// 2. install as dest file name
// 3. program installation folder

// Example of use:
//	Installer installer("c:\\temp\\GRiNS","C:\Program Files\Oratrix\GRiNS 0.5");
//	installer.installFile("mfc42.dll","mfc42.dll",true); // this will not use C:\Program Files\Oratrix\GRiNS 0.5 since it is shared


class Installer
	{
	public:
	Installer(LPCTSTR strSrcFolder,LPCTSTR strDstFolder);
	void installFile(LPCTSTR strName,LPCTSTR dstName,bool is_shared=false,bool forceInst=false);

	// Danger!!! Use them if you know what are you doing (i.e you know the versions, lang, etc)
	// Current implementation is valid only on NT
	// They are globals (not part of this class) but put in the namespace of Installer
	static void ForceInstallOnReboot(LPCTSTR strSrcFn,LPCTSTR strDstFn);
	static void ForceInstallMfcOnReboot(LPCTSTR strSrcFolder);

	private:
	void VerFindFile();
	void VerInstallFile();

	char szSourceFileName[_MAX_PATH];
	char szDestFileName[_MAX_PATH]; 
	char szWinDir[_MAX_PATH];
	char szAppDir[_MAX_PATH];
	char szCurDir[_MAX_PATH];
	char szDestDir[_MAX_PATH];
	char szSrcDir[_MAX_PATH];       
	char szTmpFile[_MAX_PATH];  
	UINT lenCurDir;
	UINT lenDestDir;
	UINT lenTmpFile;
	DWORD dwVerFindFileFlags;
	DWORD dwVerInstallFlags;
	};

#endif  // INC_INSTALLER

