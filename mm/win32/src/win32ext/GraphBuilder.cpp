// CMIF_ADD
//
// kk@epsilon.com.gr
//

#include "stdafx.h"
#include "win32win.h"

#include "moddef.h"

#include "GraphBuilder.h"

// Purpose: This module exports to Python the interface IGraphBuilder and indirectly 
// other interfaces related to the DirectShow Infrastructure. The indirectly exposed interface
// is sufficient to control a media stream (sound and video)


// Create an instance of a GraphBuilder (a wrapper object to the COM interface IGraphBuilder)
// Arguments: No
// Return Values: a GraphBuilder object that is a wrapper to the COM interface IGraphBuilder
//static 
PyObject *GraphBuilderCreator::Create(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);

	IGraphBuilder *pIGraph=NULL;
	GUI_BGN_SAVE;
	HRESULT hr = CoCreateInstance(CLSID_FilterGraph,
                          NULL,
                          CLSCTX_INPROC_SERVER,
                          IID_IGraphBuilder,
                          (void **)&pIGraph);
	GUI_END_SAVE;
	if (FAILED(hr)) RETURN_NONE;

	GraphBuilder* pGraph=new GraphBuilder(pIGraph);
	return ui_assoc_object::make(PyClass<GraphBuilder,GraphBuilderCreator>::type,pGraph);
	}

// Release the interface associated with the GraphBuilder
// Arguments: No
// Return Values: None
static PyObject* py_release(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,Release);

	GraphBuilder *pGraphBuilder=(GraphBuilder*)((PyClass<GraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraphBuilder)return NULL;

	GUI_BGN_SAVE;
	pGraphBuilder->Release();
	GUI_END_SAVE;

	RETURN_NONE;
	}

// Render the media file passed as argument
// Arguments: filename to parse (string)
// Return Values: None
static PyObject* py_render_file(PyObject *self, PyObject *args)
	{
	char* pszFileName;
	if(!PyArg_ParseTuple(args,"s:RenderFile",&pszFileName))
		return NULL;

	GraphBuilder *pGraphBuilder=(GraphBuilder*)((PyClass<GraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraphBuilder)return NULL;
	IGraphBuilder* pGraph=pGraphBuilder->m_pI;

    WCHAR wPath[MAX_PATH];
    MultiByteToWideChar(CP_ACP,0,pszFileName,-1, wPath, MAX_PATH);
 
	GUI_BGN_SAVE;
	HRESULT hr=pGraph->RenderFile(wPath, NULL);
	GUI_END_SAVE;

	BOOL res=TRUE;
	if(FAILED(hr)) 
		res=FALSE; //RETURN_ERR("RenderFile failed");

	return Py_BuildValue("i",res);
	}

// Run (start playing) the rendered stream
// Arguments: No
// Return Values: None
static PyObject* py_run(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,Run);

	GraphBuilder *pGraphBuilder=(GraphBuilder*)((PyClass<GraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraphBuilder)return NULL;
	IGraphBuilder* pGraph=pGraphBuilder->m_pI;

	IMediaControl *pMC=NULL;
	HRESULT	hr = pGraph->QueryInterface(IID_IMediaControl, (void **) &pMC);
    if(SUCCEEDED(hr) )
		{
		GUI_BGN_SAVE;
        hr = pMC->Run();
        pMC->Release();
		GUI_END_SAVE;
        }
	RETURN_NONE;
	}

// Stop the rendered media stream
// Arguments: No
// Return Values: None
static PyObject* py_stop(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,Stop);

	GraphBuilder *pGraphBuilder=(GraphBuilder*)((PyClass<GraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraphBuilder)return NULL;
	IGraphBuilder* pGraph=pGraphBuilder->m_pI;

	IMediaControl *pMC=NULL;
	HRESULT	hr = pGraph->QueryInterface(IID_IMediaControl, (void **) &pMC);
    if(SUCCEEDED(hr))
		{
		GUI_BGN_SAVE;
        hr = pMC->Stop();
        pMC->Release();
		GUI_END_SAVE;
        }
	RETURN_NONE;
	}

// Pause the rendered media stream
// Arguments: No
// Return Values: None
static PyObject* py_pause(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,Pause);

	GraphBuilder *pGraphBuilder=(GraphBuilder*)((PyClass<GraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraphBuilder)return NULL;
	IGraphBuilder* pGraph=pGraphBuilder->m_pI;

	IMediaControl* pMC=NULL;
	HRESULT	hr = pGraph->QueryInterface(IID_IMediaControl, (void **) &pMC);
    if(SUCCEEDED(hr))
		{
		GUI_BGN_SAVE;
        hr = pMC->Pause();
        pMC->Release();
		GUI_END_SAVE;
        }
	RETURN_NONE;
	}

// Get the duration (in msec) of the rendered file
// Arguments: No
// Return Values: duration in msecs

static PyObject* py_get_duration(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,GetDuration);

	GraphBuilder *pGraphBuilder=(GraphBuilder*)((PyClass<GraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraphBuilder)return NULL;
	IGraphBuilder* pGraph=pGraphBuilder->m_pI;

	HRESULT hr=S_OK;
	if(!pGraphBuilder->m_pIMP)
		hr = pGraph->QueryInterface(IID_IMediaPosition, (void**)&(pGraphBuilder->m_pIMP));
    if(SUCCEEDED(hr) )
		{
        REFTIME tLength; // double in secs
		GUI_BGN_SAVE;
        hr = pGraphBuilder->m_pIMP->get_Duration(&tLength);
		GUI_END_SAVE;
		if (SUCCEEDED(hr))
			return Py_BuildValue("i", int(tLength*1000)); // in msec
        }
	RETURN_ERR("GetDuration failed");
	}

// Get the current sample position (in msec) within the stream
// Arguments: No
// Return Values: position within the stream in msecs
static PyObject* py_get_position(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,GetPosition);

	GraphBuilder *pGraphBuilder=(GraphBuilder*)((PyClass<GraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraphBuilder)return NULL;
	IGraphBuilder* pGraph=pGraphBuilder->m_pI;

	HRESULT hr=S_OK;
	if(!pGraphBuilder->m_pIMP)
		hr = pGraph->QueryInterface(IID_IMediaPosition, (void**)&(pGraphBuilder->m_pIMP));
    if(SUCCEEDED(hr))
		{
        REFTIME tCurrent; // double in secs
		GUI_BGN_SAVE;
        hr = pGraphBuilder->m_pIMP->get_CurrentPosition(&tCurrent);
		GUI_END_SAVE;
		if (SUCCEEDED(hr))
			return Py_BuildValue("i", int(tCurrent*1000)); // in msec
        }
	RETURN_ERR("GetPosition failed");
	}

// Set to sample position (in msec) within the stream
// Arguments: position in msec
// Return Values: None
static PyObject* py_set_position(PyObject *self, PyObject *args)
	{
	int pos; // in msec
	if(!PyArg_ParseTuple(args,"i:SetPosition",&pos))
		return NULL;

	GraphBuilder *pGraphBuilder=(GraphBuilder*)((PyClass<GraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraphBuilder)return NULL;
	IGraphBuilder* pGraph=pGraphBuilder->m_pI;

	HRESULT hr=S_OK;
	if(!pGraphBuilder->m_pIMP)
		hr = pGraph->QueryInterface(IID_IMediaPosition, (void**)&(pGraphBuilder->m_pIMP));
    if(SUCCEEDED(hr))
		{
		GUI_BGN_SAVE;
        REFTIME tPos=double(pos)/1000.0; // double in secs
        hr = pGraphBuilder->m_pIMP->put_CurrentPosition(tPos);
		GUI_END_SAVE;
        }
	RETURN_NONE;
	}

// Set the visible property to the value passed as argument (only for video)
// Arguments: visible flag 
// Return Values: None
static PyObject* py_set_visible(PyObject *self, PyObject *args)
	{
	int flag; 
	if(!PyArg_ParseTuple(args,"i:SetVisible",&flag))
		return NULL;

	GraphBuilder *pGraphBuilder=(GraphBuilder*)((PyClass<GraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraphBuilder)return NULL;
	IGraphBuilder* pGraph=pGraphBuilder->m_pI;
	
	long Visible=flag?-1:0; // OATRUE (-1),OAFALSE (0)
	IVideoWindow  *pivw  = NULL;
    HRESULT hr=pGraph->QueryInterface(IID_IVideoWindow,(void **)&pivw);
    if(SUCCEEDED(hr))
		{
		GUI_BGN_SAVE;
        pivw->put_Visible(Visible);
		pivw->Release();
		GUI_END_SAVE;
		}
	RETURN_NONE;
	}

// Set the owner and notification window (only for video)
// Arguments: a PyCWnd object and optionaly the message id for notifications
// Return Values: None
static PyObject* py_set_window(PyObject *self, PyObject *args)
	{
	int WM_GRAPHNOTIFY=WM_USER+101;
	PyObject *obWnd = Py_None;
	if(!PyArg_ParseTuple(args,"O|i:SetWindow",&obWnd,&WM_GRAPHNOTIFY))
		return NULL;
	CWnd *pWnd = GetWndPtr(obWnd);
	if(!pWnd)RETURN_TYPE_ERR("The arg must be a PyCWnd object");

	GraphBuilder *pGraphBuilder=(GraphBuilder*)((PyClass<GraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraphBuilder)return NULL;
	IGraphBuilder* pGraph=pGraphBuilder->m_pI;


	IVideoWindow  *pivw  = NULL;
    HRESULT hr=pGraph->QueryInterface(IID_IVideoWindow,(void **)&pivw);
    if(SUCCEEDED(hr) )
		{
		GUI_BGN_SAVE;
        pivw->put_Owner((OAHWND)pWnd->GetSafeHwnd());
		pivw->put_MessageDrain((OAHWND)pWnd->GetSafeHwnd());
        pivw->put_WindowStyle(WS_CHILD|WS_CLIPSIBLINGS|WS_CLIPCHILDREN);
		CRect rc;pWnd->GetClientRect(&rc);
		pivw->SetWindowPosition(rc.left, rc.top, rc.right, rc.bottom);
		pivw->Release();
		GUI_END_SAVE;
		}

	IMediaEventEx *pimex = NULL;
    hr=pGraph->QueryInterface(IID_IMediaEventEx,(void **)&pimex);
    if(SUCCEEDED(hr) )
		{
        pimex->SetNotifyWindow((OAHWND)pWnd->GetSafeHwnd(),WM_GRAPHNOTIFY,0);
		pimex->Release();
		}
	RETURN_NONE;
	}

// Set window position(only for video)
// Arguments: the window rectangle 
// Return Values: None
static PyObject* py_set_window_position(PyObject *self, PyObject *args)
	{
	CRect rc;
	if (!PyArg_ParseTuple(args,"(iiii):SetWindowPosition", &rc.left, &rc.top, &rc.right, &rc.bottom))
		return NULL;

	GraphBuilder *pGraphBuilder=(GraphBuilder*)((PyClass<GraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraphBuilder)return NULL;
	IGraphBuilder* pGraph=pGraphBuilder->m_pI;

	IVideoWindow  *pivw  = NULL;
    HRESULT hr=pGraph->QueryInterface(IID_IVideoWindow,(void **)&pivw);
    if(SUCCEEDED(hr) )
		{
		GUI_BGN_SAVE;
		pivw->SetWindowPosition(rc.left, rc.top, rc.right, rc.bottom);
		pivw->Release();
		GUI_END_SAVE;
		}
	RETURN_NONE;
	}

// Get window position(only for video)
// Arguments: No 
// Return Values: window position as (left,top,width,height)

static PyObject* py_get_window_position(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,GetWindowPosition);


	GraphBuilder *pGraphBuilder=(GraphBuilder*)((PyClass<GraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraphBuilder)return NULL;
	IGraphBuilder* pGraph=pGraphBuilder->m_pI;

	IVideoWindow  *pivw  = NULL;
    HRESULT hr=pGraph->QueryInterface(IID_IVideoWindow,(void **)&pivw);
	CRect rc;
    if(SUCCEEDED(hr) )
		{
		GUI_BGN_SAVE;
		pivw->GetWindowPosition(&rc.left, &rc.top, &rc.right, &rc.bottom);
		pivw->Release();
		GUI_END_SAVE;
		}

	return Py_BuildValue("(iiii)",rc.left, rc.top, rc.right, rc.bottom); 
	}


// Set the owner window to Null (only for video)
// Arguments: No 
// Return Values: None

static PyObject* py_set_window_null(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,SetWindowNull);

	GraphBuilder *pGraphBuilder=(GraphBuilder*)((PyClass<GraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraphBuilder)return NULL;
	IGraphBuilder* pGraph=pGraphBuilder->m_pI;

	IVideoWindow* pivw  = NULL;
    HRESULT hr=pGraph->QueryInterface(IID_IVideoWindow,(void **)&pivw);
    if(SUCCEEDED(hr))
		{
		GUI_BGN_SAVE;
        pivw->put_Visible(0);
        pivw->put_Owner(NULL);
		pivw->Release();
		GUI_END_SAVE;
		}
	RETURN_NONE;
	}


// Set the window that will receive stream notification messages
// Arguments: a PyCWnd object and optionaly the message id for notifications
// Return Values: None
static PyObject* py_set_notify_window(PyObject *self, PyObject *args)
	{
	int WM_GRAPHNOTIFY=WM_USER+101;
	PyObject *obWnd = Py_None;
	if(!PyArg_ParseTuple(args,"O|i:SetNotifyWindow",&obWnd,&WM_GRAPHNOTIFY))
		return NULL;
	CWnd *pWnd = GetWndPtr(obWnd);
	if(!pWnd)RETURN_TYPE_ERR("The arg must be a PyCWnd object");

	GraphBuilder *pGraphBuilder=(GraphBuilder*)((PyClass<GraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraphBuilder)return NULL;
	IGraphBuilder* pGraph=pGraphBuilder->m_pI;

	IMediaEventEx *pimex = NULL;
    HRESULT hr=pGraph->QueryInterface(IID_IMediaEventEx,(void **)&pimex);
    if(SUCCEEDED(hr) )
		{
        pimex->SetNotifyWindow((OAHWND)pWnd->GetSafeHwnd(),WM_GRAPHNOTIFY,0);
		pimex->Release();
		}
	RETURN_NONE;
	}

// Check if the stream has completed
// Arguments: No
// Return Values: Not zero if completed 
static PyObject* py_is_complete_event(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,IsCompleteEvent);

	GraphBuilder *pGraphBuilder=(GraphBuilder*)((PyClass<GraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraphBuilder)return NULL;
	IGraphBuilder* pGraph=pGraphBuilder->m_pI;

	IMediaEventEx *pimex = NULL;
    HRESULT hr=pGraph->QueryInterface(IID_IMediaEventEx,(void **)&pimex);
    int completed=0;
	long evCode,evParam1,evParam2;
	if(SUCCEEDED(hr) )
		{
        while (SUCCEEDED(pimex->GetEvent(&evCode, &evParam1, &evParam2, 0)))
			{
            hr = pimex->FreeEventParams(evCode, evParam1, evParam2);
            if(evCode==EC_COMPLETE){completed=1;}
			}
		pimex->Release();
		}
	return Py_BuildValue("i",completed);
	}



// @object PyGraphBuilder|A class which encapsulates DirectShow SDK.
static struct PyMethodDef PyGraphBuilder_methods[] = {
	{"Release",py_release,1}, 
	{"RenderFile",py_render_file,1},
	
	{"Run",py_run,1}, 
	{"Stop",py_stop,1}, 
	{"Pause",py_pause,1}, 

	{"GetDuration",py_get_duration,1}, 
	{"GetPosition",py_get_position,1}, 
	{"SetPosition",py_set_position,1},
	
	{"SetWindow",py_set_window,1}, 
	{"SetWindowNull",py_set_window_null,1}, 
	{"SetNotifyWindow",py_set_notify_window,1}, 
	{"IsCompleteEvent",py_is_complete_event,1}, 
	{"SetWindowPosition",py_set_window_position,1}, 
	{"GetWindowPosition",py_get_window_position,1}, 
	{"SetVisible",py_set_visible,1}, 

	{NULL,NULL,1}		
};


ui_type PyClass<GraphBuilder,GraphBuilderCreator>::type ("PyGraphBuilder",
				&ui_assoc_object::type,
				sizeof(PyClass<GraphBuilder,GraphBuilderCreator>),
				PyGraphBuilder_methods,
				PyClass<GraphBuilder,GraphBuilderCreator>::PyObConstruct);

