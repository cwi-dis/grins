// -*- Mode: C++; tab-width: 4 -*-
// $Id$
//
#include "timerex.h"

static PyObject *timerexError;
char cmifClass[100]="";
char dbgmess[100]="";

PyIMPORT CWnd *GetWndPtr(PyObject *);

#ifdef __cplusplus
extern "C" {
#endif

//***************************
//Things to do:
//	- built a LinkList with the used windows so as to preserve MemoryManagement
//	- use cmifClass in a more clever way to cover every case
//***************************

#pragma data_seg("SHARED")
PyObject *testOb = Py_None;
PyCWnd *testWnd=NULL;
CWnd *newWnd, *mainWnd;
UWORD timerID = 100;
#pragma data_seg()

static PyObject* py_timerex_CreateWindow(PyObject *self, PyObject *args)
{
	if(testOb!=Py_None)
		return Py_BuildValue("O", testOb);
	
	newWnd = new CWnd;

	if(!PyArg_ParseTuple(args, ""))
		return Py_BuildValue("i", 0);

	mainWnd = AfxGetMainWnd();
	
	if(cmifClass[0]==0)
		strcpy(cmifClass, AfxRegisterWndClass( CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS, LoadCursor (NULL, IDC_ARROW), (HBRUSH) GetStockObject (WHITE_BRUSH), NULL));
		
	if(newWnd->CreateEx(WS_EX_CLIENTEDGE,
						cmifClass, "Timer",
						WS_OVERLAPPEDWINDOW,
						0, 0, 0, 0,
						mainWnd->m_hWnd,
						NULL))
		TRACE("timerex CreateWindow OK!\n");
	else
	{
		TRACE("timerex CreateWindow FALSE!\n");
		return Py_BuildValue("O", testOb);
	}
	
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	testOb = testWnd->GetGoodRet();

	return Py_BuildValue("O", testOb);
}


static PyObject* py_timerex_SetTimer(PyObject *self, PyObject *args)
{
	UWORD elapse, id;
	
	if(!PyArg_ParseTuple(args, "i", &elapse))
		return Py_BuildValue("i", -1);

	if(newWnd==NULL)
		return Py_BuildValue("i", -1);

	id = newWnd->SetTimer(timerID, elapse, NULL);
	if(++timerID>20000)
		timerID = 100;

	return Py_BuildValue("i", id);
}

static PyObject* py_timerex_KillTimer(PyObject *self, PyObject *args)
{
	BOOL res;
	UWORD id;

	if(!PyArg_ParseTuple(args, "i", &id))
		return Py_BuildValue("i", -1);

	if(newWnd==NULL)
		return Py_BuildValue("i", -1);

	res = newWnd->KillTimer(id);

	return Py_BuildValue("i", (int)res);
}

static PyMethodDef timerexMethods[] = 
{
	{ "CreateTimerWindow", py_timerex_CreateWindow, 1},
	{ "SetTimer", py_timerex_SetTimer, 1},
	{ "KillTimer", py_timerex_KillTimer, 1},
	{ NULL, NULL }
};

PyEXPORT 
void inittimerex()
{
	PyObject *m, *d;
	m = Py_InitModule("timerex", timerexMethods);
	d = PyModule_GetDict(m);
	timerexError = PyString_FromString("timerex.error");
	PyDict_SetItemString(d, "error", timerexError);
}

#ifdef __cplusplus
}
#endif
