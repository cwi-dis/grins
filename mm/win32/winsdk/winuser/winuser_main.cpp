
/*************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include "winuser_main.h"

#include "utils.h"


#include <shellapi.h>

PyObject* Winuser_MessageLoop(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	MSG msg;
	Py_BEGIN_ALLOW_THREADS
	while(::GetMessage(&msg, NULL, 0, 0)) 
		{
		TranslateMessage(&msg);
		DispatchMessage(&msg);
		}
	Py_END_ALLOW_THREADS
	return none();
}

PyObject* Winuser_PostQuitMessage(PyObject *self, PyObject *args)
{
	int nExitCode = 0;
	if (!PyArg_ParseTuple(args, "|i"))
		return NULL;
	PostQuitMessage(nExitCode);
	return none();
}


PyObject* Winuser_MessageBox(PyObject *self, PyObject *args)
{
	char *text;
	char *caption = "GRiNS Player";
	UINT type = MB_OK;
	if (!PyArg_ParseTuple(args, "s|si", &text, &caption, &type))
		return NULL;
	int res;
	Py_BEGIN_ALLOW_THREADS
	res = MessageBox(NULL, TextPtr(text), TextPtr(caption), type);
	Py_END_ALLOW_THREADS
	return Py_BuildValue("i", res);
}


PyObject* Winuser_GetSystemMetrics(PyObject *self, PyObject *args)
{
	int nIndex;
	if (!PyArg_ParseTuple(args, "i", &nIndex))
		return NULL;
	int res = GetSystemMetrics(nIndex);
	if(res == 0){
		seterror("GetSystemMetrics", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", res);
}

PyObject* Winuser_GetSysColor(PyObject *self, PyObject *args)
{
	int nIndex;
	if (!PyArg_ParseTuple(args, "i", &nIndex))
		return NULL;
	DWORD res = GetSysColor(nIndex);
	return Py_BuildValue("i", res);
}

PyObject* Winuser_GetDC(PyObject *self, PyObject *args)
{
	HWND hWnd = NULL;
	if (!PyArg_ParseTuple(args, "|i", &hWnd))
		return NULL;
	HDC hdc = GetDC(hWnd);
	if(hdc == 0){
		seterror("GetDC", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", hdc);
}

PyObject* Winuser_LoadStandardCursor(PyObject *self, PyObject *args)
{
	int nIndex;
	if (!PyArg_ParseTuple(args, "i", &nIndex))
		return NULL;
	HCURSOR hCursor = LoadCursor(NULL, MAKEINTRESOURCE(nIndex));
	if(hCursor == NULL){
		seterror("LoadStandardCursor", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", hCursor);
}

PyObject* Winuser_LoadCursor(PyObject *self, PyObject *args)
{
	HMODULE hModule;
	int nIndex;
	if (!PyArg_ParseTuple(args, "ii", &hModule, &nIndex))
		return NULL;
	HCURSOR hCursor = LoadCursor(hModule, MAKEINTRESOURCE(nIndex));
	if(hCursor == NULL){
		seterror("LoadCursor", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", hCursor);
}

PyObject* Winuser_ShellExecute(PyObject *self, PyObject *args)
	{
	HWND hwnd;
	char *op, *file, *params, *dir;
	int show;
	if (!PyArg_ParseTuple(args, "izszzi", &hwnd, &op, &file, &params, &dir, &show))
		return NULL;
#ifdef _WIN32_WCE
	return Py_BuildValue("is", 32, "ShellExecute not supported under win CE");
#else
	if (dir==NULL) dir="";
	HINSTANCE rc;
	Py_BEGIN_ALLOW_THREADS
	rc = ShellExecute(hwnd, TextPtr(op), TextPtr(file), TextPtr(params), TextPtr(dir), show);
	Py_END_ALLOW_THREADS
	TCHAR szMsg[512] = TEXT("OK");
	if ((rc) <= (HINSTANCE)32) 
		{
		BOOL bHaveMessage = ::FormatMessage(FORMAT_MESSAGE_FROM_SYSTEM, NULL, (DWORD)rc, 0, szMsg, sizeof(szMsg), NULL )>0;
		if (!bHaveMessage)
			lstrcpy(szMsg, TEXT("Error. No error message is available"));
		}
	return Py_BuildValue("is",rc, szMsg);
#endif
	}
