#include "Std.h"
#include "PyCppApi.h"
#include "StdRma.h"
#include "Engine.h"
#include "os.h"
#include "StdApp.h"
#ifdef _MACINTOSH
#include <Windows.h>
extern "C" {
extern int WinObj_Convert(PyObject *, WindowPtr *);
}
#endif

class PlayerObject : public RMAObject {
public:
	MAKE_PY_CTOR(PlayerObject)
	static TypeObject type;
	static PyObject *CreateInstance(PyObject *self, PyObject *args);
	static TypeObject *GetBaseType(){return &RMAObject::type;}

	// PyMethods
	static PyObject *OpenURL(PyObject *self, PyObject *args);

	static PyObject *Begin(PyObject *self, PyObject *args);
	static PyObject *Stop(PyObject *self, PyObject *args);
 	static PyObject *Pause(PyObject *self, PyObject *args);

	static PyObject *IsDone(PyObject *self, PyObject *args);
 	static PyObject *IsLive(PyObject *self, PyObject *args);

	static PyObject *GetCurrentPlayTime(PyObject *self, PyObject *args);
  	static PyObject *Seek(PyObject *self, PyObject *args);

	static PyObject *SetPyAdviceSink(PyObject *self, PyObject *args);
	static PyObject *SetPyVideoSurface(PyObject *self, PyObject *args);

	static PyObject *SetOsWindow(PyObject *self, PyObject *args);
	static PyObject *ShowInNewWindow(PyObject *self, PyObject *args);

protected:
	PlayerObject();
	~PlayerObject();
#if !defined(_ABIO32) || _ABIO32 == 0
	virtual string repr();
#else
	virtual char *repr();
#endif

private:
	bool SetContext();
	void ReleaseObjects();

	PyObject *pEngine;

	IRMAPlayer *pPlayer;
	IRMAErrorSink *pErrorSink;
	IRMAErrorSinkControl *pErrorSinkControl;
	ExampleClientContext *pContext;
};

PlayerObject::PlayerObject() :
	pEngine(NULL),
	pPlayer(NULL),
	pErrorSink(NULL),
	pErrorSinkControl(NULL),
	pContext(NULL)
{
}

PlayerObject::~PlayerObject()
{
	if (pContext)
		pContext->m_pClientSink->SetPyAdviceSink(NULL);
	if (pPlayer)
		pPlayer->Stop();
	ReleaseObjects();
}

PyObject *PlayerObject::CreateInstance(PyObject *engine, PyObject *args)
{
	CHECK_NO_ARGS(args);
	IRMAClientEngine *pClientEngine = GetEngine(engine);
	PlayerObject *obj = (PlayerObject*) RMAObject::make(PlayerObject::type);
	obj->pEngine = engine;
	Py_INCREF(engine);
	if (pClientEngine->CreatePlayer(obj->pPlayer) != PNR_OK) {
		PyErr_SetString(module_error,"CreatePlayer failed.");
		Py_DECREF(obj);
		return NULL;
	}
	obj->SetContext();
	return obj;
}

PyObject *PlayerObject_CreateInstance(PyObject *engine, PyObject *args)
{
	return PlayerObject::CreateInstance(engine, args);
}

#if !defined(_ABIO32) || _ABIO32 == 0
string
#else
char *
#endif
PlayerObject::repr()
{
	char buf[256];
	sprintf(buf, " instance 0x%X", this);
#if !defined(_ABIO32) || _ABIO32 == 0
	sprintf (buf, " instance 0x%X", this);
	return RMAObject::repr() + buf;
#else
	char *rep = RMAObject::repr();
	sprintf (buf, "%s instance 0x%X", rep, this);
	free(rep);
	return strdup(buf);
#endif
}

PyObject *
PlayerObject::OpenURL(PyObject *self, PyObject *args)
{
	PlayerObject* obj = (PlayerObject*)self;
	char *psz;
	PN_RESULT res;
	if (!PyArg_ParseTuple(args, "s", &psz))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	res=obj->pPlayer->OpenURL(psz);
	Py_END_ALLOW_THREADS
	return Py_BuildValue("i",res);
}

PyObject *
PlayerObject::Begin(PyObject *self, PyObject *args)
{
	PN_RESULT res;
	CHECK_NO_ARGS(args);
	Py_BEGIN_ALLOW_THREADS
	res=((PlayerObject*)self)->pPlayer->Begin();
	Py_END_ALLOW_THREADS
	return Py_BuildValue("i",res);
}

PyObject *
PlayerObject::Stop(PyObject *self, PyObject *args)
{
	PN_RESULT res;
	CHECK_NO_ARGS(args);
	Py_BEGIN_ALLOW_THREADS
	res=((PlayerObject*)self)->pPlayer->Stop();
	Py_END_ALLOW_THREADS
	return Py_BuildValue("i",res);
}

PyObject *
PlayerObject::Pause(PyObject *self, PyObject *args)
{
	PN_RESULT res;
	CHECK_NO_ARGS(args);
	Py_BEGIN_ALLOW_THREADS
	res=((PlayerObject*)self)->pPlayer->Pause();
	Py_END_ALLOW_THREADS
	return Py_BuildValue("i",res);
}

PyObject *
PlayerObject::IsDone(PyObject *self, PyObject *args)
{
	BOOL res;
	CHECK_NO_ARGS(args);
	Py_BEGIN_ALLOW_THREADS
	res=((PlayerObject*)self)->pPlayer->IsDone();
	Py_END_ALLOW_THREADS
	return Py_BuildValue("i",res);
}

PyObject *
PlayerObject::IsLive(PyObject *self, PyObject *args)
{
	BOOL res;
	CHECK_NO_ARGS(args);
	Py_BEGIN_ALLOW_THREADS
	res=((PlayerObject*)self)->pPlayer->IsLive();
	Py_END_ALLOW_THREADS
	return Py_BuildValue("i",res);
}

PyObject *
PlayerObject::GetCurrentPlayTime(PyObject *self, PyObject *args)
{
	ULONG32 res;
	CHECK_NO_ARGS(args);
	Py_BEGIN_ALLOW_THREADS
	res=((PlayerObject*)self)->pPlayer->GetCurrentPlayTime();
	Py_END_ALLOW_THREADS
	return Py_BuildValue("i",res);
}

PyObject *
PlayerObject::Seek(PyObject *self, PyObject *args)
{
	ULONG32 val;
	PN_RESULT res;
	if (!PyArg_ParseTuple(args, "i", &val))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	res=((PlayerObject*)self)->pPlayer->Seek(val);
	Py_END_ALLOW_THREADS
	return Py_BuildValue("i",res);
}

PyObject *
PlayerObject::SetPyAdviceSink(PyObject *self, PyObject *args)
{
	PyObject *obj;
	if (!PyArg_ParseTuple(args, "O", &obj))
		return NULL;
	ExampleClientContext *pCC = ((PlayerObject*)self)->pContext;
	if (pCC)
		pCC->m_pClientSink->SetPyAdviceSink(obj);
	RETURN_NONE;
}

// Support removed. 
PyObject *
PlayerObject::SetPyVideoSurface(PyObject *self, PyObject *args)
{
	PyObject *obj;
	if (!PyArg_ParseTuple(args, "O", &obj))
		return NULL;
	ExampleClientContext *pCC = ((PlayerObject*)self)->pContext;
//	if(pCC) {
//		ExampleSiteSupplier *ss=pCC->m_pSiteSupplier;
//		if(ss)ss->SetPyVideoSurface(obj);
//	}
	RETURN_NONE;
}

PyObject *
PlayerObject::SetOsWindow(PyObject *self, PyObject *args)
{
#ifdef _MACINTOSH
	WindowPtr hwnd;
	if (!PyArg_ParseTuple(args, "O&", WinObj_Convert, &hwnd))
		return NULL;
#else
	/* Windows */
	int hwnd;
	if (!PyArg_ParseTuple(args, "i", &hwnd))
		return NULL;
#endif
	ExampleClientContext *pCC = ((PlayerObject*)self)->pContext;
	if(pCC) {
		ExampleSiteSupplier *ss=pCC->m_pSiteSupplier;
		if (ss)
			ss->SetOsWindow((void*)hwnd);
	}
	RETURN_NONE;
}

PyObject *
PlayerObject::ShowInNewWindow(PyObject *self, PyObject *args)
{
	int f;
	if (!PyArg_ParseTuple(args, "i", &f))
		return NULL;
	ExampleClientContext *pCC = ((PlayerObject*)self)->pContext;
	if(pCC) {
		ExampleSiteSupplier *ss=pCC->m_pSiteSupplier;
		if (ss)
			ss->ShowInNewWindow(f);
	}
	RETURN_NONE;
}

static struct PyMethodDef PyRMPlayer_methods[] = {
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

bool
PlayerObject::SetContext()
{
	if ((pContext = new ExampleClientContext()) == NULL)
		return false;

	pContext->AddRef();

	pContext->Init(pPlayer);
	pPlayer->SetClientContext(pContext);

	pPlayer->QueryInterface(IID_IRMAErrorSinkControl, 
				(void**)&pErrorSinkControl);
	if (pErrorSinkControl) {	
		pContext->QueryInterface(IID_IRMAErrorSink, 
					 (void**) &pErrorSink);
		
		if (pErrorSink) {
			pErrorSinkControl->AddErrorSink(pErrorSink,
							PNLOG_EMERG,
							PNLOG_INFO);
		}
	}
	return true;
}

void
PlayerObject::ReleaseObjects()
{
	if (pErrorSinkControl) {
		pErrorSinkControl->RemoveErrorSink(pErrorSink);
		pErrorSinkControl->Release();
		pErrorSinkControl = NULL;
	}
	if (pContext) {
		pContext->Release();
		pContext = NULL;
	}
	if (pPlayer) {
		GetEngine(pEngine)->ClosePlayer(pPlayer);
		pPlayer->Release();
		pPlayer = NULL;
	}
	Py_DECREF(pEngine);
	pEngine = NULL;
}

