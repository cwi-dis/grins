#ifndef INC_MTPYCALL
#define INC_MTPYCALL


/*
PyCallbackBlock:

PRE: The process requires a valid PyInterpreterState

1.	Create a new PyThreadState
	Acquire global interpreter lock

2.  Callback to python

3.	Release global interpreter lock
	Clear and delete thread state object
*/

#ifdef _WIN32

class PyCallbackBlock
	{
	public:
	PyCallbackBlock() 
		{
		m_tstate = PyThreadState_New(s_interpreterState);
		PyEval_AcquireThread(m_tstate);
		}
	~PyCallbackBlock() 
		{
		PyEval_ReleaseThread(m_tstate);
		PyThreadState_Clear(m_tstate);
		PyThreadState_Delete(m_tstate);
		}
	static void init()
		{
		PyEval_InitThreads(); // nop if already called
		if (s_interpreterState==NULL) 
			{
			PyThreadState *tstate = PyThreadState_Swap(NULL);	
			if (tstate==NULL)
				Py_FatalError("Can not get interpreter state.");
			s_interpreterState = tstate->interp;
			PyThreadState_Swap(tstate);
			}
		}
	private:
	PyThreadState *m_tstate;
	static PyInterpreterState *s_interpreterState;	
	};

#else // not WIN32

class PyCallbackBlock
	{
	public:
	PyCallbackBlock(){}
	static void init(){}
	static PyInterpreterState *s_interpreterState;	
	};

#endif  # WITH_THREAD

extern void seterror(const char *msg);

class CallbackHelper
	{
	public:
	CallbackHelper(const char *methodname,PyObject *obj)
	:	handler(NULL),
		py_ob(NULL),
		retVal(NULL)
		{
		if(!methodname || !obj) return;
		PyCallbackBlock cb;
		PyObject *t, *v, *tb;
		PyErr_Fetch(&t,&v,&tb);
		handler = PyObject_GetAttrString(obj,(char*)methodname);
		if (handler) 
			{
			if (!PyMethod_Check(handler)) 
				{
				Py_DECREF(handler);
				handler = NULL;
				}
			}
		PyErr_Restore(t,v,tb);
		py_ob = obj;
		Py_INCREF(py_ob);
		}
	~CallbackHelper()
		{
		if((retVal && retVal->ob_refcnt==1) || 
			(handler && handler->ob_refcnt==1) || 
			(py_ob && py_ob->ob_refcnt==1)) 
			{
			PyCallbackBlock cb;
			Py_XDECREF(retVal);
			Py_XDECREF(handler);
			Py_XDECREF(py_ob);
			} 
		else 
			{
			Py_XDECREF(retVal);
			Py_XDECREF(handler);
			Py_XDECREF(py_ob);
			}
		}
	BOOL cancall() const {return handler!=NULL;}
	BOOL call(PyObject *args)
		{
		if(!handler) return FALSE;
		PyCallbackBlock cb;
		Py_XDECREF(retVal);
		retVal = NULL;
		PyObject *result = PyEval_CallObject(handler,args);
		Py_DECREF(args);
		if (result==NULL) 
			{
			char msg[256];
			print_error();
			PyObject *obRepr = PyObject_Repr(handler);
			char *szRepr = PyString_AsString(obRepr);
			sprintf(msg, "handler (%s) raised an exception",szRepr);
			Py_XDECREF(obRepr);
			seterror(msg);
			print_error();
			return FALSE;
			}
		retVal = result;
		return TRUE;
		}

	
	private:	
		
	void print_error()
		{
		static BOOL bInError = FALSE;
		if (bInError) return;
		bInError=TRUE;

		PyObject *exception, *v, *tb;
		PyErr_Fetch(&exception, &v, &tb);
		PyErr_NormalizeException(&exception, &v, &tb);

		if (exception  && PyErr_GivenExceptionMatches(exception, PyExc_SystemExit)) 
			{
			Py_DECREF(exception);
			Py_XINCREF(PyExc_RuntimeError);
			PyErr_Restore(PyExc_RuntimeError, v, tb);
			} 
		else
			PyErr_Restore(exception, v, tb);
		PyErr_Print();
		bInError=FALSE;
		}
	
	PyObject *handler;
	PyObject *retVal;
	PyObject *py_ob;	
	};

#endif // INC_MTPYCALL

