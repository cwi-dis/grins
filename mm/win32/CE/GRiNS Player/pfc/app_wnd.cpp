#include "Python.h"

#include <windows.h>

#include "pyinterface.h"

#include "app_wnd.h"
#include "charconv.h"


/////////////////////////////////////////
std::map<HWND, PyWnd*> PyWnd::wnds;


///////////////////////////////////////////
// module

#define ASSERT_ISWINDOW(wnd) if((wnd) == NULL || !IsWindow(wnd)) {seterror("Not a window"); return NULL;}

static PyObject* PyWnd_Detach(PyWnd *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HWND hWnd = NULL;
	std::map<HWND, PyWnd*>::iterator wit = PyWnd::wnds.find(self->m_hWnd);
	if(wit != PyWnd::wnds.end())
		{
		PyWnd *pywnd = (*wit).second;
		PyWnd::wnds.erase(wit);
		hWnd = pywnd->m_hWnd;
		pywnd->m_hWnd = NULL;
		// remove hooks since the object will not be deallocated
		if(pywnd->m_phooks != NULL)
			{
			std::map<UINT, PyObject*>::iterator it;
			for(it = pywnd->m_phooks->begin();it!=pywnd->m_phooks->end();it++)
				Py_XDECREF((*it).second);
			delete pywnd->m_phooks;
			pywnd->m_phooks = NULL;
			}
		Py_DECREF(pywnd); 
		}
	return Py_BuildValue("i", hWnd);
	}

static PyObject* PyWnd_ShowWindow(PyWnd *self, PyObject *args)
	{
	int nCmdShow = SW_SHOW;
	if (!PyArg_ParseTuple(args, "|i", &nCmdShow))
		return NULL;
	ASSERT_ISWINDOW(self->m_hWnd)
	BOOL res = ShowWindow(self->m_hWnd, nCmdShow);
	return Py_BuildValue("i", int(res));
	}

static PyObject* PyWnd_UpdateWindow(PyWnd *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	ASSERT_ISWINDOW(self->m_hWnd)
	BOOL res = UpdateWindow(self->m_hWnd);
	if(!res){
		seterror("UpdateWindow", GetLastError());
		return NULL;
		}
	return none();
	}

static PyObject* PyWnd_DestroyWindow(PyWnd *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	if(!IsWindow(self->m_hWnd))
		{
		seterror("DestroyWindow against not a window");
		return NULL;
		}
	
	// DestroyWindow sends (WM_NCDESTROY, WM_DESTROY)
	BOOL res;
	Py_BEGIN_ALLOW_THREADS
	res = ::DestroyWindow(self->m_hWnd);
	Py_END_ALLOW_THREADS
	if(!res){
		seterror("DestroyWindow", GetLastError());
		return NULL;
		}
	return none();
	}

static PyObject* PyWnd_InvalidateRect(PyWnd *self, PyObject *args)
{
	PyObject *pyrc = NULL; 
	BOOL bErase = TRUE;
	if (!PyArg_ParseTuple(args, "|Oi", &pyrc, &bErase))
		return NULL;
	RECT rc, *prc = NULL;
	if(pyrc != NULL && pyrc != Py_None)
		{
		if(!PyArg_ParseTuple(pyrc, "iiii", &rc.left, &rc.top, &rc.right, &rc.bottom)) 
			{
			seterror("first argument should be a rect tuple or None");
			return NULL;
			}
		prc = &rc;
		}
	ASSERT_ISWINDOW(self->m_hWnd)
	BOOL res = InvalidateRect(self->m_hWnd, prc, bErase);
	if(!res){
		seterror("InvalidateRect", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject* PyWnd_GetClientRect(PyWnd *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	ASSERT_ISWINDOW(self->m_hWnd)
	RECT rc;
	BOOL res = GetClientRect(self->m_hWnd, &rc);
	if(!res){
		seterror("GetClientRect", GetLastError());
		return NULL;
		}
	return Py_BuildValue("iiii", rc.left, rc.top, rc.right, rc.bottom);
}

static PyObject* PyWnd_RedrawWindow(PyWnd *self, PyObject *args)
{
	PyObject *pyrc;	      // update rectangle
	HRGN hrgn;            // handle to update region
	UINT flags;           // array of redraw flags
	if (!PyArg_ParseTuple(args, "Oii", &pyrc, &hrgn, &flags))
		return NULL;
	ASSERT_ISWINDOW(self->m_hWnd)
	RECT rc, *prc = NULL;
	if(pyrc != Py_None)
		{
		if(!PyArg_ParseTuple(pyrc, "iiii", &rc.left, &rc.top, &rc.right, &rc.bottom)) 
			{
			seterror("first argument should be a rect tuple or None");
			return NULL;
			}
		prc = &rc;
		}
#ifdef _WIN32_WCE
	return none();
#else
	BOOL res = RedrawWindow(self->m_hWnd, prc, hrgn, flags);
	if(!res){
		seterror("RedrawWindow", GetLastError());
		return NULL;
		}
	return none();
#endif
}

static PyObject* PyWnd_GetDC(PyWnd *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	ASSERT_ISWINDOW(self->m_hWnd)
	HDC hdc = GetDC(self->m_hWnd);
	if(hdc == 0){
		seterror("GetDC", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", hdc);
}

static PyObject* PyWnd_ReleaseDC(PyWnd *self, PyObject *args)
{
	HDC hdc;
	if (!PyArg_ParseTuple(args, "i", &hdc))
		return NULL;
	ASSERT_ISWINDOW(self->m_hWnd)
	int res = ::ReleaseDC(self->m_hWnd, hdc);
	if(res == 0)
		{
		seterror("ReleaseDC failed");
		return NULL;
		}
	return none();
}

static PyObject* PyWnd_BeginPaint(PyWnd *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	ASSERT_ISWINDOW(self->m_hWnd)
	
	PAINTSTRUCT ps;
	HDC hdc = BeginPaint(self->m_hWnd, &ps);
	PyObject *obRet = Py_BuildValue("(ii(iiii)iis#)",
		ps.hdc,
		ps.fErase,
		ps.rcPaint.left, ps.rcPaint.top, ps.rcPaint.right, ps.rcPaint.bottom,
		ps.fRestore,
		ps.fIncUpdate,
		ps.rgbReserved, sizeof(ps.rgbReserved));
	return obRet;
}

static PyObject* PyWnd_EndPaint(PyWnd *self, PyObject *args)
{
	PAINTSTRUCT ps;
	PyObject *obString;
	if (!PyArg_ParseTuple(args, "(ii(iiii)iiO)",
		&ps.hdc,
		&ps.fErase,
		&ps.rcPaint.left, &ps.rcPaint.top, &ps.rcPaint.right, &ps.rcPaint.bottom,
		&ps.fRestore,
		&ps.fIncUpdate,
		&obString))
		return NULL;
	ASSERT_ISWINDOW(self->m_hWnd)
	if (!PyString_Check(obString) || PyString_Size(obString) != sizeof(ps.rgbReserved))
		{
		seterror("Invalid paintstruct");
		return NULL;
		}
	memcpy(ps.rgbReserved, PyString_AsString(obString), sizeof(ps.rgbReserved));
	EndPaint(self->m_hWnd, &ps);
	return none();
}


static PyObject* PyWnd_GetSafeHwnd(PyWnd *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	if(!IsWindow(self->m_hWnd))
		return Py_BuildValue("i", 0);
	return Py_BuildValue("i", self->m_hWnd);
}

static PyObject* PyWnd_IsWindow(PyWnd *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, "")) return NULL;
	return Py_BuildValue("i", IsWindow(self->m_hWnd));
}

static PyObject* PyWnd_PostMessage(PyWnd *self, PyObject *args)
{
	UINT message;
	WPARAM wParam = 0;
	LPARAM lParam = 0;
	if (!PyArg_ParseTuple(args, "i|ii", &message, &wParam, &lParam))
		return NULL;
	BOOL res = ::PostMessage(self->m_hWnd, message, wParam, lParam);
	if(!res){
		seterror("PostMessage", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject* PyWnd_SendMessage(PyWnd *self, PyObject *args)
{
	UINT message;
	WPARAM wParam = 0;
	LPARAM lParam = 0;
	if (!PyArg_ParseTuple(args, "i|ii", &message, &wParam, &lParam))
		return NULL;
	long rc = ::SendMessage(self->m_hWnd, message, wParam, lParam);
	return Py_BuildValue("l",rc);
}

static PyObject* PyWnd_HookMessage(PyWnd *self, PyObject *args)
{
	PyObject *method;
	UINT message;
	if (!PyArg_ParseTuple(args,"Oi",&method, &message))
		return NULL;
	if (method!=Py_None && !PyCallable_Check(method))
		{
		seterror("The first parameter must be a callable object");
		return NULL;
		}
	if(self->m_phooks == NULL)
		{
		seterror("Cannot hook message for foreign windows");
		return NULL;
		}
	ASSERT_ISWINDOW(self->m_hWnd)

	// find previous
	std::map<UINT, PyObject*>::iterator it = self->m_phooks->find(message);
	PyObject *prevMethod = NULL;
	if(it != self->m_phooks->end())
		{
		prevMethod = (*it).second;
		self->m_phooks->erase(it);
		}

	// add new
	if (method!=Py_None) 
		{
		Py_INCREF(method);
		(*self->m_phooks)[message] = method;
		}
	Py_XDECREF(prevMethod);
	return none();
}

static PyObject* PyWnd_MessageBox(PyWnd *self, PyObject *args)
{
	char *text;
	char *caption;
	UINT type = MB_OK;
	if (!PyArg_ParseTuple(args, "ss|i", &text, &caption, &type))
		return NULL;
	int res;
	Py_BEGIN_ALLOW_THREADS
	res = MessageBox(self->m_hWnd, TextPtr(text), TextPtr(caption), type);
	Py_END_ALLOW_THREADS
	return Py_BuildValue("i", res);
}

static PyObject* PyWnd_DrawMenuBar(PyWnd *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	ASSERT_ISWINDOW(self->m_hWnd)
	BOOL res = DrawMenuBar(self->m_hWnd);
	if(!res){
		seterror("DrawMenuBar", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject* PyWnd_SetClassLong(PyWnd *self, PyObject *args)
	{
	int nIndex;
	LONG dwNewLong;
	if (!PyArg_ParseTuple (args, "il",&nIndex,&dwNewLong))
		return NULL;
	ASSERT_ISWINDOW(self->m_hWnd)
	DWORD dwOldLong = SetClassLong(self->m_hWnd, nIndex, dwNewLong);
	return Py_BuildValue("l",dwOldLong);
	}
 
static PyObject* PyWnd_SetWindowLong(PyWnd *self, PyObject *args)
	{
	int nIndex;
	LONG newLong;
	if (!PyArg_ParseTuple (args, "il",&nIndex,&newLong))
		return NULL;
	ASSERT_ISWINDOW(self->m_hWnd)
	LONG oldLong=::SetWindowLong(self->m_hWnd, nIndex, newLong);
	return Py_BuildValue("l",oldLong);
	}

static PyObject* PyWnd_GetWindowLong(PyWnd *self, PyObject *args)
	{
	int nIndex;
	if (!PyArg_ParseTuple (args, "i", &nIndex))
		return NULL;
	ASSERT_ISWINDOW(self->m_hWnd)
	LONG val = ::GetWindowLong(self->m_hWnd, nIndex);
	return Py_BuildValue("l", val);
	}
 
static PyObject* PyWnd_SetWindowPos(PyWnd *self, PyObject *args)
{
	HWND insertAfter;
	int x,y,cx,cy;
	int flags;
	if (!PyArg_ParseTuple(args,"i(iiii)i",
		        (int*)(&insertAfter), &x, &y, &cx, &cy, &flags))
		return NULL;
	ASSERT_ISWINDOW(self->m_hWnd)
	SetWindowPos(self->m_hWnd, insertAfter, x, y, cx, cy, flags);
	return none();
}

static PyObject* PyWnd_MoveWindow(PyWnd *self, PyObject *args)
{
	int x,y,cx,cy;
	BOOL bRepaint = TRUE;
	if (!PyArg_ParseTuple(args,"i(iiii)|i", &x, &y, &cx, &cy, &bRepaint))
		return NULL;
	ASSERT_ISWINDOW(self->m_hWnd)
	MoveWindow(self->m_hWnd, x, y, cx, cy, bRepaint);
	return none();
}

static PyObject* PyWnd_SetTimer(PyWnd *self, PyObject *args)
	{
	UINT nIDEvent, nElapse;
	if (!PyArg_ParseTuple(args, "ii",&nIDEvent,&nElapse))
		return NULL;
	ASSERT_ISWINDOW(self->m_hWnd)
	UINT id = SetTimer(self->m_hWnd, nIDEvent, nElapse, NULL);
	if(id==0){
		seterror("SetTimer", GetLastError());
		return NULL;
		}	
	return Py_BuildValue("i", id);
	}

static PyObject* PyWnd_KillTimer(PyWnd *self, PyObject *args)
	{
	UINT nID;
	if (!PyArg_ParseTuple(args, "i",&nID))
		return NULL;
	BOOL res = KillTimer(self->m_hWnd, nID);
	if(!res){
		seterror("KillTimer", GetLastError());
		return NULL;
		}	
	return none();
	}

static PyObject* PyWnd_ClientToScreen(PyWnd *self, PyObject *args)
{
	RECT rect;
	POINT pt;
	bool isrect = true;
	if(!PyArg_ParseTuple(args,"(iiii)", &rect.left, &rect.top, &rect.right, &rect.bottom))
		{
		PyErr_Clear();
		isrect = false;
		if (!PyArg_ParseTuple(args,"(ii):ClientToScreen", &pt.x, &pt.y))
			return NULL;
		}
	if (isrect)
		{
		POINT pt1 = {rect.left, rect.top};
		BOOL res = ClientToScreen(self->m_hWnd, &pt1);
		if(!res)
			{
			seterror("ClientToScreen", GetLastError());
			return NULL;
			}
		POINT pt2 = {rect.right, rect.bottom};
		res = ClientToScreen(self->m_hWnd, &pt2);
		if(!res)
			{
			seterror("ClientToScreen", GetLastError());
			return NULL;
			}
		return Py_BuildValue("(iiii)",pt1.x, pt1.y, pt2.x, pt2.y);
		}
	BOOL res = ClientToScreen(self->m_hWnd, &pt);
	if(!res)
		{
		seterror("ClientToScreen", GetLastError());
		return NULL;
		}
	return Py_BuildValue("(ii)",pt.x, pt.y);
}

static PyObject* PyWnd_SetMenu(PyWnd *self, PyObject *args)
{
	PyObject *obj;
	HMENU hMenu;
	if (!PyArg_ParseTuple(args, "O", &obj))
		return NULL;
	if(PyInt_Check(obj))
		hMenu = (HMENU)PyInt_AsLong(obj);
	else
		{
		struct Temp { PyObject_HEAD; HMENU m_hMenu;};
		hMenu = ((Temp*)obj)->m_hMenu;
		}
	ASSERT_ISWINDOW(self->m_hWnd)
#ifdef _WIN32_WCE
	return none();
#else
	BOOL res = SetMenu(self->m_hWnd, hMenu);
	if(!res){
		seterror("SetMenu", GetLastError());
		return NULL;
		}
	return none();
#endif
}

#ifdef _WIN32_WCE
#include <Aygshell.h>
#include <commctrl.h>
#pragma comment(lib, "aygshell.lib")
static PyObject* PyWnd_SHCreateMenuBar(PyWnd *self, PyObject *args)
	{
	UINT id;
	if(!PyArg_ParseTuple(args,"i", &id))
		return NULL;
	SHMENUBARINFO mbi;
	memset(&mbi, 0, sizeof(SHMENUBARINFO));
	mbi.cbSize     = sizeof(SHMENUBARINFO);
	mbi.hwndParent = self->m_hWnd;
	mbi.nToolBarId = id;
	mbi.hInstRes   = NULL; //GetAppHinstance();
	mbi.nBmpId     = 0;
	mbi.cBmpImages = 0;	
	BOOL res = SHCreateMenuBar(&mbi);
	if(!res)
		{
		seterror("SHCreateMenuBar", GetLastError());
		return NULL;
		}
 	return Py_BuildValue("i", mbi.hwndMB);
	}

extern HWND	hwndCB;	// The command bar handle
static PyObject* PyWnd_GetMenuHandle(PyWnd *self, PyObject *args)
	{
	if(!PyArg_ParseTuple(args,""))
		return NULL;
	if (!hwndCB) {
		seterror("GetMenuHandle", "No menu available");
		return NULL;
	}
	HMENU hMenu = (HMENU)SendMessage(hwndCB, SHCMBM_GETMENU, (WPARAM)0, (LPARAM)0);
 	return Py_BuildValue("i", hMenu);
	}

static PyObject *PyWnd_HideMenuBar(PyWnd *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args,""))
		return NULL;
	if (!hwndCB) {
		seterror("GetMenuHandle", "No menu available");
		return NULL;
	}
	CommandBar_Show(hwndCB, 0);
	return none();
}

#endif

PyMethodDef PyWnd::methods[] = {
	{"Detach", (PyCFunction)PyWnd_Detach, METH_VARARGS, ""},
	{"ShowWindow", (PyCFunction)PyWnd_ShowWindow, METH_VARARGS, ""},
	{"UpdateWindow", (PyCFunction)PyWnd_UpdateWindow, METH_VARARGS, ""},
	{"DestroyWindow", (PyCFunction)PyWnd_DestroyWindow, METH_VARARGS, ""},
	{"InvalidateRect", (PyCFunction)PyWnd_InvalidateRect, METH_VARARGS, ""},
	{"GetClientRect", (PyCFunction)PyWnd_GetClientRect, METH_VARARGS, ""},
	{"RedrawWindow", (PyCFunction)PyWnd_RedrawWindow, METH_VARARGS, ""},
	{"GetDC", (PyCFunction)PyWnd_GetDC, METH_VARARGS, ""},
	{"ReleaseDC", (PyCFunction)PyWnd_ReleaseDC, METH_VARARGS, ""},
	{"BeginPaint", (PyCFunction)PyWnd_BeginPaint, METH_VARARGS, ""},
	{"EndPaint", (PyCFunction)PyWnd_EndPaint, METH_VARARGS, ""},
	{"GetSafeHwnd", (PyCFunction)PyWnd_GetSafeHwnd, METH_VARARGS, ""},
	{"IsWindow", (PyCFunction)PyWnd_IsWindow, METH_VARARGS, ""},
	{"PostMessage", (PyCFunction)PyWnd_PostMessage, METH_VARARGS, ""},
	{"SendMessage", (PyCFunction)PyWnd_SendMessage, METH_VARARGS, ""},
	{"HookMessage", (PyCFunction)PyWnd_HookMessage, METH_VARARGS, ""},
	{"MessageBox", (PyCFunction)PyWnd_MessageBox, METH_VARARGS, ""},
	{"DrawMenuBar", (PyCFunction)PyWnd_DrawMenuBar, METH_VARARGS, ""},
	{"SetClassLong", (PyCFunction)PyWnd_SetClassLong, METH_VARARGS, ""},
	{"SetWindowLong", (PyCFunction)PyWnd_SetWindowLong, METH_VARARGS, ""},
	{"GetWindowLong", (PyCFunction)PyWnd_GetWindowLong, METH_VARARGS, ""},
	{"SetWindowPos", (PyCFunction)PyWnd_SetWindowPos, METH_VARARGS, ""},
	{"MoveWindow", (PyCFunction)PyWnd_MoveWindow, METH_VARARGS, ""},
	{"SetTimer", (PyCFunction)PyWnd_SetTimer, METH_VARARGS, ""},
	{"KillTimer", (PyCFunction)PyWnd_KillTimer, METH_VARARGS, ""},
	{"ClientToScreen", (PyCFunction)PyWnd_ClientToScreen, METH_VARARGS, ""},
	{"SetMenu", (PyCFunction)PyWnd_SetMenu, METH_VARARGS, ""},

#ifdef _WIN32_WCE
	{"SHCreateMenuBar", (PyCFunction)PyWnd_SHCreateMenuBar, METH_VARARGS, ""},
	{"GetMenuHandle", (PyCFunction)PyWnd_GetMenuHandle, METH_VARARGS, ""},
	{"HideMenuBar", (PyCFunction)PyWnd_HideMenuBar, METH_VARARGS, ""},
#endif
	{NULL, (PyCFunction)NULL, 0, NULL}		// sentinel
};

PyTypeObject PyWnd::type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,					// ob_size
	"PyWnd",			// tp_name
	sizeof(PyWnd),		// tp_basicsize
	0,					// tp_itemsize
	
	// methods
	(destructor)PyWnd::dealloc,	// tp_dealloc
	(printfunc)0,				// tp_print
	(getattrfunc)PyWnd::getattr,// tp_getattr
	(setattrfunc)0,	// tp_setattr
	(cmpfunc)0,		// tp_compare
	(reprfunc)0,	// tp_repr
	0,				// tp_as_number
	0,				// tp_as_sequence
	0,				// tp_as_mapping
	(hashfunc)0,	// tp_hash
	(ternaryfunc)0,	// tp_call
	(reprfunc)0,	// tp_str

	// Space for future expansion
	0L,0L,0L,0L,

	"PyWnd Type" // Documentation string
	};

// Local Variables:
// tab-width:4
// End:
