#include "stdafx.h"
#include "pythonwin.h"
#include "pythonview.h"
#include "win32ui.h"


typedef CPythonWndFramework< CWebBrowser > CPythonWebBrowser;

class PYW_EXPORT PyCWebBrowser : public PyCWnd 
	{
	protected:
	PyCWebBrowser() {}
	~PyCWebBrowser(){}
	public:
	static CWebBrowser *GetWebBrowserPtr(PyObject *self);
	static ui_type_CObject type;
	};

CView *PyCWebBrowser::GetWebBrowserPtr(PyObject *self)
	{
	return (CWebBrowser*)PyCWnd::GetPythonGenericWnd(self, &PyCWebBrowser::type);
	}

// @pymethod <o PyCWebBrowser>|win32ui|CreateBrowser|Creates a generic browser object.
PyObject * PyCWebBrowser::create(PyObject *self, PyObject *args)
	{
	GUI_BGN_SAVE;
	CWebBrowser *pWebBrowser = new CPythonWebBrowser();
	GUI_END_SAVE;
	return ui_assoc_object::make(PyCWebBrowser::type,pWebBrowser);
	}

// @pymethod |PyCWebBrowser|Create|Creates the window for the browser.
static PyObject *
PyCWebBrowser_create(PyObject *self, PyObject *args)
	{
	CWebBrowser *pWebBrowser = PyCWebBrowser::GetWebBrowserPtr(self);
	if (!pWebBrowser) return NULL;

	GUI_BGN_SAVE;
    BOOL ok = pWebBrowser->Create(NULL, NULL, style, rect, pWnd, id, &context);
	GUI_END_SAVE;
	if(!ok)RETURN_ERR("Create() browser failed\n");

	RETURN_NONE;
	}

