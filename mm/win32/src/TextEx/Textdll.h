#include <windows.h>
//#include <afxwin.h>
//#include <afxext.h>
#include <mmsystem.h>

#ifndef _TXTDLL_
#define TXTAPP __declspec(dllimport)
#else 
#define TXTAPP __declspec(dllexport)
#endif


TXTAPP char* readtext(char* filename);
