#include "stdafx.h"

#include "Module.h"
#include "Registry.h"
#include "Installer.h"

// set to true to open GRiNSver.log imm
static bool showResultsInNotepad=true;

// check module version for:
static const char* pszModules[]=
	{
	"mfc42.dll",
	"msvcrt.dll",

	"comdlg32.dll",
	"msvcrt40.dll",
	"oleaut32.dll",
	"ole32.dll",
	"msdxm.ocx",
	"shdocvw.dll",
	NULL,
	};

const char szHeaderMsg[]=
	"This report can be found in GRiNSver.log\nIn case of problems starting GRiNS please send this report to Oratrix.";

int main(int argc, char* argv[])
	{
	string strLogFile("GRiNSver.log");
	ofstream ofs(strLogFile.c_str());

	cout << szHeaderMsg << endl << endl;
	ofs << szHeaderMsg << endl << endl;

	Module::reportPlatformOn(ofs);
	Module::VerifyAll(pszModules,ofs);

	
	RegistryKey::reportOn(ofs,HKEY_LOCAL_MACHINE,"SOFTWARE\\MICROSOFT\\MediaPlayer");
	RegistryKey::reportOn(ofs,HKEY_LOCAL_MACHINE,"SOFTWARE\\MICROSOFT\\MediaPlayer\\Setup","SetupVersion");
	RegistryKey::reportOn(ofs,HKEY_LOCAL_MACHINE,"SOFTWARE\\MICROSOFT\\Internet Explorer","Version");
	RegistryKey::reportOn(ofs,HKEY_CLASSES_ROOT,"Webster.WebsterPro.1",NULL);
	//RegistryKey::reportOn(ofs,HKEY_LOCAL_MACHINE,"SOFTWARE\\Oratrix",NULL);
	//RegistryKey::reportOn(ofs,HKEY_CURRENT_USER,"SOFTWARE\\Oratrix",NULL);

	ofs.close();
	if(showResultsInNotepad)
		{
		string cmd("Notepad ");
		cmd+=strLogFile;
		::WinExec(cmd.c_str(),SW_SHOW);
		}

	//Installer installer("D:\ufs\mm\cmif\win32\bench\GRiNSver\from","D:\ufs\mm\cmif\win32\bench\GRiNSver\to"");
	//installer.installFile("file.xxx","file.xxx",false);

	return 0;
	}

