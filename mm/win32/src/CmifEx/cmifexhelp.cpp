#include "StdAfx.h"
#include "cmifexhelp.h"

static HWND ChildWnds[500];

VOID MyCascadeChildWindows(register HWND hwndParent, int x, int y, int xClient, int yClient)
{
	HWND hwndMove;
	INT       i;
	INT       cWindows;
	RECT      rc;
	DWORD      wFlags;
	HANDLE    hDefer;
	WINDOWPLACEMENT wndpl;
	float	xfactor, yfactor;
	BOOL	bTest;

	cWindows = CountWindows(hwndParent);
	xfactor = (float)x/(float)xClient;
	yfactor = (float)y/(float)yClient;

	if (!cWindows)
		return;

	hwndMove = GetWindow(hwndParent, GW_CHILD);

	hDefer = BeginDeferWindowPos(cWindows);

	for (i=0; i<cWindows; i++)
	{  
		//wFlags = SWP_NOZORDER | SWP_NOACTIVATE | SWP_NOCOPYBITS;
		
		wFlags = 0;

		wndpl.length = sizeof(WINDOWPLACEMENT);
		bTest = GetWindowPlacement(ChildWnds[i], &wndpl);
		if(bTest==FALSE)
			GetErrorMessage();

		rc = wndpl.rcNormalPosition;

		rc.left = (int)((float)rc.left*xfactor + 0.5);
		rc.top = (int)((float)rc.top*yfactor + 0.5);
		rc.right = (int)((float)rc.right*xfactor + 0.5);
		rc.bottom = (int)((float)rc.bottom*yfactor + 0.5);
		/* Size the window. */
		hDefer = DeferWindowPos(hDefer,
								ChildWnds[i], i==0?NULL:ChildWnds[i-1],
								rc.left, rc.top,
								rc.right-rc.left, rc.bottom-rc.top,
								wFlags);
		if(hDefer==NULL)
		{
			GetErrorMessage();
			return;
		}

		hwndMove = GetWindow(hwndMove, GW_HWNDNEXT);
	}

	EndDeferWindowPos(hDefer);
}

INT CountWindows(register HWND hwndParent)
{
	INT cWindows = 0;
	register HWND hwnd;

	for (hwnd=GetWindow(hwndParent, GW_CHILD); hwnd; hwnd= GetWindow(hwnd, GW_HWNDNEXT))
		ChildWnds[cWindows++] = hwnd;
	ChildWnds[cWindows] = hwnd;

	return(cWindows);
}

void GetErrorMessage(void)
{
	LPVOID lpMsgBuf;
	DWORD error;
 
	error = GetLastError();

	FormatMessage( 
		FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
		NULL,
		error,
		MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
		(LPTSTR) &lpMsgBuf,
		0,
		NULL 
	);

	// Display the string.
	AfxMessageBox( (LPCTSTR)lpMsgBuf, MB_OK|MB_ICONINFORMATION, 0 );

	// Free the buffer.
	LocalFree( lpMsgBuf );
}