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
		PyErr_Clear();
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

////////////////////////////////////

// the following is borrowed from Python\PC\ce

char* PyInterface::getTraceback(PyObject *exc_tb)
{
	char *result = NULL;
	char *errMsg = NULL;
	PyObject *modStringIO = NULL;
	PyObject *modTB = NULL;
	PyObject *obFuncStringIO = NULL;
	PyObject *obStringIO = NULL;
	PyObject *obFuncTB = NULL;
	PyObject *argsTB = NULL;
	PyObject *obResult = NULL;

	// Import the modules we need - cStringIO and traceback
	modStringIO = PyImport_ImportModule("cStringIO");
	if (modStringIO==NULL) 
		result = "cant import cStringIO\n";

	if (errMsg==NULL) {
		modTB = PyImport_ImportModule("traceback");
		if (modTB==NULL)
			errMsg = "cant import traceback\n";
	}
	// Construct a cStringIO object
	if (errMsg == NULL) {
		obFuncStringIO = PyObject_GetAttrString(modStringIO, "StringIO");
		if (obFuncStringIO==NULL)
			errMsg = "cant find cStringIO.StringIO\n";
	}
	if (errMsg == NULL) {
		obStringIO = PyObject_CallObject(obFuncStringIO, NULL);
		if (obStringIO==NULL) 
			errMsg = "cStringIO.StringIO() failed\n";
	}
	// Get the traceback.print_exception function, and call it
	if (errMsg == NULL) {
		obFuncTB = PyObject_GetAttrString(modTB, "print_tb");
		if (obFuncTB==NULL) 
			errMsg = "cant find traceback.print_tb\n";
	}
	if (errMsg == NULL) {
		argsTB = Py_BuildValue("OOO", 
				exc_tb  ? exc_tb  : Py_None,
				Py_None, 
				obStringIO);
		if (argsTB==NULL) 
			errMsg = "cant make print_tb arguments\n";
	}
	if (errMsg == NULL) {
		obResult = PyObject_CallObject(obFuncTB, argsTB);
		if (obResult==NULL) 
			errMsg = "traceback.print_tb() failed\n";
	}
	// Now call the getvalue() method in the StringIO instance
	Py_XDECREF(obFuncStringIO);
	obFuncStringIO = NULL;
	if (errMsg == NULL) {
		obFuncStringIO = PyObject_GetAttrString(obStringIO, "getvalue");
		if (obFuncStringIO==NULL) 
			errMsg = "cant find getvalue function\n";
	}
	Py_XDECREF(obResult);
	obResult = NULL;
	if (errMsg == NULL) {
		obResult = PyObject_CallObject(obFuncStringIO, NULL);
		if (obResult==NULL) 
			errMsg = "getvalue() failed.\n";
	}
	// And it should be a string all ready to go - duplicate it.
	if (errMsg == NULL) {
		if (!PyString_Check(obResult))
			errMsg = "getvalue() did not return a string\n";
		else {
			char *tempResult = PyString_AsString(obResult);
			result = PyMem_Malloc(strlen(tempResult)+1);
			strcpy(result, tempResult);
		}
	}
	// All finished - first see if we encountered an error
	if (result==NULL && errMsg != NULL) {
		result = new char(strlen(errMsg)+1);
		strcpy(result, errMsg);
	}

	Py_XDECREF(modStringIO);
	Py_XDECREF(modTB);
	Py_XDECREF(obFuncStringIO);
	Py_XDECREF(obStringIO);
	Py_XDECREF(obFuncTB);
	Py_XDECREF(argsTB);
	Py_XDECREF(obResult);
	return result;
}

TCHAR* PyInterface::getTracebackMsg()
	{
	PyExcInfo exc;
	char *szPrefix = "Traceback (innermost last):\n";
	char *pszTraceback = getTraceback(exc.traceback);
	char *szExcType = PyString_AsString(PyObject_Str(exc.type));
	char *szExcValue = PyString_AsString(PyObject_Str(exc.value));
	int buf_size = sizeof(TCHAR) * (8 + strlen(szPrefix) + strlen(pszTraceback) + strlen(szExcType) + strlen(szExcValue));
	TCHAR *buf = new TCHAR[buf_size];
	wsprintf(buf, TEXT("%hs%hs%hs: %hs"), szPrefix, pszTraceback, szExcType, szExcValue);
	delete[] pszTraceback;
	return buf;
	}

