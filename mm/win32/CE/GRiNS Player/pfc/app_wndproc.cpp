#include "Python.h"

#include <windows.h>

#include "pyinterface.h"
#include "app_wndproc.h"
#include "app_wnd.h"

LRESULT CALLBACK MinimalMainWndProc(HWND hwnd, UINT iMsg, WPARAM wParam, LPARAM lParam)
	{
	if(iMsg == WM_DESTROY)
		{
		PostQuitMessage(0);
		return 0;
		}
	return DefWindowProc (hwnd, iMsg, wParam, lParam); 
	}

LONG APIENTRY PyWnd_WndProc(HWND hWnd, UINT uMsg, UINT wParam, LONG lParam)
{	
	if(uMsg == WM_CREATE)
		{
		return 0;
		}
	else if(uMsg == WM_DESTROY)
		{
		// application exit
		MSG msg = {hWnd, uMsg, wParam, lParam, 0, {0, 0}};
		std::map<HWND, PyWnd*>::iterator wit = PyWnd::wnds.find(hWnd);
		if(wit != PyWnd::wnds.end())
			{
			PyWnd *pywnd = (*wit).second;
			PyWnd::wnds.erase(wit);
			pywnd->m_hWnd = NULL;
			PyCallbackBlock cbblock;
			Py_DECREF(pywnd);
			}
		PostQuitMessage(0);
		return 0;
		}

	MSG msg = {hWnd, uMsg, wParam, lParam, 0, {0, 0}};
	std::map<HWND, PyWnd*>::iterator wit = PyWnd::wnds.find(hWnd);
	if(wit != PyWnd::wnds.end())
		{
		PyWnd *pywnd = (*wit).second;
		std::map<UINT, PyObject*>& hooks = *pywnd->m_phooks;
		std::map<UINT, PyObject*>::iterator hit = hooks.find(uMsg);
		if(hit != hooks.end())
			{
			PyCallbackBlock cbblock;
			PyObject *method = (*hit).second;
			PyObject *arglst = Py_BuildValue("((iiiii(ii)))",
				msg.hwnd,msg.message,msg.wParam,msg.lParam,msg.time,msg.pt.x,msg.pt.y);
			PyObject *retobj = PyEval_CallObject(method, arglst);
			Py_DECREF(arglst);
			// xxx: elaborate on specific messages
			if (retobj == NULL)
				{
				PyErr_Show();
				PyErr_Clear();
				return DefWindowProc(hWnd, uMsg, wParam, lParam);
				}
			else if(retobj == Py_None)
				{
				Py_DECREF(retobj);
				return 0;
				}
			else
				{
				long retval = PyInt_AsLong(retobj);
				Py_DECREF(retobj);
				if(retval == 0) return 0;
				else return DefWindowProc(hWnd, uMsg, wParam, lParam);
				}
			}
		}
	return DefWindowProc(hWnd, uMsg, wParam, lParam);
}
