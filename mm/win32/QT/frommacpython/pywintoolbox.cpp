#include "pywintoolbox.h"

#include "Python.h"

#include <windows.h>

#include <QTML.h>
#include <TextUtils.h>

int ToEventRecord(PyObject *obj, EventRecord  *pe)
	{
	MSG msg;
	if (!PyArg_ParseTuple(obj, "iiiii(ii)", &msg.hwnd, &msg.message, &msg.wParam, &msg.lParam, &msg.time, &msg.pt.x, &msg.pt.y))
		return 0;
	WinEventToMacEvent(&msg, pe);
	return 1;
	}

int ToRect(PyObject *obj, Rect  *pr)
	{
	RECT rc;
	if(!PyArg_ParseTuple(obj, "iiii", &rc.left, &rc.top, &rc.right, &rc.bottom))
		return 0;
	pr->left = short(rc.left);
	pr->top = short(rc.top);
	pr->right = short(rc.right);
	pr->bottom = short(rc.bottom);
	return 1;
	}