#include "std.h"
#include "PyCppApi.h"
#include "StdRma.h"

#include "Engine.h"

#include "os.h"
#include "StdApp.h"


class PlayerObject : public Object
	{
	public:
	MAKE_PY_CTOR(PlayerObject)
	static TypeObject type;
	static PyObject *CreateInstance(PyObject *self, PyObject *args);
	static TypeObject* GetBaseType(){return &Object::type;}

	// PyMethods
	static PyObject* OpenURL(PyObject *self, PyObject *args);

	static PyObject* Begin(PyObject *self, PyObject *args);
	static PyObject* Stop(PyObject *self, PyObject *args);
 	static PyObject* Pause(PyObject *self, PyObject *args);

	static PyObject* IsDone(PyObject *self, PyObject *args);
 	static PyObject* IsLive(PyObject *self, PyObject *args);

	static PyObject* GetCurrentPlayTime(PyObject *self, PyObject *args);
  	static PyObject* Seek(PyObject *self, PyObject *args);

	static PyObject* SetPyAdviceSink(PyObject *self, PyObject *args);
	static PyObject* SetPyVideoSurface(PyObject *self, PyObject *args);

	static PyObject* SetOsWindow(PyObject *self, PyObject *args);
	static PyObject* ShowInNewWindow(PyObject *self, PyObject *args);
	

	protected:
	PlayerObject();
	~PlayerObject();
	virtual string repr();

	private:
	bool SetContext();
	void ReleaseObjects();

	IRMAPlayer*	pPlayer;
	IRMAErrorSink* pErrorSink;
	IRMAErrorSinkControl* pErrorSinkControl;
	PN_RESULT theErr;
	ExampleClientContext *pContext;
	};


PyObject *PlayerObject_CreateInstance(PyObject *self, PyObject *args)
	{
	return PlayerObject::CreateInstance(self,args);
	}

PlayerObject::PlayerObject()
:	pPlayer(NULL),
	pErrorSink(NULL),pErrorSinkControl(NULL),
	theErr(PNR_OK),
	pContext(NULL)
	{
	}

PlayerObject::~PlayerObject()
	{
	if(pContext)
		pContext->m_pClientSink->SetPyAdviceSink(NULL);
	if(pPlayer)pPlayer->Stop();
	ReleaseObjects();
	EngineObject_Release();
	}

PyObject *PlayerObject::CreateInstance(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	EngineObject_CreateInstance(self,args);
	IRMAClientEngine* pEngine=GetEngine();
	if(!pEngine)
		{
		PyErr_SetString(module_error,"Failed to create RMEngine.");
		return NULL;
		}
	PlayerObject* obj=(PlayerObject*)Object::make(PlayerObject::type);
	if(PNR_OK != pEngine->CreatePlayer(obj->pPlayer))
		{
		PyErr_SetString(module_error,"CreatePlayer failed.");
		return NULL;
		}
	obj->SetContext();
	return obj;
	}

string PlayerObject::repr()
	{
	char buf[256];
	sprintf (buf," instance 0x%X",this);
	return Object::repr() + buf;
	}

/////////////////////////////////////////////
// PyMethods
PyObject* PlayerObject::OpenURL(PyObject *self, PyObject *args)
	{
	PlayerObject* obj = (PlayerObject*)self;
	char *psz;
	if(!PyArg_ParseTuple(args,"s",&psz))return NULL;
	BGN_SAVE;
	PN_RESULT res=obj->pPlayer->OpenURL(psz);
	END_SAVE;
	return Py_BuildValue("i",res);
	}
PyObject* PlayerObject::Begin(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	BGN_SAVE;
	PN_RESULT res=((PlayerObject*)self)->pPlayer->Begin();
	END_SAVE;
	return Py_BuildValue("i",res);
	}
PyObject* PlayerObject::Stop(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	BGN_SAVE;
	PN_RESULT res=((PlayerObject*)self)->pPlayer->Stop();
	END_SAVE;
	return Py_BuildValue("i",res);
	}
PyObject* PlayerObject::Pause(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	BGN_SAVE;
	PN_RESULT res=((PlayerObject*)self)->pPlayer->Pause();
	END_SAVE;
	return Py_BuildValue("i",res);
	}
PyObject* PlayerObject::IsDone(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	BGN_SAVE;
	BOOL res=((PlayerObject*)self)->pPlayer->IsDone();
	END_SAVE;
	return Py_BuildValue("i",res);
	}
PyObject* PlayerObject::IsLive(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	BGN_SAVE;
	BOOL res=((PlayerObject*)self)->pPlayer->IsLive();
	END_SAVE;
	return Py_BuildValue("i",res);
	}
PyObject* PlayerObject::GetCurrentPlayTime(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	BGN_SAVE;
	ULONG32 res=((PlayerObject*)self)->pPlayer->GetCurrentPlayTime();
	END_SAVE;
	return Py_BuildValue("i",res);
	}
PyObject* PlayerObject::Seek(PyObject *self, PyObject *args)
	{
	ULONG32 val;
	if(!PyArg_ParseTuple(args,"i",&val))return NULL;
	BGN_SAVE;
	PN_RESULT res=((PlayerObject*)self)->pPlayer->Seek(val);
	END_SAVE;
	return Py_BuildValue("i",res);
	}
PyObject* PlayerObject::SetPyAdviceSink(PyObject *self, PyObject *args)
	{
	PyObject *obj;
	if(!PyArg_ParseTuple(args,"O",&obj))return NULL;
	ExampleClientContext *pCC=((PlayerObject*)self)->pContext;
	if(pCC)pCC->m_pClientSink->SetPyAdviceSink(obj);
	RETURN_NONE;
	}

// Support removed. 
PyObject* PlayerObject::SetPyVideoSurface(PyObject *self, PyObject *args)
	{
	PyObject *obj;
	if(!PyArg_ParseTuple(args,"O",&obj))return NULL;
	ExampleClientContext *pCC=((PlayerObject*)self)->pContext;
	if(pCC)
		{
		ExampleSiteSupplier *ss=pCC->m_pSiteSupplier;
		//if(ss)ss->SetPyVideoSurface(obj);
		}
	RETURN_NONE;
	}

PyObject* PlayerObject::SetOsWindow(PyObject *self, PyObject *args)
	{
	int hwnd;
	if(!PyArg_ParseTuple(args,"i",&hwnd))return NULL;
	ExampleClientContext *pCC=((PlayerObject*)self)->pContext;
	if(pCC)
		{
		ExampleSiteSupplier *ss=pCC->m_pSiteSupplier;
		if(ss)ss->SetOsWindow((void*)hwnd);
		}
	RETURN_NONE;
	}

PyObject* PlayerObject::ShowInNewWindow(PyObject *self, PyObject *args)
	{
	int f;
	if(!PyArg_ParseTuple(args,"i",&f))return NULL;
	ExampleClientContext *pCC=((PlayerObject*)self)->pContext;
	if(pCC)
		{
		ExampleSiteSupplier *ss=pCC->m_pSiteSupplier;
		if(ss)ss->ShowInNewWindow(f);
		}
	RETURN_NONE;
	}


static struct PyMethodDef PyRMPlayer_methods[] =
	{
	{"OpenURL",PlayerObject::OpenURL,1}, 
	{"Begin",PlayerObject::Begin,1}, 
	{"Stop",PlayerObject::Stop,1}, 
	{"Pause",PlayerObject::Pause,1},
	{"IsDone",PlayerObject::IsDone,1},
	{"IsLive",PlayerObject::IsLive,1},
	{"GetCurrentPlayTime",PlayerObject::GetCurrentPlayTime,1},
	{"Seek",PlayerObject::Seek,1},
	{"SetPyAdviceSink",PlayerObject::SetPyAdviceSink,1},   // formal name
	{"SetStatusListener",PlayerObject::SetPyAdviceSink,1}, // alias
	{"SetVideoSurface",PlayerObject::SetPyVideoSurface,1},
	{"SetOsWindow",PlayerObject::SetOsWindow,1}, // alias
	{"ShowInNewWindow",PlayerObject::ShowInNewWindow,1}, // alias
	{NULL, 	NULL}
	};

TypeObject PlayerObject::type("PyRMPlayer", 
						  GetBaseType(), 
						  sizeof(PlayerObject), 
						  PyRMPlayer_methods, 
						  GET_PY_CTOR(PlayerObject));






bool PlayerObject::SetContext()
	{
    if(!(pContext = new ExampleClientContext()))
		{
		theErr = PNR_UNEXPECTED;
		return false;
		}
	pContext->AddRef();

    pContext->Init(pPlayer);
    pPlayer->SetClientContext(pContext);

    pPlayer->QueryInterface(IID_IRMAErrorSinkControl, 
					(void**)&pErrorSinkControl);
    if (pErrorSinkControl)
		{	
		pContext->QueryInterface(IID_IRMAErrorSink, 
					(void**) &pErrorSink);
		
		if (pErrorSink)
			{
			pErrorSinkControl->AddErrorSink(pErrorSink,PNLOG_EMERG, PNLOG_INFO);
			}
		}
	return true;
	}


void PlayerObject::ReleaseObjects()
	{
    if (pErrorSinkControl)
		{
		pErrorSinkControl->RemoveErrorSink(pErrorSink);
		pErrorSinkControl->Release();
		pErrorSinkControl = NULL;
		}
    if (pContext)
		{
		pContext->Release();
		pContext = NULL;
		}
    if (pPlayer)
		{
		GetEngine()->ClosePlayer(pPlayer);
		pPlayer->Release();
		pPlayer = NULL;
		}
	}

