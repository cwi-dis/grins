#ifndef INC_APP_PYINTERFACE
#define INC_APP_PYINTERFACE

bool InitializePythonInterface(HWND hWnd);
void FinalizePythonInterface();
void *PyInterfaceImport(const TCHAR *psztmodule);

#endif
