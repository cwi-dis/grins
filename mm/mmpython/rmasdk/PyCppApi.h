#ifndef INC_PYCPPAPI
#define INC_PYCPPAPI

// Cpp framework 
// for modules that export PyObjects

// For rapid-dev we borrow win32ui's core mechanisms
// we 'll revisit this module

// Using Std C++ (not MFC or other lib)

// Associations (a central win32ui mechanism) has been removed
// If the need arises, reimplement them in a cleaner not intrusive way


#include "Python.h"

// class SyncObject and CEnterLeavePython
#include "mt.h"

#if !defined(_ABIO32) || _ABIO32 == 0
#include "string"
#endif

inline void Trace(const char*, ...){}
#define TRACE Trace
#define ASSERT(f) ((void)0)

#ifdef _WINDOWS
#ifdef PY_EXPORTS
#define DLL_API __declspec(dllexport)
#else
#define DLL_API __declspec(dllimport)
#endif
#else
#define DLL_API
#endif
#define PY_API extern "C" DLL_API


////////////////////////////////////////////////
////////////////////////////////////////////////
// Helper Macros

#define MAKE_PY_CTOR(classname) static RMAObject * PyObConstruct()\
	{RMAObject* ret = new classname;return ret;}
#define GET_PY_CTOR(classname) classname::PyObConstruct

#define GET_THREAD_AND_DECREF(object) \
	if ((object) && (object)->ob_refcnt==1) { \
		CEnterLeavePython elp;Py_XDECREF((object)); \
	} else Py_XDECREF((object));

#define CHECK_NO_ARGS(args)		do {if (!PyArg_ParseTuple(args,"")) return NULL;} while (0)
#define CHECK_NO_ARGS2(args,fnName) do {if (!PyArg_ParseTuple(args,":"#fnName)) return NULL;} while (0)
#define RETURN_NONE				do {Py_INCREF(Py_None);return Py_None;} while (0)
#define RETURN_ERR(err)			do {PyErr_SetString(module_error,err);return NULL;} while (0)
#define RETURN_MEM_ERR(err)		do {PyErr_SetString(PyExc_MemoryError,err);return NULL;} while (0)
#define RETURN_TYPE_ERR(err)	do {PyErr_SetString(PyExc_TypeError,err);return NULL;} while (0)
#define RETURN_VALUE_ERR(err)	do {PyErr_SetString(PyExc_ValueError,err);return NULL;} while (0)

#define DOINCREF(o) Py_INCREF(o)
#define DODECREF(o) Py_DECREF(o)
#define XDODECREF(o) Py_XDECREF(o)

extern DLL_API PyObject *module_error;


////////////////////////////////////////////////
////////////////////////////////////////////////
// TypeObject

class RMAObject;
class DLL_API TypeObject : public PyTypeObject 
	{
	public:
	TypeObject(const char *name,TypeObject *pBaseType,int typeSize,
		struct PyMethodDef* methodList,RMAObject *(*thector)());
	~TypeObject();
	public:
	TypeObject *base;
	struct PyMethodDef* methods;
	RMAObject *(*ctor)();
	};


////////////////////////////////////////////////
////////////////////////////////////////////////
// RMAObject

class DLL_API RMAObject : public PyObject 
	{
	public:
	static RMAObject* make(TypeObject &type);

	// virtuals for Python support
#if !defined(_ABIO32) || _ABIO32 == 0
	virtual string repr();
#else
	virtual char *repr();
#endif
	virtual PyObject *getattr(char *name);
	virtual int setattr(char *name, PyObject *v);
	virtual void cleanup();

	static TypeObject type;	

	protected:
	RMAObject();
	virtual ~RMAObject();

	public:
	static BOOL is_object(PyObject*&,TypeObject *which);
	static BOOL is_nativeobject(PyObject *ob,TypeObject *which);

	BOOL is_object(TypeObject *which);
	static void so_dealloc(PyObject *ob);
	static PyObject *so_repr(PyObject *ob);
	static PyObject *so_getattr(PyObject *self,char *name);
	static int so_setattr(PyObject *op,char *name,PyObject *v);

	static PyObject* GetMethodByType(PyObject *self,PyObject *args);
	};


////////////////////////////////////////////////
////////////////////////////////////////////////
// CallerHelper

// Helper to call a method of a Python object.

class DLL_API CallerHelper
	{
	public:
	CallerHelper(const char *iname,PyObject *inst);
	~CallerHelper();

	BOOL HaveHandler() {return handler!=NULL;}
	void print_error();
	// All the "call" functions return FALSE if the call failed, or no handler exists.
	BOOL call();
	BOOL call(int);
	BOOL call(int, int);
	BOOL call(int, int, int);
	BOOL call(int, int, int, int);
	BOOL call(int, int, int, const char *);
	BOOL call(int val1, int val2, int val3, const char *val4, void* data);
	BOOL call(long);
	BOOL call(const char *);
	BOOL call(const char *, int);
	BOOL call(PyObject *);
	BOOL call(PyObject *, PyObject *);
	BOOL call(PyObject *, PyObject *, int);
	BOOL call_args(PyObject *arglst);
	// All the retval functions will ASSERT if the call failed!
	BOOL retval( int &ret );
	BOOL retval( long &ret );
	BOOL retval( PyObject* &ret );
	BOOL retval( char * &ret );
#if !defined(_ABIO32) || _ABIO32 == 0
	BOOL retval( string &ret );
#endif
	BOOL retnone();
	PyObject *GetHandler();
	
	private:
	BOOL do_call(PyObject *args);
	PyObject *handler;
	PyObject *retVal;
	PyObject *py_ob;
#if !defined(_ABIO32) || _ABIO32 == 0
	string csHandlerName;
#endif
	};

#endif

