#ifndef INC_PYCBAPI
#define INC_PYCBAPI

/*
Comments on the Python callback process 
implemented by class PyCallbackBlock:

PyCallbackBlock is the same for now 
as CEnterLeavePython of PyWinTypes 
but the code is in one place.

The process requires a valid PyInterpreterState

1.	Look for a PyThreadState for this thread at 
	thread's local storage (tls)
	if found
		set newblock = false
	else 
		set newblock = true
		create a new PyThreadState and save it to tls
	Acquire global interpreter lock (PyEval_AcquireThread)

2.  Callback to python

3. 	Get stored PyThreadState from tls
	(to be used as a check in PyEval_ReleaseThread)
	Release global interpreter lock (PyEval_ReleaseThread)
	if newblock:
		a) Reset all information in the thread state object
		b) Clean tls
*/

class PyCallbackBlock
	{
	public:
	PyCallbackBlock() 
		{
		ThreadData *ptd = (ThreadData*)TlsGetValue(0);
		if(!ptd)
			{
			ptd = (ThreadData *)LocalAlloc(LMEM_ZEROINIT,sizeof(ThreadData));
			TlsSetValue(0,ptd);
			ptd->ts = PyThreadState_New(s_pPyThreadState);
			m_bIsNewBlock=true;
			}
		else m_bIsNewBlock=false;
		PyEval_AcquireThread(ptd->ts);
		}
	~PyCallbackBlock() 
		{
		ThreadData *ptd = (ThreadData*)TlsGetValue(0);
		if(!ptd) return;
		PyEval_ReleaseThread(ptd->ts);
		if(m_bIsNewBlock)
			{
			if(ptd->ts)
				{
				PyThreadState_Clear(ptd->ts);
				PyThreadState_Delete(ptd->ts);
				}
			TlsSetValue(0,NULL);
			LocalFree(ptd);
			}
		}
	static void init()
		{
		if (s_pPyThreadState==NULL) 
			{
			PyThreadState *pPyThreadState = PyThreadState_Swap(NULL);
			if (pPyThreadState==NULL)
				Py_FatalError("Python interpreter state is invalid");
			s_pPyThreadState = pPyThreadState->interp;
			PyThreadState_Swap(pPyThreadState);
			}
		}
	static void free()
		{
		ThreadData *ptd = (ThreadData*)TlsGetValue(0);
		if(!ptd) return;
		if(ptd->ts)PyThreadState_Delete(ptd->ts);
		TlsSetValue(0, NULL);
		LocalFree(ptd);
		}
	
	private:
	bool m_bIsNewBlock;
	struct ThreadData {PyThreadState *ts;};
	static PyInterpreterState *s_pPyThreadState;	
	};


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
		if(handler)
			{
			py_ob = obj;
			Py_INCREF(py_ob);
			}
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



#endif // INC_PYCBAPI




