// CMIF_ADD
//
// kk@epsilon.com.gr
//

#include "stdafx.h"
#include "win32win.h"

#include "moddef.h"

#include "GraphBuilder.h"

//static 
PyObject *GraphBuilderCreator::Create(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);

	IGraphBuilder *pGraph=NULL;
	GUI_BGN_SAVE;
	HRESULT hr = CoCreateInstance(CLSID_FilterGraph,
                          NULL,
                          CLSCTX_INPROC_SERVER,
                          IID_IGraphBuilder,
                          (void **)&pGraph);
	GUI_END_SAVE;
	if (FAILED(hr)) RETURN_NONE;
	return ui_assoc_object::make(PyIClass<IGraphBuilder,GraphBuilderCreator>::type,pGraph);
	}


static PyObject* py_release(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,Release);

	IGraphBuilder *pGraph=(IGraphBuilder*)((PyIClass<IGraphBuilder,GraphBuilderCreator> *)self)->GetObject();

	GUI_BGN_SAVE;
	if(pGraph) pGraph->Release();
	GUI_END_SAVE;

	RETURN_NONE;
	}

static PyObject* py_render_file(PyObject *self, PyObject *args)
	{
	char* pszFileName;
	if(!PyArg_ParseTuple(args,"s:RenderFile",&pszFileName))
		return NULL;

	IGraphBuilder *pGraph=(IGraphBuilder*)((PyIClass<IGraphBuilder,GraphBuilderCreator> *)self)->GetObject();

    WCHAR wPath[MAX_PATH];
    MultiByteToWideChar(CP_ACP,0,pszFileName,-1, wPath, MAX_PATH);
 
	GUI_BGN_SAVE;
	HRESULT hr=pGraph->RenderFile(wPath, NULL);
	GUI_END_SAVE;

	if(FAILED(hr)) RETURN_ERR("RenderFile failed");

	RETURN_NONE;
	}

static PyObject* py_run(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,Run);

	IGraphBuilder *pGraph=(IGraphBuilder*)((PyIClass<IGraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraph)return NULL;

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

static PyObject* py_stop(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,Stop);

	IGraphBuilder *pGraph=(IGraphBuilder*)((PyIClass<IGraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraph)return NULL;
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
static PyObject* py_pause(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,Pause);

	IGraphBuilder *pGraph=(IGraphBuilder*)((PyIClass<IGraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraph) return NULL;

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

static PyObject* py_get_duration(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,GetDuration);

	IGraphBuilder *pGraph=(IGraphBuilder*)((PyIClass<IGraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraph)return NULL;

    IMediaPosition* pMP=NULL;
    HRESULT hr = pGraph->QueryInterface(IID_IMediaPosition, (void**) &pMP);
    if(SUCCEEDED(hr) )
		{
        REFTIME tLength; // double in secs
		GUI_BGN_SAVE;
        hr = pMP->get_Duration(&tLength);
		pMP->Release();
		GUI_END_SAVE;
		if (SUCCEEDED(hr))
			return Py_BuildValue("i", int(tLength*1000)); // in msec
        }
	RETURN_ERR("GetDuration failed");
	}

static PyObject* py_get_position(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,GetPosition);

	IGraphBuilder *pGraph=(IGraphBuilder*)((PyIClass<IGraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraph)return NULL;
    IMediaPosition * pMP=NULL;
    HRESULT hr = pGraph->QueryInterface(IID_IMediaPosition, (void**) &pMP);
    if(SUCCEEDED(hr) )
		{
        REFTIME tCurrent; // double in secs
		GUI_BGN_SAVE;
        hr = pMP->get_CurrentPosition(&tCurrent);
		pMP->Release();
		GUI_END_SAVE;
		if (SUCCEEDED(hr))
			return Py_BuildValue("i", int(tCurrent*1000)); // in msec
        }
	RETURN_ERR("GetPosition failed");
	}

static PyObject* py_set_position(PyObject *self, PyObject *args)
	{
	int pos; // in msec
	if(!PyArg_ParseTuple(args,"i:SetPosition",&pos))
		return NULL;

	IGraphBuilder *pGraph=(IGraphBuilder*)((PyIClass<IGraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraph)return NULL;
    IMediaPosition* pMP=NULL;
    HRESULT hr = pGraph->QueryInterface(IID_IMediaPosition, (void**) &pMP);
    if(SUCCEEDED(hr) )
		{
		GUI_BGN_SAVE;
        REFTIME tPos=double(pos)/1000.0; // double in secs
        hr = pMP->put_CurrentPosition(tPos);
		pMP->Release();
		GUI_END_SAVE;
        }
	RETURN_NONE;
	}

static PyObject* py_set_visible(PyObject *self, PyObject *args)
	{
	int flag; 
	if(!PyArg_ParseTuple(args,"i:SetVisible",&flag))
		return NULL;

	IGraphBuilder *pGraph=(IGraphBuilder*)((PyIClass<IGraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraph)return NULL;
	
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


static PyObject* py_set_window(PyObject *self, PyObject *args)
	{
	int WM_GRAPHNOTIFY=WM_USER+101;
	PyObject *obWnd = Py_None;
	if(!PyArg_ParseTuple(args,"O|i:SetWindow",&obWnd,&WM_GRAPHNOTIFY))
		return NULL;
	CWnd *pWnd = GetWndPtr(obWnd);
	if(!pWnd)RETURN_TYPE_ERR("The arg must be a PyCWnd object");

	IGraphBuilder *pGraph=(IGraphBuilder*)((PyIClass<IGraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraph)return NULL;


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


static PyObject* py_set_window_position(PyObject *self, PyObject *args)
	{
	CRect rc;
	if (!PyArg_ParseTuple(args,"(iiii):SetWindowPosition", &rc.left, &rc.top, &rc.right, &rc.bottom))
		return NULL;

	IGraphBuilder *pGraph=(IGraphBuilder*)((PyIClass<IGraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraph)return NULL;

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

// returns (left,top,width,height)
static PyObject* py_get_window_position(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,GetWindowPosition);


	IGraphBuilder *pGraph=(IGraphBuilder*)((PyIClass<IGraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraph)return NULL;

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



static PyObject* py_set_window_null(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,SetWindowNull);

	IGraphBuilder *pGraph=(IGraphBuilder*)((PyIClass<IGraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraph)return NULL;

	IVideoWindow* pivw  = NULL;
    HRESULT hr=pGraph->QueryInterface(IID_IVideoWindow,(void **)&pivw);
    if(SUCCEEDED(hr))
		{
		GUI_BGN_SAVE;
        pivw->put_Visible(0);
        pivw->put_Owner(NULL);
		GUI_END_SAVE;
		}
	RETURN_NONE;
	}


static PyObject* py_set_notify_window(PyObject *self, PyObject *args)
	{
	int WM_GRAPHNOTIFY=WM_USER+101;
	PyObject *obWnd = Py_None;
	if(!PyArg_ParseTuple(args,"O|i:SetNotifyWindow",&obWnd,&WM_GRAPHNOTIFY))
		return NULL;
	CWnd *pWnd = GetWndPtr(obWnd);
	if(!pWnd)RETURN_TYPE_ERR("The arg must be a PyCWnd object");

	IGraphBuilder *pGraph=(IGraphBuilder*)((PyIClass<IGraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraph)return NULL;

	IMediaEventEx *pimex = NULL;
    HRESULT hr=pGraph->QueryInterface(IID_IMediaEventEx,(void **)&pimex);
    if(SUCCEEDED(hr) )
		{
        pimex->SetNotifyWindow((OAHWND)pWnd->GetSafeHwnd(),WM_GRAPHNOTIFY,0);
		pimex->Release();
		}
	RETURN_NONE;
	}

static PyObject* py_is_complete_event(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,IsCompleteEvent);

	IGraphBuilder *pGraph=(IGraphBuilder*)((PyIClass<IGraphBuilder,GraphBuilderCreator> *)self)->GetObject();
	if(!pGraph)return NULL;

	IMediaEventEx *pimex = NULL;
    HRESULT hr=pGraph->QueryInterface(IID_IMediaEventEx,(void **)&pimex);
    int completed=0;
	long evCode,evParam1,evParam2;
	if(SUCCEEDED(hr) )
		{
        while (SUCCEEDED(pimex->GetEvent(&evCode, &evParam1, &evParam2, 0)))
			{
            hr = pimex->FreeEventParams(evCode, evParam1, evParam2);
            if(evCode==EC_COMPLETE){completed=1;break;}
			}
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


ui_type PyIClass<IGraphBuilder,GraphBuilderCreator>::type ("PyGraphBuilder",
				&ui_assoc_object::type,
				sizeof(PyIClass<IGraphBuilder,GraphBuilderCreator>),
				PyGraphBuilder_methods,
				PyIClass<IGraphBuilder,GraphBuilderCreator>::PyObConstruct);

