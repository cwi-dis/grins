#include "stdenv.h"

#include <windows.h>

#include "util.h"
	
int main(int argc, char **argv)
	{
	if(argc == 1)
		{
		char *p = strrchr(argv[0], '\\');
		std::cout << "usage: "<< (p?(p+1):argv[0]) << " filename.py" << std::endl;
		return 0;
		}

	CoInitialize(NULL);
	
	if(!python::initialize(argc-1, argv))
		{
		std::cout << "initialize_python failed" << std::endl;
		CoUninitialize();
		return 1;
		}

	python::run_file(argv[1]);

	MSG msg;
	while(GetMessage(&msg, NULL, 0, 0)) 
		{
		TranslateMessage(&msg);
		DispatchMessage(&msg);
		}

	python::finalize();
	
	RedrawWindow(NULL, NULL, NULL, RDW_INVALIDATE | RDW_ERASE | RDW_ALLCHILDREN);
	CoUninitialize();
	return 0;
	}