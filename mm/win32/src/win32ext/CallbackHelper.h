#ifndef INC_CALLBACKHELPER
#define INC_CALLBACKHELPER

// A version of the win32ui original CVirtualHelper 
// that does not use associations

extern PyObject *ui_module_error;

class CallbackHelper
	{
	public:
	CallbackHelper(const char *iname,PyObject *inst);
	~CallbackHelper();

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
	BOOL retval( CString &ret );
	BOOL retnone();
	PyObject *GetHandler();
	
	private:
	BOOL do_call(PyObject *args);
	PyObject *handler;
	PyObject *retVal;
	PyObject *py_ob;
	CString csHandlerName;
	};

inline CallbackHelper::CallbackHelper(const char *methodname,PyObject *obj)
:	handler(NULL),
	py_ob(NULL),
	retVal(NULL)
	{
	if(!methodname || !obj) return;
	csHandlerName = methodname;
	CEnterLeavePython elp;
	PyObject *t, *v, *tb;
	PyErr_Fetch(&t,&v,&tb);
	handler = PyObject_GetAttrString(obj,(char*)methodname);
	if (handler) 
		{
		// explicitely check a method returned, else the classes
		// delegation may cause a circular call chain.
		if (!PyMethod_Check(handler)) 
			{
			if (!PyCFunction_Check(handler))
				TRACE("Handler for object is not a method!\n");
			DODECREF(handler);
			handler = NULL;
			}
		}
	PyErr_Restore(t,v,tb);
	py_ob = obj;
	Py_INCREF(py_ob);
	//Py_XINCREF(handler);
	}
inline CallbackHelper::~CallbackHelper()
	{
	// XXX - Gross hack for speed.  This is called for eachh window message
	// so only grabs the Python lock if the objects need Python,
	if((retVal && retVal->ob_refcnt==1) || 
		(handler && handler->ob_refcnt==1) || 
		(py_ob && py_ob->ob_refcnt==1)) 
		{
		CEnterLeavePython _celp;
		XDODECREF(retVal);
		XDODECREF(handler);
		XDODECREF(py_ob);
		} 
	else 
		{
		XDODECREF(retVal);
		XDODECREF(handler);
		XDODECREF(py_ob);
		}
	}
inline PyObject *CallbackHelper::GetHandler()
	{
	return handler;
	}
inline BOOL CallbackHelper::do_call(PyObject *args)
	{
	CEnterLeavePython _celp;
	XDODECREF(retVal);	// our old one.
	retVal = NULL;
	ASSERT(handler);	// caller must trap this.
	ASSERT(args);
	PyObject *result = PyEval_CallObject(handler,args);
	DODECREF(args);
	if (result==NULL) 
		{
		char msg[256];
		TRACE("CallVirtual : callback failed with exception\n");
		print_error();
		PyObject *obRepr = PyObject_Repr(handler);
		char *szRepr = PyString_AsString(obRepr);
		sprintf(msg, "%s() virtual handler (%s) raised an exception",csHandlerName, szRepr);
		Py_XDECREF(obRepr);
		PyErr_SetString(ui_module_error, msg);
		print_error();
		return FALSE;
		}
	retVal = result;
	return TRUE;
	}

inline BOOL CallbackHelper::call_args(PyObject *arglst)
	{
	if (!handler) return FALSE;
	return do_call(arglst);
	}

inline BOOL CallbackHelper::call()
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("()");
	return do_call(arglst);
	}

inline BOOL CallbackHelper::call(int val)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(i)",val);
	return do_call(arglst);
	}

inline BOOL CallbackHelper::call(int val1, int val2)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(ii)",val1, val2);
	return do_call(arglst);
	}

inline BOOL CallbackHelper::call(int val1, int val2, int val3)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(iii)",val1, val2, val3);
	return do_call(arglst);
	}

inline BOOL CallbackHelper::call(int val1, int val2, int val3, int val4)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(iiii)",val1, val2, val3, val4);
	return do_call(arglst);
	}

inline BOOL CallbackHelper::call(int val1, int val2, int val3, const char *val4)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(iiiz)",val1, val2, val3, val4);
	return do_call(arglst);
	}

inline BOOL CallbackHelper::call(int val1, int val2, int val3, const char *val4, void* data)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(iiizl)",val1, val2, val3, val4, data);
	return do_call(arglst);
	}

inline BOOL CallbackHelper::call(long val)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(l)",val);
	return do_call(arglst);
	}

inline BOOL CallbackHelper::call(const char *val)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(z)",val);
	return do_call(arglst);
	}

inline BOOL CallbackHelper::call(const char *val, int ival)
	{
	if(!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(zi)",val,ival);
	return do_call(arglst);
	}

inline BOOL CallbackHelper::call(PyObject *ob)
	{
	if (!handler) return FALSE;
	if (!ob) ob=Py_None;
	PyObject *arglst = Py_BuildValue("(O)",ob);
	return do_call(arglst);
	}

inline BOOL CallbackHelper::call(PyObject *ob, PyObject *ob2)
	{
	if (!handler) return FALSE;
	if (!ob)ob=Py_None;
	if (!ob2)ob2=Py_None;
	PyObject *arglst = Py_BuildValue("(OO)",ob, ob2);
	return do_call(arglst);
	}

inline BOOL CallbackHelper::call(PyObject *ob, PyObject *ob2, int i)
	{
	if (!handler) return FALSE;
	if (!ob)
		ob=Py_None;
	if (!ob2)
		ob2=Py_None;
	PyObject *arglst = Py_BuildValue("(OOi)",ob, ob2, i);
	return do_call(arglst);
	}

inline BOOL CallbackHelper::retnone()
	{
	ASSERT(retVal);
	if (!retVal)
		return FALSE;	// failed - assume didnt work in non debug
	return (retVal==Py_None);
	}

inline BOOL CallbackHelper::retval( int &ret )
	{
	ASSERT(retVal);
	if (!retVal)
		return FALSE;	// failed - assume didnt work in non debug
	if (retVal==Py_None) 
		{
		ret = 0;
		return TRUE;
		}
	CEnterLeavePython _celp;
	ret = PyInt_AsLong(retVal);
	return !PyErr_Occurred();
	}

inline BOOL CallbackHelper::retval( long &ret )
	{
	ASSERT(retVal);
	if (!retVal)
		return FALSE;	// failed - assume didnt work in non debug
	if (retVal==Py_None) 
		{
		ret = 0;
		return TRUE;
		}
	CEnterLeavePython _celp;
	ret = PyInt_AsLong(retVal);
	if (PyErr_Occurred()) 
		{
		PyErr_Clear();
		return FALSE;
		}
	return TRUE;
	}

inline BOOL CallbackHelper::retval( char *&ret )
	{
	ASSERT(retVal);
	if (!retVal)
		return FALSE;	// failed - assume didnt work in non debug
	if (retVal==Py_None) 
		{
		ret = NULL;
		return TRUE;
		}
	CEnterLeavePython _celp;
	ret = PyString_AsString(retVal);
	if (PyErr_Occurred()) 
		{
		PyErr_Clear();
		return FALSE;
		}
	return TRUE;
	}

inline BOOL CallbackHelper::retval(CString &ret)
	{
	ASSERT(retVal);
	if (!retVal)
		return FALSE;	// failed - assume didnt work in non debug
	if (retVal==Py_None) 
		{
		ret="";
		return TRUE;
		}
	CEnterLeavePython elp;
	ret = PyString_AsString(retVal);
	if (PyErr_Occurred()) 
		{
		PyErr_Clear();
		return FALSE;
		}
	return TRUE;
	}

inline BOOL CallbackHelper::retval(_object* &ret)
	{
	ASSERT(retVal);
	if (!retVal)
		return FALSE;	// failed - assume didnt work in non debug
	CEnterLeavePython elp;
	if (!PyArg_Parse(retVal, "O",&ret)) 
		{
		PyErr_Clear();
		return FALSE;
		}
	return TRUE;
	}

inline void CallbackHelper::print_error()
	{
	// basic recursion control.
	static BOOL bInError = FALSE;
	if (bInError) return;
	bInError=TRUE;

	// Check if the exception is SystemExit - if so,
	// PyErr_Print will terminate then and there!  This is
	// not good (and not what we want!?
	PyObject *exception, *v, *tb;
	PyErr_Fetch(&exception, &v, &tb);
	PyErr_NormalizeException(&exception, &v, &tb);

	if (exception  && PyErr_GivenExceptionMatches(exception, PyExc_SystemExit)) 
		{
		// Replace it with a RuntimeError.
		TRACE("WARNING!!  SystemError - Replacing with RuntimeError!!\n");
		Py_DECREF(exception);
		Py_XINCREF(PyExc_RuntimeError);
		PyErr_Restore(PyExc_RuntimeError, v, tb);
		} 
	else
		PyErr_Restore(exception, v, tb);
	// Now print it.

	PyErr_Print();
	bInError=FALSE;
	}

#endif // INC_CALLBACKHELPER