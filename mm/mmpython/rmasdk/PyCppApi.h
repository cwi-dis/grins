#ifndef INC_PYCPPAPI
#define INC_PYCPPAPI

// Cpp framework 
// for modules that export PyObjects

// For rapid-dev we borrow win32ui's core mechanisms
// we 'll revisit this module

// Using Std C++ (not MFC or other lib)

// Associations (a central win32ui mechanism) has been removed
// If the need arises, reimplement them in a cleaner not intrusive way


#ifndef Py_PYTHON_H
#include "Python.h"
#endif

// class SyncObject and CEnterLeavePython
#ifndef INC_MT
#include "mt.h"
#endif


inline void Trace(const char*, ...){}
#define TRACE Trace
#define ASSERT(f) ((void)0)

#ifdef PY_EXPORTS
#define DLL_API __declspec(dllexport)
#else
#define DLL_API __declspec(dllimport)
#endif
#define PY_API extern "C" DLL_API


////////////////////////////////////////////////
////////////////////////////////////////////////
// Helper Macros

#define MAKE_PY_CTOR(classname) static Object * PyObConstruct()\
	{Object* ret = new classname;return ret;}
#define GET_PY_CTOR(classname) classname::PyObConstruct

#define BGN_SAVE PyThreadState *_save = PyEval_SaveThread()
#define END_SAVE PyEval_RestoreThread(_save)
#define BLOCK_THREADS Py_BLOCK_THREADS

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

class Object;
class DLL_API TypeObject : public PyTypeObject 
	{
	public:
	TypeObject(const char *name,TypeObject *pBaseType,int typeSize,
		struct PyMethodDef* methodList,Object *(*thector)());
	~TypeObject();
	public:
	TypeObject *base;
	struct PyMethodDef* methods;
	Object *(*ctor)();
	};


////////////////////////////////////////////////
////////////////////////////////////////////////
// Object

class DLL_API Object : public PyObject 
	{
	public:
	static Object* make(TypeObject &type);

	// virtuals for Python support
	virtual string repr();
	virtual PyObject *getattr(char *name);
	virtual int setattr(char *name, PyObject *v);
	virtual void cleanup();
#ifdef MS_WIN32
	static struct PyMethodDef Object::empty_methods[];
#endif
	static TypeObject type;	

	protected:
	Object();
	virtual ~Object();

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
	BOOL retval( string &ret );
	BOOL retnone();
	PyObject *GetHandler();
	
	private:
	BOOL do_call(PyObject *args);
	PyObject *handler;
	PyObject *retVal;
	PyObject *py_ob;
	string csHandlerName;
	};

#endif

