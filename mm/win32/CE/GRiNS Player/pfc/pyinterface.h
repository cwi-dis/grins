#ifndef INC_PYINTERFACE
#define INC_PYINTERFACE

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

#ifndef _WINDOWS_
#include <windows.h>
#endif

#pragma warning(disable: 4786) // long names trunc (debug)
#pragma warning(disable: 4018) // signed/unsigned mismatch
#include <list>
#include <string>
#include <algorithm>

class PyInterface
	{
	public:
	static void setPythonHome(const TCHAR *python_home);
	static const TCHAR* getPythonHome();

	static bool initialize(const TCHAR *progname);
	static bool initialize(const TCHAR *progname, const TCHAR *cmdline);
	static bool initialize(int argc, char **argv);
	static void finalize();

	static bool get_sys_path(std::list< std::basic_string<TCHAR> >& path);
	static bool addto_sys_path_dir(const TCHAR *dir);
	static bool addto_sys_path(const std::list< std::basic_string<TCHAR> >& path);
	static bool addto_sys_path(const TCHAR *pszpath);

	static bool run_command(const TCHAR *command);
	static bool run_file(const TCHAR *filename);

	static PyObject* import(const TCHAR *psztmodule);
	static std::basic_string<TCHAR> get_copyright();

	static PyThreadState* getPyThreadState() { return s_tstate;}
	static PyObject* getErrorObject() { return s_errorObject;}

	private:
	static PyThreadState *s_tstate;
	static char s_python_home[MAX_PATH];
	static PyObject *s_errorObject;
	};

struct AcquireThread
	{
	AcquireThread(PyThreadState *tstate)
	:	m_tstate(tstate)
		{
		PyEval_AcquireThread(m_tstate);
		}
	~AcquireThread()
		{
		PyEval_ReleaseThread(m_tstate);
		}
	PyThreadState *m_tstate;
	};

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
	static bool init(PyThreadState *tstate)
		{
		PyEval_AcquireThread(tstate);
		s_interpreterState = tstate->interp;
		PyEval_ReleaseThread(tstate);
		return true;
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

struct PyExcInfo 
	{
	PyObject *type;
	PyObject *value;
	PyObject *traceback;
	PyExcInfo()
		{
		PyErr_Fetch(&type, &value, &traceback);
		PyErr_NormalizeException(&type, &value, &traceback);
		}
	~PyExcInfo()
		{
		Py_XDECREF(type);
		Py_XDECREF(value);
		Py_XDECREF(traceback);
		PyErr_Restore(type, value, traceback);
		}
	std::basic_string<TCHAR> getShortMsg();
	std::basic_string<TCHAR> getMsg();
	std::basic_string<TCHAR> getTraceback();
	};

struct PyObjectWrapper
	{
	typedef PyObject* PyObjectPtr;
	PyObject *m_obj;

	PyObjectWrapper(PyObject *obj = NULL) : m_obj(obj) {}

	PyObjectWrapper(const char *name) 
	:	m_obj(PyImport_ImportModule(const_cast<char*>(name))) {}

	~PyObjectWrapper() { Py_XDECREF(m_obj);}

	PyObject* GetAttr(const char *name)
		{
		return PyObjectWrapper(PyObject_GetAttrString(m_obj, const_cast<char*>(name)));
		}
	
	PyObject* Call(PyObject *args = NULL)
		{
		return PyObject_CallObject(m_obj, args);
		}

	const PyObjectWrapper& operator=(PyObject* obj)
		{
		Py_XDECREF(obj);
		m_obj = obj;
		return *this;
		}

	std::basic_string<TCHAR> toString();

	operator void const*() const {return (m_obj==NULL)?0:this;}

	PyObject& operator*() const { return *m_obj;}

	PyObjectPtr operator->() const  {return m_obj;}

	operator PyObjectPtr() {return m_obj;}
	};

inline void PyErr_Show() { PyErr_Print();}

inline PyObject* none() {Py_INCREF(Py_None); return Py_None;}

inline void seterror(const char *msg){ PyErr_SetString(PyInterface::getErrorObject(), msg);}

inline void seterror(const char *funcname, const char *msg)
	{
	PyErr_Format(PyInterface::getErrorObject(), "%s failed, %s", funcname, msg);
	PyErr_SetString(PyInterface::getErrorObject(), msg);
	}

inline void seterror(const char *funcname, DWORD err)
	{
	char* pszmsg;
	FormatMessage( 
		 FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
		 NULL,
		 err,
		 MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
		 (LPTSTR) &pszmsg,
		 0,
		 NULL 
		);
	PyErr_Format(PyInterface::getErrorObject(), "%s failed, error = %x, %s", funcname, err, pszmsg);
	LocalFree(pszmsg);
	}


#endif // INC_PYINTERFACE
