#include <windows.h>
#include "resource.h"

void RunBatchFile(LPCTSTR pszCmd);

int APIENTRY WinMain(HINSTANCE hInstance,
                     HINSTANCE hPrevInstance,
                     LPSTR     lpCmdLine,
                     int       nCmdShow)
	{
	char cmd[2*MAX_PATH]="";
	if(LoadString(hInstance,IDS_BATFILE,cmd,MAX_PATH))
		{
		lstrcat(cmd," ");
		lstrcat(cmd,lpCmdLine);
		RunBatchFile(cmd);
		}
	return 0;
	}

void RunBatchFile(LPCTSTR pszCmd)
	{
	STARTUPINFO si;
	PROCESS_INFORMATION pi;

	ZeroMemory(&si, sizeof(si));
	ZeroMemory(&pi, sizeof(pi));
	si.cb = sizeof(si);

	// We want the console window to be invisible to the user.
	si.dwFlags = STARTF_USESHOWWINDOW;
	si.wShowWindow = SW_HIDE;

	// Spawn the batch file with normal-priority.	
	if (CreateProcess(NULL,(LPTSTR)pszCmd, NULL, NULL, FALSE,
		 NORMAL_PRIORITY_CLASS, NULL, NULL, &si, &pi)) 
		{	
		CloseHandle(pi.hProcess);
		CloseHandle(pi.hThread);
		}
	}


