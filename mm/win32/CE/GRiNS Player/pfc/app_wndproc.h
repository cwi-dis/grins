#ifndef INC_APP_WNDPROC
#define INC_APP_WNDPROC

#ifndef _WINDOWS_
#include <windows.h>
#endif

LRESULT CALLBACK MinimalMainWndProc(HWND hwnd, UINT iMsg, WPARAM wParam, LPARAM lParam);
LONG APIENTRY PyWnd_WndProc(HWND hWnd, UINT uMsg, UINT wParam, LONG lParam);

#endif
