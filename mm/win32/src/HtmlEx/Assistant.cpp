// -*- Mode: C++; tab-width: 4 -*-
// $Id$

#include "cmifex.h"

static PyObject *CmifExError;
char cmifClass[100]="";

PyIMPORT CWnd *GetWndPtr(PyObject *);

#ifdef __cplusplus
extern "C" {
#endif
//***************************
//Things to do:
//	- built a LinkList with the used windows so as to preserve MemoryManagement
//	- use cmifClass in a more clever way to cover every case
//***************************

static PyObject* py_example_CreateWindow(PyObject *self, PyObject *args)
{
	char *wndName;
	PyObject *testOb = Py_None;
	CWnd *newWnd, *mainWnd;
	PyCWnd *testWnd;
	int x=100, y=100, nWidth=400, nHeigth=400;
	
	newWnd = new CWnd;

	if(!PyArg_ParseTuple(args, "s", &wndName))
	{
		Py_INCREF(Py_None);
		return Py_None;return NULL;
	}

	mainWnd = AfxGetMainWnd();
	
	if(cmifClass[0]==0)
		strcpy(cmifClass, AfxRegisterWndClass(CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS, LoadCursor (NULL, IDC_ARROW), (HBRUSH) GetStockObject (WHITE_BRUSH), LoadIcon(NULL, MAKEINTRESOURCE(IDR_PYTHON))));
		
	if(newWnd->CreateEx(WS_EX_CLIENTEDGE,
						cmifClass, wndName,
						WS_OVERLAPPEDWINDOW| WS_VISIBLE,
						x, y, nWidth, nHeigth,
						mainWnd->m_hWnd,
						NULL))
		TRACE("CmifEx CreateWindow OK!\n");
	else
	{
		TRACE("CmifEx CreateWindow FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	testOb = testWnd->GetGoodRet();

	return Py_BuildValue("O", testOb);
}

static PyObject* py_example_CreateChildWindow(PyObject *self, PyObject *args)
{
	char *wndName;
	PyObject *testOb = Py_None, *ob = Py_None;
	CWnd *newWnd, *parentWnd;
	PyCWnd *testWnd;
	int x=150, y=150, nWidth=100, nHeigth=100;
	
	if(!PyArg_ParseTuple(args, "sO", &wndName, &ob))
	{
		Py_INCREF(Py_None);
		return Py_None;return NULL;
	}

	newWnd = new CWnd;
	parentWnd = GetWndPtr( ob );

	if(newWnd->CreateEx(WS_EX_CONTROLPARENT|WS_EX_CLIENTEDGE,
						cmifClass, wndName,
						WS_CHILD | WS_VISIBLE,
						x, y, nWidth, nHeigth,
						parentWnd->m_hWnd,
						NULL))
		TRACE("CmifEx CreateChildWindow OK!\n");
	else
	{
		TRACE("CmifEx CreateChildWindow FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	testOb = testWnd->GetGoodRet();

	return Py_BuildValue("O", testOb);
}

static PyMethodDef CmifExMethods[] = 
{
	{ "CreateWindow", py_example_CreateWindow, 1},
	{ "CreateChildWindow", py_example_CreateChildWindow, 1},
	{ NULL, NULL }
};

PyEXPORT 
void initcmifex()
{
	PyObject *m, *d;
	m = Py_InitModule("cmifex", CmifExMethods);
	d = PyModule_GetDict(m);
	CmifExError = PyString_FromString("cmifex.error");
	PyDict_SetItemString(d, "error", CmifExError);
}

#ifdef __cplusplus
}
#endif
