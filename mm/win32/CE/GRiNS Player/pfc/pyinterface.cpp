#include "Python.h"

#include <windows.h>

#include "pyinterface.h"

#include "charconv.h"

PyThreadState* PyInterface::s_tstate = NULL;
char PyInterface::s_python_home[MAX_PATH] = "";
PyObject* PyInterface::s_errorObject = NULL;

PyInterpreterState* PyCallbackBlock::s_interpreterState = NULL;

void PyInterface::setPythonHome(const TCHAR *python_home)
	{
	strcpy(s_python_home, toMB(python_home));
	Py_SetPythonHome(s_python_home);
	}

const TCHAR* PyInterface::getPythonHome()
	{
	char *python_home = Py_GetPythonHome();
	if(python_home == NULL)
		return NULL;
	return toTEXT(python_home);
	}

bool PyInterface::initialize(const TCHAR *progname)
	{
	char* bprogname = const_cast<char*>(toMB(progname));
	return initialize(1, &bprogname);
	}

bool PyInterface::initialize(const TCHAR *progname, const TCHAR *cmdline)
	{
	// xxx: parse cmdline
	char* bprogname = const_cast<char*>(toMB(progname));
	return initialize(1, &bprogname);
	}

bool PyInterface::initialize(int argc, char **argv)
	{
	if (s_tstate != NULL) 
		return true;
	
#ifndef _WIN32_WCE
	if(getPythonHome() == NULL)
		return false;
#endif

	/*
	std::cout << "Python " << Py_GetVersion() << std::endl << Py_GetCopyright() 
			<< std::endl << std::endl;

	char python_home[256];
	get_ini_entry("GENERAL", "PYTHONHOME", python_home, 256);
	if(python_home[0] != '\0')
		Py_SetPythonHome(python_home);
	*/

	Py_SetProgramName(argv[0]);

	// Initialize the interpreter
	Py_Initialize(); 
	
	// Set argc, argv
	PySys_SetArgv(argc, argv);

	// Create and acquire the interpreter lock
	PyEval_InitThreads();

	
	//
	s_errorObject = PyString_FromString("pyinterface.error");

	// Release the thread state
	s_tstate = PyEval_SaveThread();
	
	// init callback block
	PyCallbackBlock::init(s_tstate);

	// add site ini path
	/*
	const int max_path_len = 2048;
	char *pathbuf = new char[max_path_len];
	get_ini_entry("GENERAL", "PYTHONPATH", pathbuf, max_path_len);
	if(pathbuf[0] != '\0')
		addto_sys_path(pathbuf);
	delete[] pathbuf;
	*/
	return s_tstate!=NULL;
	}

void PyInterface::finalize()
	{
	if (s_tstate) 
		{
		PyEval_AcquireThread(s_tstate);
		s_tstate = NULL;
		Py_Finalize();
		}
	}

std::basic_string<TCHAR> PyInterface::get_copyright()
	{
	std::basic_string<TCHAR> tstr(TEXT("Python "));
	tstr += toTEXT(Py_GetVersion());
	tstr += TEXT("\r\n");
	tstr += toTEXT(Py_GetCopyright());
	tstr += TEXT("\r\n");
	return tstr;
	}

bool PyInterface::get_sys_path(std::list< std::basic_string<TCHAR> >& path)
	{
	AcquireThread at(s_tstate);
	PyObject *p = PySys_GetObject("path");
	if (!PyList_Check(p))
		return false;
	int n = PyList_Size(p);
	for(int i=0; i!=n; i++)
		{
		char *entry = PyString_AsString(PyList_GetItem(p, i));
		path.push_back(toTEXT(entry));
		}
	return true;
	}

bool PyInterface::addto_sys_path_dir(const TCHAR *dir)
	{
	std::list< std::basic_string<TCHAR> > existing;
	if(!get_sys_path(existing))
		return false;

	AcquireThread at(s_tstate);
	PyObject *p = PySys_GetObject("path");
	if (!PyList_Check(p))
		return false;

	if(std::find(existing.begin(),existing.end(), dir) == existing.end())
		{
		PyObject *obj = PyString_FromString(const_cast<char*>(toMB(dir)));
		PyList_Insert(p, 0, obj);
		Py_DECREF(obj);
		}
	return true;
	}

bool PyInterface::addto_sys_path(const std::list< std::basic_string<TCHAR> >& path)
	{
	std::list< std::basic_string<TCHAR> > existing;
	if(!get_sys_path(existing))
		return false;

	AcquireThread at(s_tstate);
	PyObject *p = PySys_GetObject("path");
	if (!PyList_Check(p))
		return false;
	std::list< std::basic_string<TCHAR> >::const_iterator it;
	for(it=path.begin();it!=path.end();it++)
		{
		if(std::find(existing.begin(),existing.end(), *it) == existing.end())
			{
			char *pstr = const_cast<char*>(toMB((*it).c_str()));
			PyObject *obj = PyString_FromString(pstr);
			PyList_Insert(p, 0, obj);
			Py_DECREF(obj);
			}
		}
	return true;
	}

bool PyInterface::addto_sys_path(const TCHAR *pszpath)
	{
	StrRec sr(pszpath, TEXT(";"));
	std::list< std::basic_string<TCHAR> > path;
	for(StrRec::iterator it = sr.begin(); it != sr.end();it++)
		path.push_back(*it);
	return addto_sys_path(path);
	}

bool PyInterface::run_command(const TCHAR *command)
	{
	AcquireThread at(s_tstate);
	PyObject *m = PyImport_AddModule("__main__");
	if (m == NULL)
		{
		PyErr_Show();
		PyErr_Clear();
		return false;
		}
	PyObject *d = PyModule_GetDict(m);
	const char *mb_command = toMB(command);
	PyObject *v = PyRun_String(const_cast<char*>(mb_command), Py_file_input, d, d);
	if(v == NULL)
		{
		PyErr_Show();
		return false;
		}
	Py_XDECREF(v);
	return true;
	}

bool PyInterface::run_file(const TCHAR *filename)
	{
	typedef std::basic_string<TCHAR> str_type; 
	const str_type read_data = TEXT("f = open(r'%s')\ndata = f.read()\nf.close()\n");
	const str_type compile = TEXT("code = compile(data, r'%s', 'exec')\n");
	const str_type exec = TEXT("import __main__\nexec code in __main__.__dict__\n");
	const str_type fmt_str = read_data + compile + exec;
	int n = lstrlen(filename);
	TCHAR *command = new TCHAR[fmt_str.length()+2*n+64];
	wsprintf(command, fmt_str.c_str(), filename, filename);
	bool ret = run_command(command);
	delete[] command;
	return ret;
	}

std::basic_string<TCHAR> PyObjectWrapper::toString()
	{
	if(m_obj == NULL)
		return TEXT("NULL");
	std::string str = PyString_AsString(PyObject_Str(m_obj));
#ifdef UNICODE
	int n = str.length()+1;
	std::basic_string<WCHAR> wstr(n, 0);
	WCHAR* wsz = const_cast<WCHAR*>(wstr.data());
	MultiByteToWideChar(CP_ACP, 0, str.c_str(), -1, wsz, n);
	return wstr;
#else
	return str;
#endif
	}

std::basic_string<TCHAR> PyExcInfo::getShortMsg()
	{
	std::string str = PyString_AsString(PyObject_Str(type));
	str += "\r\n";
	str += PyString_AsString(PyObject_Str(value));
#ifdef UNICODE
	int n = str.length()+1;
	std::basic_string<WCHAR> wstr(n, 0);
	WCHAR* wsz = const_cast<WCHAR*>(wstr.data());
	MultiByteToWideChar(CP_ACP, 0, str.c_str(), -1, wsz, n);
	return wstr;
#else
	return str;
#endif
	}

std::basic_string<TCHAR> PyExcInfo::getMsg()
	{
	std::basic_string<TCHAR> sm = getShortMsg();
	if(traceback != NULL)
		{
		std::basic_string<TCHAR> tstr = TEXT("Traceback (innermost last):\r\n");
		tstr += getTraceback();
		tstr += TEXT("\r\n");
		tstr += sm;
		return tstr;
		}
	return sm;
	}

// uses python/lib/traceback.py and cStringIO module 
std::basic_string<TCHAR> PyExcInfo::getTraceback()
	{
	PyObjectWrapper tracebackMod("traceback");
	if(!tracebackMod) return TEXT("cant import traceback");
	
	PyObjectWrapper print_tb = tracebackMod.GetAttr("print_tb");
	if(!print_tb) return TEXT("cant find traceback.print_tb");

	PyObjectWrapper cStringIOMod("cStringIO");
	if(!cStringIOMod) return TEXT("cant import StringIO");
	
	PyObjectWrapper StringIO = cStringIOMod.GetAttr("StringIO");
	if(!StringIO) return TEXT("cant find cStringIO.StringIO");
	
	PyObjectWrapper strout = StringIO.Call();
	if(!strout) return TEXT("StringIO.StringIO() failed");

	PyObjectWrapper tb_args = Py_BuildValue("OOO", traceback, Py_None, (PyObject*)strout);

	PyObjectWrapper result = print_tb.Call(tb_args);
	if(!result) return TEXT("traceback.print_tb() failed");

	PyObjectWrapper getvalue = strout.GetAttr("getvalue");
	if(!getvalue) return TEXT("cant find strout.getvalue()");

	result = getvalue.Call();
	if(!result) {PyErr_Clear();return TEXT("strout.getvalue() call failed");}

	if(!PyString_Check(result))
		return TEXT("strout.getvalue() did not return a string");
	
	char *p = PyString_AsString(result);

#ifdef UNICODE
	int n = strlen(p)+1;
	std::basic_string<WCHAR> wstr(n, 0);
	WCHAR* wsz = const_cast<WCHAR*>(wstr.data());
	MultiByteToWideChar(CP_ACP, 0, p, -1, wsz, n);
	return wstr;
#else
	return p;
#endif
	}
