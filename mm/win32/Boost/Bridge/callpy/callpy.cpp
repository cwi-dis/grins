// callpy.cpp : Defines the entry point for the console application.
//

#include "stdafx.h"
#include "callpy.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#undef THIS_FILE
static char THIS_FILE[] = __FILE__;
#endif

// shortcuts
using std::cout;
using std::cerr;
using std::endl;

/////////////////////////////////////////////////////////////////////////////

std::ostream& operator<<(std::ostream& os, const std::list<std::string>& s)
	{
	std::list<std::string>::const_iterator it = s.begin();
	if(it != s.end()) os << *it++;
	while(it != s.end()) os << ";" << *it++;
	return os;
	}

namespace python 
{
	bool initialize(int argc, char **argv, char *python_home);
	void finalize();
	bool get_sys_path(std::list<std::string>& path);
	bool addto_sys_path(const char *folder);
	bool addto_sys_path(const std::list<std::string>& path);
	bool run_command(const char *command);

}  // namespace python


void get_app_path(std::list<std::string>& path);

CWinApp theApp;

int _tmain(int argc, TCHAR* argv[], TCHAR* envp[])
	{
	if (!AfxWinInit(::GetModuleHandle(NULL), NULL, ::GetCommandLine(), 0))
		{
		cerr << "Fatal Error: MFC initialization failed" << endl;
		return 1;
		}
	CoInitialize(NULL);

	std::string python_home = "d:\\ufs\\mm\\python";
	if(!python::initialize(argc, argv, const_cast<char*>(python_home.c_str())))
		{
		cout << "initialize_python failed" << endl;
		return 1;
		}
	//cout << "initialize_python succeeded" << endl;

	std::list<std::string> app_path;
	get_app_path(app_path);
	python::addto_sys_path(app_path);

	//std::list<std::string> py_path;
	//python::get_sys_path(py_path);
	//cout << py_path << endl;
	
	// test:
	//python::addto_sys_path("D:\\ufs\\mm\\cmif\\win32\\DXMedia\\ddraw\\test");
	//python::run_command("import test");

	// test:
	//python::run_command("import grinsp");

	// test 4:
	python::addto_sys_path("D:\\ufs\\mm\\cmif\\win32\\winsdk\\winuser");
	std::string str("import wingeneric");
	python::run_command(str.c_str());

	MSG msg;
	while(::GetMessage(&msg, NULL, 0, 0)) 
		{
		TranslateMessage(&msg);
		DispatchMessage(&msg);
		}
	
	python::finalize();

	// redraw desktop for desktop direct draw samples
	RedrawWindow(NULL, NULL, NULL, RDW_INVALIDATE | RDW_ERASE | RDW_ALLCHILDREN);

	CoUninitialize();
	return 0;
	}


void get_app_path(std::list<std::string>& path)
	{
	std::string PY_EXTENSIONS_DIR = "d:\\ufs\\mm\\python\\Extensions\\";
	std::string APP_DIR = "d:\\ufs\\mm\\cmif\\";
	
	path.push_back(APP_DIR + "lib\\wintk");
	path.push_back(APP_DIR + "lib");

	path.push_back(APP_DIR + "grins\\smil20\\win32");
	path.push_back(APP_DIR + "grins\\smil20");
	path.push_back(APP_DIR + "grins\\win32");
	path.push_back(APP_DIR + "grins");

	path.push_back(APP_DIR + "common\\win32");
	path.push_back(APP_DIR + "common");

	path.push_back(APP_DIR + "pylib");

	path.push_back(APP_DIR + "bin\\win32");

	path.push_back(APP_DIR + "win32\\src\\Build");
	path.push_back(PY_EXTENSIONS_DIR + "win32\\lib");
	}