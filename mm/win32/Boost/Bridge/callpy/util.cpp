
#include "Python.h"

#include <windows.h>

#include "stdenv.h"

namespace python {
	
static PyThreadState *g_tstate = NULL;

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

// must own global interpreter lock 
void report_error()
	{
	PyObject *type, *value, *traceback;
	PyErr_Fetch(&type, &value, &traceback);
		
	std::cout << std::endl;
	PyObject *ob = PyObject_Str(type);
	char *psz = PyString_AsString(ob);
	std::cout << psz << std::endl;

	ob = PyObject_Str(value);
	psz = PyString_AsString(ob);
	std::cout << psz << std::endl;

	ob = PyObject_Str(traceback);
	psz = PyString_AsString(ob);
	std::cout << psz << std::endl;
	std::cout << std::endl;
	
	PyErr_Restore(type, value, traceback);
	}

bool initialize(int argc, char **argv, char *python_home)
	{
	if (g_tstate) return true;
	
	std::cout << "Python " << Py_GetVersion() << std::endl << Py_GetCopyright() 
			<< std::endl << std::endl;

	Py_SetPythonHome(python_home);
	
	Py_SetProgramName(argv[0]);

	// Initialize the interpreter
	Py_Initialize(); 
	
	// Set argc, argv
	PySys_SetArgv(argc, argv);

	// Create and acquire the interpreter lock
	PyEval_InitThreads();

	// Release the thread state
	g_tstate = PyEval_SaveThread();
	
	return g_tstate!=NULL;
	}

void finalize()
	{
	if (g_tstate) 
		{
		PyEval_AcquireThread(g_tstate);
		g_tstate = NULL;
		Py_Finalize();
		}
	}

bool get_sys_path(std::list<std::string>& path)
	{
	AcquireThread at(g_tstate);
	PyObject *p = PySys_GetObject("path");
	if (!PyList_Check(p))
		return false;
	int n = PyList_Size(p);
	for(int i=0; i!=n; i++)
		{
		char *entry = PyString_AsString(PyList_GetItem(p, i));
		path.push_back(entry);
		}
	return true;
	}

bool addto_sys_path(const char *folder)
	{
	std::list<std::string> existing;
	if(!get_sys_path(existing))
		return false;

	AcquireThread at(g_tstate);
	PyObject *p = PySys_GetObject("path");
	if (!PyList_Check(p))
		return false;

	if(std::find(existing.begin(),existing.end(), folder) == existing.end())
		{
		PyObject *obj = PyString_FromString(const_cast<char*>(folder));
		PyList_Insert(p, 0, obj);
		Py_DECREF(obj);
		}
	return true;
	}

bool addto_sys_path(const std::list<std::string>& path)
	{
	std::list<std::string> existing;
	if(!get_sys_path(existing))
		return false;

	AcquireThread at(g_tstate);
	PyObject *p = PySys_GetObject("path");
	if (!PyList_Check(p))
		return false;
	for(std::list<std::string>::const_iterator it=path.begin();it!=path.end();it++)
		{
		if(std::find(existing.begin(),existing.end(), *it) == existing.end())
			{
			PyObject *obj = PyString_FromString(const_cast<char*>((*it).c_str()));
			PyList_Insert(p, 0, obj);
			Py_DECREF(obj);
			}
		}
	return true;
	}

bool run_command(const char *command)
	{
	AcquireThread at(g_tstate);
	PyObject *m = PyImport_AddModule("__main__");
	if (m == NULL)
		{
		report_error();
		return false;
		}
	PyObject *d = PyModule_GetDict(m);
	PyObject *v = PyRun_String(const_cast<char*>(command), Py_file_input, d, d);
	if(v == NULL)
		{
		report_error();
		return false;
		}

	Py_XDECREF(v);
	return true;
	}

}  // namespace python

