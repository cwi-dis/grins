#include "stdafx.h"

#include "Installer.h"

Installer::Installer(LPCTSTR strSrcFolder,LPCTSTR strDstFolder)
:	dwVerFindFileFlags(0),dwVerInstallFlags(VIFF_DONTDELETEOLD)
	{
	lstrcpy(szSrcDir,strSrcFolder);
	lstrcpy(szAppDir,strDstFolder);
	GetWindowsDirectory(szWinDir,_MAX_PATH);

	szSourceFileName[0]='\0';
	szDestFileName[0]='\0';
	szCurDir[0]='\0';
	szDestDir[0]='\0';
	szTmpFile[0]='\0';

	lenCurDir=_MAX_PATH;
	lenDestDir=_MAX_PATH;
	lenTmpFile=_MAX_PATH;
	}

void Installer::installFile(LPCTSTR strName,LPCTSTR dstName,bool shared,bool forceInst)
	{
	if(shared) dwVerFindFileFlags=VFFF_ISSHAREDFILE;
	lstrcpy(szSourceFileName,strName);
	lstrcpy(szDestFileName,dstName);
	VerFindFile();

	if(forceInst) dwVerInstallFlags|=VIFF_FORCEINSTALL;
	VerInstallFile();
	}

void Installer::VerFindFile()
	{	
	DWORD res=::VerFindFile(
		dwVerFindFileFlags,
		szDestFileName,
		szWinDir,
		szAppDir,
		szCurDir,
		&lenCurDir,
		szDestDir,
		&lenDestDir);
	if(res==VFF_FILEINUSE)
		cout << "The system is using the currently installed version of the file;\ntherefore, the file cannot be overwritten or deleted."
		       << endl;
	cout << "VerFindFile::szWinDir=" << szWinDir<< endl;
	cout << "VerFindFile::szAppDir=" << szAppDir<< endl;
	cout << "VerFindFile::szCurDir=" << szCurDir<< endl;
	cout << "VerFindFile::szDestDir=" << szDestDir<< endl;
	}

void Installer::VerInstallFile()
	{
	DWORD res=::VerInstallFile(
		dwVerInstallFlags,
		szSourceFileName,
		szDestFileName,
		szSrcDir,
		szDestDir,
		szCurDir,
		szTmpFile,
		&lenTmpFile
		);
	cout << "VerInstallFile::szSrcDir=" << szSrcDir<< endl;
	cout << "VerInstallFile::szDestDir=" << szDestDir<< endl;
	cout << "VerInstallFile::szCurDir=" << szCurDir<< endl;
	cout << "VerInstallFile::szTmpFile=" << szTmpFile<< endl;

	bool bCanInstall=true;
	bool bUnknown=false;
	if(res & VIF_TEMPFILE){bCanInstall=false;cout << "VIF_TEMPFILE" << endl;}
	if(res & VIF_MISMATCH){bCanInstall=false;cout << "VIF_MISMATCH" << endl;}
	if(res & VIF_DIFFLANG){bCanInstall=false;cout << "VIF_DIFFLANG" << endl;}
	if(res & VIF_SRCOLD){bCanInstall=false;cout << "VIF_SRCOLD" << endl;}
	if(res & VIF_DIFFLANG){bCanInstall=false;cout << "VIF_DIFFLANG" << endl;}
	if(res & VIF_DIFFCODEPG){bCanInstall=false;cout << "VIF_DIFFCODEPG" << endl;}
	if(res & VIF_DIFFTYPE){bCanInstall=false;cout << "VIF_DIFFTYPE" << endl;}
	if(res & VIF_WRITEPROT)cout << "VIF_WRITEPROT" << endl;
	if(res & VIF_FILEINUSE){bUnknown=true;cout << "VIF_FILEINUSE" << endl;}
	if(res & VIF_ACCESSVIOLATION)cout << "VIF_ACCESSVIOLATION" << endl;
	if(res & VIF_SHARINGVIOLATION)cout << "VIF_SHARINGVIOLATION" << endl;
	if(res & VIF_OUTOFSPACE)cout << "VIF_OUTOFSPACE" << endl;
	if(res & VIF_CANNOTCREATE)cout << "VIF_CANNOTCREATE" << endl;
	if(res & VIF_CANNOTDELETE)cout << "VIF_CANNOTDELETE" << endl;
	if(res & VIF_CANNOTDELETECUR)cout << "VIF_CANNOTDELETECUR" << endl;
	if(res & VIF_CANNOTREADSRC)cout << "VIF_CANNOTREADSRC" << endl;
	if(bCanInstall && !bUnknown)
		cout << "File " <<  szDestFileName <<" can be installed without problems" << endl;
	if(bUnknown)
		cout << "File " <<  szDestFileName <<" is in use. VerInstallFile can not check it." << endl;
	}

// Danger!!! Use them if you know what are you doing (i.e you know the versions, lang, etc)
// Current implementation is valid only on NT
// static
void Installer::ForceInstallOnReboot(LPCTSTR strSrcFn,LPCTSTR strDstFn)
	{
	DWORD dwFlags=MOVEFILE_DELAY_UNTIL_REBOOT | MOVEFILE_REPLACE_EXISTING;
	if(MoveFileEx(strSrcFn,strDstFn,dwFlags))
		cout << strSrcFn << " will be installed on reboot" << endl;
	}

// Danger!!! Use them if you know what are you doing (i.e you know the versions, lang, etc)
// Current implementation is valid only on NT
// static
void Installer::ForceInstallMfcOnReboot(LPCTSTR strSrcFolder)
	{
	DWORD dwFlags=MOVEFILE_DELAY_UNTIL_REBOOT | MOVEFILE_REPLACE_EXISTING;

	char szSrc[_MAX_PATH];
	char szDst[_MAX_PATH];

	// copy msvcrt.dll
	lstrcpy(szSrc,strSrcFolder);lstrcat(szSrc,"\\");lstrcat(szSrc,"msvcrt.dll");
	::GetSystemDirectory(szDst,_MAX_PATH);lstrcat(szDst,"\\");lstrcat(szDst,"msvcrt.dll");
	if(MoveFileEx(szSrc,szDst,dwFlags))
		cout << "msvcrt.dll will be installed on reboot" << endl;
	else
		cout << "MoveFileEx failed for " << szSrc << endl;

	lstrcpy(szSrc,strSrcFolder);lstrcat(szSrc,"\\");lstrcat(szSrc,"mfc42.dll");
	::GetSystemDirectory(szDst,_MAX_PATH);lstrcat(szDst,"\\");lstrcat(szDst,"msvcrt.dll");
	if(MoveFileEx(szSrc,szDst,dwFlags))
		cout << "mfc42.dll will be installed on reboot" << endl;
	else
		cout << "MoveFileEx failed for " << szSrc << endl;
	}
