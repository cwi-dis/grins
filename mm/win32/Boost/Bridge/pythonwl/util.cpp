
#include "stdenv.h"

#include "Python.h"

#include <windows.h>

#include "util.h"

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


class StrRec : public std::vector<char*>
	{
	public:
    StrRec(const char* pString,const char* pDelims)
	:	apBuf(new char[strlen(pString)+1])
		{
		char *pBuf = apBuf.get();
		strcpy(pBuf,pString);
		char* pLook = strtok(pBuf,pDelims);
		while(pLook)
			{
			push_back(pLook);
			pLook = strtok(NULL,pDelims);
			}
		}
	private:
	std::auto_ptr<char> apBuf;
	};

const char* get_ini_entry(const char* pszSec, const char* pszEntry, char *psz,int len)
	{
	char szBuf[MAX_PATH];
    GetModuleFileName(NULL, szBuf, sizeof(szBuf));
    char *p = strrchr(szBuf,'.');
	*p = '\0';
    lstrcat(szBuf,".ini");
    GetPrivateProfileString(pszSec, pszEntry, "", psz, len, szBuf);
	return psz;
	}

bool initialize(int argc, char **argv)
	{
	if (g_tstate) return true;
	
	std::cout << "Python " << Py_GetVersion() << std::endl << Py_GetCopyright() 
			<< std::endl << std::endl;

	char python_home[256];
	get_ini_entry("GENERAL", "PYTHONHOME", python_home, 256);
	if(python_home[0] != '\0')
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
	
	// add site ini path
	const int max_path_len = 2048;
	char *pathbuf = new char[max_path_len];
	get_ini_entry("GENERAL", "PYTHONPATH", pathbuf, max_path_len);
	if(pathbuf[0] != '\0')
		addto_sys_path(pathbuf);
	delete[] pathbuf;

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

bool addto_sys_path_dir(const char *dir)
	{
	std::list<std::string> existing;
	if(!get_sys_path(existing))
		return false;

	AcquireThread at(g_tstate);
	PyObject *p = PySys_GetObject("path");
	if (!PyList_Check(p))
		return false;

	if(std::find(existing.begin(),existing.end(), dir) == existing.end())
		{
		PyObject *obj = PyString_FromString(const_cast<char*>(dir));
		PyList_Insert(p, 0, obj);
		Py_DECREF(obj);
		}
	return true;
	}

bool addto_sys_path(const char *pszpath)
	{
	StrRec sr(pszpath, ";");
	std::list<std::string> path;
	for(StrRec::iterator it=sr.begin();it!= sr.end();it++)
		path.push_back(*it);
	return addto_sys_path(path);
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
		PyErr_Print();
		return false;
		}
	PyObject *d = PyModule_GetDict(m);
	PyObject *v = PyRun_String(const_cast<char*>(command), Py_file_input, d, d);
	if(v == NULL)
		{
		PyErr_Print();
		return false;
		}
	Py_XDECREF(v);
	return true;
	}

void splitpath(const char *path, char *dir, char *name)
	{
	char *p = strrchr(path, '\\');
	if(p != NULL)
		{
		int n = p - path;
		strncpy(dir, path, n);
		dir[n] = '\0';
		}
	else 
		{
		p = (char*)path-1;
		dir[0] = '\0';
		}
	char *p2 = strrchr(path, '.');
	if(p2 != NULL)
		{
		int n2 = p2-p-1;
		strncpy(name, p+1, n2);
		name[n2] = '\0';
		}
	else
		strcpy(name, p+1);
	}


bool run_file(const char *filename)
	{
	const std::string read_data = "f = open(r'%s')\ndata = f.read()\nf.close()\n";
	const std::string compile = "code = compile(data, r'%s', 'exec')\n";
	const std::string exec = "import __main__\nexec code in __main__.__dict__\n";
	const std::string fmt_str = read_data + compile + exec;
	int n = lstrlen(filename);
	char *dir = new char[n+1];
	char *name = new char[n+1];
	char *command = new char[fmt_str.length()+2*n+64];
	splitpath(filename, dir, name);
	if(dir[0] != '\0')
		addto_sys_path_dir(dir);
	wsprintf(command, fmt_str.c_str(), filename, filename);
	bool ret = python::run_command(command);
	delete[] command;
	delete[] name;
	delete[] dir;
	return ret;
	}

}  // namespace python

