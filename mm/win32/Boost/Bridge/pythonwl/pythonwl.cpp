#include "stdenv.h"

#include <windows.h>

#include "util.h"
	


int main(int argc, char **argv)
	{
	CoInitialize(NULL);
	
	char *defaulthome = "d:\\ufs\\mm\\python";
	char *pythonhome = getenv("PYTHONHOME");

	if(!python::initialize(argc, argv, pythonhome?pythonhome:defaulthome))
		{
		std::cout << "initialize_python failed" << std::endl;
		return 1;
		}
	if(argc > 1)
		{
		python::run_file(argv[1]);

		MSG msg;
		while(GetMessage(&msg, NULL, 0, 0)) 
			{
			TranslateMessage(&msg);
			DispatchMessage(&msg);
			}
		}
	else
		{
		char *p = strrchr(argv[0], '\\');
		std::cout << "usage: "<< (p?(p+1):argv[0]) << " filename.py" << std::endl;
		}

	python::finalize();
	
	RedrawWindow(NULL, NULL, NULL, RDW_INVALIDATE | RDW_ERASE | RDW_ALLCHILDREN);
	CoUninitialize();
	return 0;
	}