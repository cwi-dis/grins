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
	};


PyObject *PlayerObject_CreateInstance(PyObject *self, PyObject *args)
	{
	return PlayerObject::CreateInstance(self,args);
	}

PlayerObject::PlayerObject()
:	pPlayer(NULL),
	pErrorSink(NULL),pErrorSinkControl(NULL),
	theErr(PNR_OK)
	{
	}

PlayerObject::~PlayerObject()
	{
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
	PN_RESULT res=obj->pPlayer->OpenURL(psz);
	return Py_BuildValue("i",res);
	}
PyObject* PlayerObject::Begin(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	PN_RESULT res=((PlayerObject*)self)->pPlayer->Begin();
	return Py_BuildValue("i",res);
	}
PyObject* PlayerObject::Stop(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	PN_RESULT res=((PlayerObject*)self)->pPlayer->Stop();
	return Py_BuildValue("i",res);
	}
PyObject* PlayerObject::Pause(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	PN_RESULT res=((PlayerObject*)self)->pPlayer->Begin();
	return Py_BuildValue("i",res);
	}
PyObject* PlayerObject::IsDone(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	BOOL res=((PlayerObject*)self)->pPlayer->IsDone();
	return Py_BuildValue("i",res);
	}
PyObject* PlayerObject::IsLive(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	BOOL res=((PlayerObject*)self)->pPlayer->IsLive();
	return Py_BuildValue("i",res);
	}
PyObject* PlayerObject::GetCurrentPlayTime(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	ULONG32 res=((PlayerObject*)self)->pPlayer->GetCurrentPlayTime();
	return Py_BuildValue("i",res);
	}
PyObject* PlayerObject::Seek(PyObject *self, PyObject *args)
	{
	ULONG32 val;
	if(!PyArg_ParseTuple(args,"i",&val))return NULL;
	PN_RESULT res=((PlayerObject*)self)->pPlayer->Seek(val);
	return Py_BuildValue("i",res);
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
	{NULL, 	NULL}
	};

TypeObject PlayerObject::type("PyRMPlayer", 
						  GetBaseType(), 
						  sizeof(PlayerObject), 
						  PyRMPlayer_methods, 
						  GET_PY_CTOR(PlayerObject));






bool PlayerObject::SetContext()
	{
	ExampleClientContext *pContext = GetContext();
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
    if (pPlayer)
		{
		GetEngine()->ClosePlayer(pPlayer);
		pPlayer->Release();
		pPlayer = NULL;
		}
	}

