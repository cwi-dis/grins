/*------------------------------------------------------------
   HELLOWIN.C -- Displays "Hello, Windows 95!" in client area
                 (c) Charles Petzold, 1996
  ------------------------------------------------------------*/

#include <windows.h>

#include "resource.h"

#define MAXBUF 300

#define MAXFILTERS     10
#define MAXCUSTFILTER  MAXBUF
#define FILENAMESIZE   MAXBUF
#define FILETITLESIZE  MAXBUF
#define DLGTITLESIZE   MAXBUF
#define INITDIRSIZE    MAXBUF
#define DEFEXTSIZE     40
#define TEMPNAMESIZE   30

TCHAR szFileTitle[FILETITLESIZE]  ;
TCHAR szDlgTitle[DLGTITLESIZE]    ;
TCHAR szFileName[FILENAMESIZE]    ;
TCHAR szInitialDir[INITDIRSIZE]   ;
TCHAR szDefExt[DEFEXTSIZE]        ;
TCHAR szTempName[TEMPNAMESIZE]    ;

TCHAR szDrive[_MAX_DRIVE];
TCHAR szDir[_MAX_DIR];
TCHAR szFname[_MAX_FNAME];
TCHAR szExt[_MAX_EXT];

TCHAR szFilterInits[MAXFILTERS][30] ;
TCHAR szFilterString[MAXBUF] ;
LPTSTR lpszFilterString ;

TCHAR  szCustFiltInits[3][30] ;
TCHAR  szCustFilterString[MAXBUF] ;
LPTSTR lpszCustFilterString ;

HINSTANCE hInst;
HKEY hKey  = NULL;
DWORD dwFlags ;
OPENFILENAME file;

LRESULT CALLBACK WndProc (HWND, UINT, WPARAM, LPARAM) ;
void InitOpenStruct(HWND hwnd, LPOPENFILENAME po);
void InitCustFilterString(void);
void InitFilterString(void);

int WINAPI WinMain (HINSTANCE hInstance, HINSTANCE hPrevInstance,
                    PSTR szCmdLine, int iCmdShow)
{
	static char szAppName[] = "HelloWin" ;
	HWND        hwnd ;
	MSG         msg ;

	WNDCLASSEX  wndclass ;

	wndclass.cbSize        = sizeof (wndclass) ;
	wndclass.style         = CS_HREDRAW | CS_VREDRAW ;
	wndclass.lpfnWndProc   = WndProc ;
	wndclass.cbClsExtra    = 0 ;
	wndclass.cbWndExtra    = 0 ;
	wndclass.hInstance     = hInstance ;
	wndclass.hIcon         = LoadIcon (NULL, IDI_APPLICATION) ;
	wndclass.hCursor       = LoadCursor (NULL, IDC_ARROW) ;
	wndclass.hbrBackground = (HBRUSH) GetStockObject (WHITE_BRUSH) ;
	wndclass.lpszMenuName  = szAppName ;
	wndclass.lpszClassName = szAppName ;
	wndclass.hIconSm       = LoadIcon (NULL, IDI_APPLICATION) ;

	RegisterClassEx (&wndclass) ;

	hwnd = CreateWindow (szAppName,         // window class name
					"The Hello Program",     // window caption
					WS_OVERLAPPEDWINDOW,     // window style
					CW_USEDEFAULT,           // initial x position
					CW_USEDEFAULT,           // initial y position
                    CW_USEDEFAULT,           // initial x size
                    CW_USEDEFAULT,           // initial y size
                    NULL,                    // parent window handle
                    NULL,                    // window menu handle
                    hInstance,               // program instance handle
		            NULL) ;		             // creation parameters

	ShowWindow (hwnd, iCmdShow) ;
	UpdateWindow (hwnd) ;

	hInst = hInstance;

	while (GetMessage (&msg, NULL, 0, 0))
    {
		TranslateMessage (&msg) ;
		DispatchMessage (&msg) ;
	}
	return msg.wParam ;
}

LRESULT CALLBACK WndProc (HWND hwnd, UINT iMsg, WPARAM wParam, LPARAM lParam)
{
	HDC         hdc, tst;
	PAINTSTRUCT ps ;
	RECT        rect ;
	BOOL status;
	long lResult;
	char szTemp[10];

	switch (iMsg)
	{
		case WM_CREATE:
			InitOpenStruct(hwnd, &file);
			return 0;

		case WM_COMMAND:
			switch(LOWORD(wParam))
			{			
				case IDM_FILE_OPEN:					
					if((status=GetOpenFileName(&file)))
					{
						//MessageBox(hwnd, file.lpstrFile, "Test", MB_OK);
						_splitpath( file.lpstrFile, szDrive, szDir, szFname, szExt );
						lstrcpy(szInitialDir, szDrive);
						lstrcat(szInitialDir, szDir);
						file.lpstrInitialDir = szInitialDir;						
					}
					else
					{
						wsprintf(szTemp, "%ld", CommDlgExtendedError()) ;
						MessageBox(hwnd, szTemp, "Test", MB_OK);
					}

					break;
			}
			return 0;	   

		case WM_PAINT :
			tst = (HDC)wParam;	
			hdc = BeginPaint (hwnd, &ps) ;
			GetClientRect (hwnd, &rect) ;
			DrawText (hdc, "Hello, Windows 95!", -1, &rect,
						DT_SINGLELINE | DT_CENTER | DT_VCENTER) ;

			EndPaint (hwnd, &ps) ;
			return 0 ;

		case WM_DESTROY :
			lResult= RegSetValueEx(hKey, NULL, 0, REG_SZ,
									szInitialDir, sizeof(szInitialDir) );
			if(lResult!=ERROR_SUCCESS)
				MessageBox(hwnd, "Error in RegSetValueEx!", "Error", MB_OK|MB_ICONSTOP);		
			RegCloseKey(hKey);
			PostQuitMessage (0) ;
			return 0 ;
	}

	return DefWindowProc (hwnd, iMsg, wParam, lParam) ;
}


/************************************************************************


  Function: InitOpenStruct(HWND, LPOPENFILENAME)

  Purpose:

    Initializes the OPENFILENAME structure.  The structure is referenced
    via a pointer passed in as the second parameter so that we can pass
    any of the three OPENFILENAME structures into this function and
    Initialize them.

  Returns: Nothing.

  Comments:

    The szFilterInits and szCustFiltInits arrays are initialized to
    contain some default strings.  Eventually the strings in
    these arrays must be arranged one after the other with a null
    character between them and two null characters at the end:

    "Text files\0*.txt\0All files\0*.*\0\0"

************************************************************************/


void InitOpenStruct(HWND hwnd, LPOPENFILENAME po)
{
	int i = 0 ;
	long  lResult; 
	DWORD dwType, dwDisposition, cbData = sizeof(szInitialDir);

	SECURITY_ATTRIBUTES sa;

	sa.nLength              = sizeof(SECURITY_ATTRIBUTES);
	sa.bInheritHandle       = FALSE;
	sa.lpSecurityDescriptor = NULL;


	szFileName[0] = 0 ;
	szFileTitle[0] = 0 ;


    dwFlags = OFN_READONLY | OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST ;


	lResult= RegCreateKeyEx(HKEY_LOCAL_MACHINE, "Software\\Python\\PythonCore\\Cmif Path\\", 0,
							NULL, REG_OPTION_NON_VOLATILE,
							KEY_ALL_ACCESS, 
							&sa, &hKey, &dwDisposition );
	if(lResult!=ERROR_SUCCESS)
		MessageBox(hwnd, "Error in RegCreateKeyEx!", "Error", MB_OK|MB_ICONSTOP);		
	
	lstrcpy(szInitialDir, TEXT("c:\\")) ;
	if(dwDisposition==REG_OPENED_EXISTING_KEY)
	{
		lResult= RegQueryValueEx(hKey, NULL, 0,	&dwType, szInitialDir, &cbData );
		if(lResult!=ERROR_SUCCESS)
		{
			MessageBox(hwnd, "Error in RegQueryKeyEx!", "Error", MB_OK|MB_ICONSTOP);		
			lstrcpy(szInitialDir, TEXT("c:\\")) ;
		}
	}	

    lstrcpy(szDlgTitle, TEXT("Open Dialog Title")) ;
   
    lstrcpy(szDefExt, TEXT("rat")) ;
    lstrcpy(szTempName, TEXT("opentemp1")) ;

    lstrcpy(&szFilterInits[0][0], TEXT("CMIF Documents (*.cmif)")) ;
    lstrcpy(&szFilterInits[1][0], TEXT("*.cmif")) ;
    szFilterInits[2][0] = (TCHAR) 0 ;


    lstrcpy(&szCustFiltInits[0][0], TEXT("Last Filter Used")) ;
    lstrcpy(&szCustFiltInits[1][0], TEXT("*.lst")) ;
    szCustFiltInits[2][0] = (TCHAR) 0 ;


   /*

      These two functions will create "strings" in the applications
      data area that are in the form

      "Filter Description"\0
      "Filter"\0
      "Filter Description"\0
      "Filter"\0
      ..
      ..
      \0\0

      The filters must be in this form in order that the common dialogs
      interpret it correctly...
   */

    InitFilterString() ;

    InitCustFilterString() ;

    po->lStructSize          = sizeof(OPENFILENAME) ;
    po->hwndOwner            = hwnd ;
    po->hInstance            = hInst ;
    (LPTSTR) po->lpstrFilter = lpszFilterString ;
    po->lpstrCustomFilter    = NULL ;
    po->nMaxCustFilter       = MAXCUSTFILTER ;
    po->nFilterIndex         = 1L ;
    po->lpstrFile            = szFileName ;
    po->nMaxFile             = FILENAMESIZE ;
    po->lpstrFileTitle       = szFileTitle ;
    po->nMaxFileTitle        = FILETITLESIZE ;
    po->lpstrInitialDir      = szInitialDir ;
    (LPTSTR) po->lpstrTitle  = szDlgTitle ;
    po->Flags                = dwFlags ;
    po->nFileOffset          = 0 ;
    po->nFileExtension       = 0 ;
    (LPTSTR) po->lpstrDefExt = szDefExt;
    po->lCustData            = 0L ;
    po->lpfnHook             = NULL ;
    (LPTSTR) po->lpTemplateName  = szTempName ;

    return ;
}

/************************************************************************


  Function: InitCustFiltString(void)


  Purpose:

    This function will create a "string" in memory in the form that the
    GetOpenFileName() function will expect for a custom filter.

  Returns: Nothing.

  Comments:

    The szFilterInits and szCustFiltInits arrays are initialized to
    contain some default strings.  Eventually the strings in
    these arrays must be arranged one after the other with a null
    character between them and two null characters at the end:

    "Text files\0*.txt\0All files\0*.*\0\0"

    This program initializes these strings, but they do not need to be
    initialized.  The GetOpenFileName() functiion will write a filter
    into this memory area if the user types a new filter into the
    "FileName" box and returns by clicking the OK button (indicating that
    a file matching that filter was found).

************************************************************************/


void InitCustFilterString(void)
{
  int i ;
  LPTSTR lpStr = szCustFilterString ;
  int nInc = 0 ;

  for (i=0; i<MAXBUF; i++)
    szCustFilterString[i] = 0 ;

  i = 0 ;

  for(i=0; i<2; i++)  //only two for the custom filter
  {
    lstrcpy(lpStr, &szCustFiltInits[i][0]) ;
    nInc+=lstrlen(&szCustFiltInits[i][0]) + 1 ;
    lpStr = &szCustFilterString[nInc] ;
  }

  szCustFilterString[nInc] = (TCHAR) 0 ;

  lpszCustFilterString = szCustFilterString ;

  return ;
}

/************************************************************************


  Function: InitFilterString(void)


  Purpose:

    This function will create a "string" in memory in the form that the
    GetOpenFileName() function will expect for the filters it fills into
    the "List Files of Type" combo box.

  Returns: Nothing.

  Comments:

    The szFilterInits and szCustFiltInits arrays are initialized to
    contain some default strings.  Eventually the strings in
    these arrays must be arranged one after the other with a null
    character between them and two null characters at the end:

    "Text files\0*.txt\0All files\0*.*\0\0"

************************************************************************/


void InitFilterString(void)
{
  int i ;
  int nInc = 0 ;
  LPTSTR lpStr = szFilterString ;


  /* First, zero out this memory just for the sake of sanity */

  for (i=0; i<MAXBUF; i++)
    szFilterString[i] = 0 ;


  /* Now, for each string in the szFilterInits array, concatenate it to
     the last one right after the last one's null terminator */

  i = 0 ;

  while (szFilterInits[i][0] != (TCHAR) 0)
  {
    lstrcpy(lpStr, &szFilterInits[i][0]) ;
    nInc+=lstrlen(&szFilterInits[i][0]) + 1 ;   //1 past null term...
    lpStr = &szFilterString[nInc] ;
    i++ ;
  }

  szFilterString[nInc] = (TCHAR) 0 ;  //double terminator


  /* Set the lpszFilterString to point to the memory we just filled in
     with the filters because lpszFilterString is what is in
     OPENFILENAME->lpstrFilter */

  lpszFilterString = szFilterString ;

  return ;
}
