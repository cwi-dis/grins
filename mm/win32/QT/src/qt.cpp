
/*************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

****************************************************************************/

// python
#include "Python.h"

// windows
#include <windows.h>
#include <wtypes.h>
#include <assert.h>

#include "util.h"

// QT
#include "QTML.h"
#include "Movies.h"
#include "TextUtils.h"

static PyObject *ErrorObject;

void seterror(const char *msg){PyErr_SetString(ErrorObject, msg);}


///////////////////////////////////////////
///////////////////////////////////////////
// Objects

struct GrafPtrObject
	{
	PyObject_HEAD
	GrafPtr grafPtr;
	static void Initialize(GrafPtrObject *p){p->grafPtr = NULL;}
	static void Release(GrafPtrObject *p)
		{
		if(p && p->grafPtr) DestroyPortAssociation((CGrafPtr)p->grafPtr);
		}
	};
staticforward python_type_object<GrafPtrObject> grafPtrType;


struct ComponentInstanceObject
	{
	PyObject_HEAD
	ComponentInstance componentInstance;
	static void Initialize(ComponentInstanceObject *p){p->componentInstance = NULL;}
	static void Release(ComponentInstanceObject *p)
		{
		if(p && p->componentInstance)
			DisposeMovieController(p->componentInstance);
		}
	};
staticforward python_type_object<ComponentInstanceObject> componentInstanceType;


struct MovieObject
	{
	PyObject_HEAD
	Movie movie;
	static void Initialize(MovieObject *p){p->movie = NULL;}
	static void Release(MovieObject *p)
		{
		if(p && p->movie)
			DisposeMovie(p->movie);
		}
	};
staticforward python_type_object<MovieObject> movieType;


///////////////////////////////////////////
///////////////////////////////////////////
// Implementation


//////////////////////////////////////////////
// GrafPtr

static struct PyMethodDef GrafPtr_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static python_type_object<GrafPtrObject> 
grafPtrType("PyGrafPtr", GrafPtr_methods, "QuickTime GrafPtr");


//////////////////////////////////////////////
// ComponentInstance

static struct PyMethodDef ComponentInstance_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static python_type_object<ComponentInstanceObject> 
componentInstanceType("PyComponentInstance", ComponentInstance_methods, "QuickTime ComponentInstance");


//////////////////////////////////////////////
// Movie

static struct PyMethodDef MovieObject_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static python_type_object<MovieObject> 
movieType("PyMovieObject", MovieObject_methods, "QuickTime Movie");


/////////////////////////////////////////////
// QT Module

static char Initialize__doc__[] =
"Initialize() : None"
;
static PyObject*
Initialize(PyObject *self, PyObject *args) 
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;

	// Initialize QuickTime Media Layer.
    InitializeQTML(kInitializeQTMLUseGDIFlag);
        
	// Initialize QuickTime.
	EnterMovies();

	Py_INCREF(Py_None);
	return Py_None;
	}

static char Terminate__doc__[] =
"Terminate(): None"
;
static PyObject*
Terminate(PyObject *self, PyObject *args) 
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;

	// Terminate QuickTime.
	ExitMovies();
        
	// Terminate QuickTime Media Layer.
	TerminateQTML();

	Py_INCREF(Py_None);
	return Py_None;
	}

static char CreatePortAssociation__doc__[] =
"CreatePortAssociation(HWND) : PyGrafPtr"
;
static PyObject*
CreatePortAssociation(PyObject *self, PyObject *args) 
	{
	HWND hwnd;
	if (!PyArg_ParseTuple(args, "i", &hwnd))
		return NULL;

	GrafPtrObject *obj = grafPtrType.makeObject();
	obj->grafPtr = CreatePortAssociation((void*)hwnd, NULL, kQTMLHandlePortEvents);
	
	// Set graphics port
	SetGWorld(CGrafPtr(GetNativeWindowPort(hwnd)), NULL); 

	return (PyObject*)obj;
	}

static char CreateMovie__doc__[] =
"CreateMovie(filename) : PyMovie"
;
static PyObject*
CreateMovie(PyObject *self, PyObject *args) 
	{
	char *psz;
	if (!PyArg_ParseTuple(args, "s", &psz))
		return NULL;

	MovieObject *obj = movieType.makeObject();

	short theFile = 0;
	FSSpec sfFile;
	FSMakeFSSpec (0, 0L, c2pstr(psz), &sfFile);
	// Open movie file
	OpenMovieFile (&sfFile, &theFile, fsRdPerm);
	
	// Get movie from file
	NewMovieFromFile (&obj->movie, theFile, nil, nil, newMovieActive, nil);

	// Close movie file
	CloseMovieFile(theFile);

	return (PyObject*)obj;
	}

static char CreateController__doc__[] =
"CreateController(PyMovie): PyComponentInstance"
;
static PyObject*
CreateController(PyObject *self, PyObject *args) 
	{
	MovieObject *movieObj;
	if (!PyArg_ParseTuple(args, "O", &movieObj))
		return NULL;
	
	ComponentInstanceObject *obj = componentInstanceType.makeObject();
	Rect theMovieRect;
	
	// 0,0 movie coordinates.
	GetMovieBox(movieObj->movie, &theMovieRect);

    obj->componentInstance = NewMovieController(movieObj->movie, &theMovieRect, mcTopLeftMovie | mcWithFrame);
            
	// Allow the controller to accept keyboard events.
    MCDoAction(obj->componentInstance, mcActionSetKeysEnabled, (void *)TRUE);

	return (PyObject*)obj;
	}

static char WinEventToMacEvent__doc__[] =
"WinEventToMacEvent(PyComponentInstance, HWND, message, wParam, lParam): None"
;
static PyObject*
WinEventToMacEvent(PyObject *self, PyObject *args) 
	{
	ComponentInstanceObject *obj;
	HWND hwnd;
	UINT message;
	WPARAM wParam;
	LPARAM lParam;
	long time;
	POINT pt;
	if (!PyArg_ParseTuple(args, "O(iiiii(ii))", &obj, &hwnd, &message,&wParam,&lParam, &time, &pt.x, &pt.y))
		return NULL;
	MSG msg;
    msg.hwnd = hwnd;
    msg.message = message;
    msg.wParam = wParam;
    msg.lParam = lParam;
    msg.time = time; 
	msg.pt = pt;
	EventRecord qtmlEvent;
	WinEventToMacEvent(&msg, &qtmlEvent);
	Py_BEGIN_ALLOW_THREADS
	MCIsPlayerEvent(obj->componentInstance, &qtmlEvent);
	Py_END_ALLOW_THREADS
	Py_INCREF(Py_None);
	return Py_None;
	}

static char MCDraw__doc__[] =
"MCDraw(PyComponentInstance, PyGrafPtr) : None"
;
static PyObject*
MCDraw(PyObject *self, PyObject *args) 
	{
	ComponentInstanceObject *cObj;
	GrafPtrObject *gpObj;
	if (!PyArg_ParseTuple(args, "OO", &cObj, &gpObj))
		return NULL;
	MCDraw(cObj->componentInstance, gpObj->grafPtr);
	Py_INCREF(Py_None);
	return Py_None;
	}


static struct PyMethodDef qt_methods[] = {
	{"Initialize", (PyCFunction)Initialize, METH_VARARGS, Initialize__doc__},
	{"Terminate", (PyCFunction)Terminate, METH_VARARGS, Terminate__doc__},
	{"CreatePortAssociation", (PyCFunction)CreatePortAssociation, METH_VARARGS, CreatePortAssociation__doc__},
	{"CreateMovie", (PyCFunction)CreateMovie, METH_VARARGS, CreateMovie__doc__},
	{"CreateController", (PyCFunction)CreateController, METH_VARARGS, CreateController__doc__},
	{"WinEventToMacEvent", (PyCFunction)WinEventToMacEvent, METH_VARARGS, WinEventToMacEvent__doc__},
	{"MCDraw", (PyCFunction)MCDraw, METH_VARARGS, MCDraw__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static char qt_module_documentation[] =
"QuickTime module"
;

extern "C" __declspec(dllexport)
void initqt()
{
	PyObject *m, *d;
	bool bPyErrOccurred = false;
	
	// Create the module and add the functions
	m = Py_InitModule4("qt", qt_methods,
		qt_module_documentation,
		(PyObject*)NULL, PYTHON_API_VERSION);

	// add 'error'
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("qt.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	// Check for errors
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module qt");
}
