
#include "registryex.h"
#include "winreg.h"

#define MAXBUF 300

#define MAXFILTERS     10
#define MAXCUSTFILTER  MAXBUF
#define FILENAMESIZE   MAXBUF
#define FILETITLESIZE  MAXBUF
#define DLGTITLESIZE   MAXBUF
#define INITDIRSIZE    MAXBUF
#define DEFEXTSIZE     40
#define TEMPNAMESIZE   30

TCHAR InitDir[MAXBUF];
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

HKEY hKey  = NULL;
DWORD dwFlags ;
long lResult;

DWORD dwType, dwDisposition, cbData = sizeof(szInitialDir);
SECURITY_ATTRIBUTES sa;
LPOPENFILENAME po;



static PyObject *RegistryExError;


PyIMPORT CWnd *GetWndPtr(PyObject *);



#ifdef __cplusplus
extern "C" {
#endif


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


void ReadReg()
{
	long  lResult; 
	LPBYTE tmp;
	DWORD dwType, dwDisposition, cbData = sizeof(szInitialDir);
	SECURITY_ATTRIBUTES sa;

	sa.nLength              = sizeof(SECURITY_ATTRIBUTES);
	sa.bInheritHandle       = FALSE;
	sa.lpSecurityDescriptor = NULL;


	szFileName[0] = 0 ;
	szFileTitle[0] = 0 ;


    dwFlags = OFN_READONLY | OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST ;


	lResult= RegCreateKeyEx(HKEY_LOCAL_MACHINE, /*"Software\\Python\\PythonCore\\Cmif Path\\"*/"Software\\Chameleon\\CmifDoc\\", 0,
							NULL, REG_OPTION_NON_VOLATILE,
							KEY_ALL_ACCESS, 
							&sa, &hKey, &dwDisposition );
	if(lResult!=ERROR_SUCCESS)
	{
		MessageBox(NULL, "Error in RegCreateKeyEx!", "Error", MB_OK|MB_ICONSTOP);		
		TRACE("Error in RegCreateKeyEx!\n");
		lstrcpy(szInitialDir, TEXT("c:\\")) ;
	}

	if(dwDisposition==REG_OPENED_EXISTING_KEY)
	{
		lResult= RegQueryValueEx(hKey, "Software\\Chameleon\\CmifDoc\\", NULL, &dwType, tmp, &cbData);
		if(lResult!=ERROR_SUCCESS)
		{
			//MessageBox(NULL, "Error in RegQueryKeyEx!", "Error", MB_OK|MB_ICONSTOP);		
			TRACE("Error in RegQueryKeyEx!\n");
			lstrcpy(szInitialDir, TEXT("c:\\")) ;
		}
	}
	strcpy ((char *)tmp, szInitialDir);
	MessageBox(NULL, (LPCTSTR)tmp, "Inside ReadReg", MB_OK|MB_ICONSTOP);		
	MessageBox(NULL, szInitialDir, "szInitialDir", MB_OK|MB_ICONSTOP);		
	
}
	
	

void InitOpenStruct(LPOPENFILENAME po)
{
	int i = 0 ;
		
		
	lstrcpy(szDlgTitle, TEXT("Open CMIF Presentation file")) ;
   
    lstrcpy(szDefExt, TEXT("rat")) ;
    lstrcpy(szTempName, TEXT("opentemp1")) ;

    lstrcpy(&szFilterInits[0][0], TEXT("CMIF Documents (*.cmif)")) ;
    lstrcpy(&szFilterInits[1][0], TEXT("*.cmif")) ;
    szFilterInits[2][0] = (TCHAR) 0 ;


    lstrcpy(&szCustFiltInits[0][0], TEXT("Last Filter Used")) ;
    lstrcpy(&szCustFiltInits[1][0], TEXT("*.lst")) ;
    szCustFiltInits[2][0] = (TCHAR) 0 ;


   
    InitFilterString() ;

    InitCustFilterString() ;

    po->lStructSize          = sizeof(OPENFILENAME) ;
    po->hwndOwner            = NULL ;
    po->hInstance            = AfxGetInstanceHandle();
    po->lpstrFilter = lpszFilterString ;
    po->lpstrCustomFilter    = NULL ;
    po->nMaxCustFilter       = MAXCUSTFILTER ;
    po->nFilterIndex         = 1L ;
    po->lpstrFile            = szFileName ;
    po->nMaxFile             = FILENAMESIZE ;
    po->lpstrFileTitle       = szFileTitle ;
    po->nMaxFileTitle        = FILETITLESIZE ;
	//po->lpstrInitialDir      = szInitialDir ;
	strcpy(szInitialDir, po->lpstrInitialDir);
    po->lpstrTitle  = szDlgTitle ;
    po->Flags                = dwFlags ;
    po->nFileOffset          = 0 ;
    po->nFileExtension       = 0 ;
    po->lpstrDefExt = szDefExt;
    po->lCustData            = 0L ;
    po->lpfnHook             = NULL ;
    po->lpTemplateName  = szTempName ;

    return ;
}


static PyObject*  py_reg_open(PyObject *args)
{
	OPENFILENAME file;

	//ReadReg();

	InitOpenStruct(&file);
	
	
	BOOL b = GetOpenFileName(&file);

	if (b)
	{
		_splitpath( file.lpstrFile, szDrive, szDir, szFname, szExt );
		lstrcpy(szInitialDir, szDrive);
		lstrcat(szInitialDir, szDir);
		file.lpstrInitialDir = szInitialDir;						
	}

			
	
	
	return Py_BuildValue("s", file.lpstrFile);
}



static PyObject*  py_reg_openfile(PyObject *args)
{
	
	OPENFILENAME file;

	InitOpenStruct(&file);
	
	
	BOOL b = GetOpenFileName(&file);

	if (b)
	{
		_splitpath( file.lpstrFile, szDrive, szDir, szFname, szExt );
		lstrcpy(szInitialDir, szDrive);
		lstrcat(szInitialDir, szDir);
		file.lpstrInitialDir = szInitialDir;						
	}

			
	
	
	return Py_BuildValue("s", file.lpstrFile);
}


static PyObject*  py_reg_read(PyObject *args)
{
	ReadReg();
	return Py_BuildValue("s", szInitialDir);
}


static PyObject* py_reg_close(PyObject *args)
{
	BOOL b = TRUE;
	
	lResult= RegSetValueEx(hKey, NULL, 0, REG_SZ,
									(unsigned char*)szInitialDir, sizeof(szInitialDir) );
	if(lResult!=ERROR_SUCCESS)
	{
			b = FALSE;
			//MessageBox(NULL, "Error in RegSetValueEx!", "Error", MB_OK|MB_ICONSTOP);		
			TRACE("Error in RegSetValueEx!\n");
	}
	RegCloseKey(hKey);
		
	
	return Py_BuildValue("s", szInitialDir);
}


static PyObject* py_reg_virtual_FileDialog(PyObject *self,PyObject *args)
{
		
	char res[256];
	CString strPath, strurl;
	char* FileName;


	if(!PyArg_ParseTuple(args, "s",  &FileName))
	{
		Py_INCREF(Py_None);
		AfxMessageBox("Error Receiving CMIF presentation String", MB_OK);
		return Py_None;
		return NULL;
	
	}


	static char filter[] = "HTM Files (*.HTM)|*.HTM|All Files (*.*)|*.*||";
	CFileDialog Dlg(TRUE, NULL, NULL, OFN_HIDEREADONLY|OFN_OVERWRITEPROMPT, 
					filter, NULL);
	Dlg.m_ofn.lpstrTitle = "Open File URL";
	
	AfxMessageBox("Before Copy File Name", MB_OK);
	strcpy(Dlg.m_ofn.lpstrFile, FileName);
	AfxMessageBox("After Copy File Name", MB_OK);

	strPath = Dlg.GetPathName();

	UINT length = strPath.GetLength();
	char c = strPath.GetAt(2);
	/*for (UINT i=0; i<length; i++)
	{
		if (strPath.GetAt(i) == ((TCHAR)'\\'))
			strPath.SetAt(i, '/');
	}
	strPath.SetAt(1, '|');
	TRACE("Path variable is now %s\n", strPath);*/
	
	strcpy(res, strPath);

	return Py_BuildValue("s", res);
}


static PyMethodDef RegistryExMethods[] = 
{
	{ "init", (PyCFunction)py_reg_open, 1},
	{ "close",(PyCFunction)py_reg_close, 1},
	{ "read",(PyCFunction)py_reg_read, 1},
	{ "openfile",(PyCFunction)py_reg_openfile, 1},
	{ "convert_arg",(PyCFunction)py_reg_virtual_FileDialog, 1},
	{ NULL, NULL }
};


PyEXPORT 
void initregistryex()
{
	PyObject *m, *d;
	m = Py_InitModule("registryex", RegistryExMethods);
	d = PyModule_GetDict(m);
	RegistryExError = PyString_FromString("registryex.error");
	PyDict_SetItemString(d, "error", RegistryExError);
}

#ifdef __cplusplus
}
#endif


