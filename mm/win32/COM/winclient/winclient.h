// winclient.h : main header file for the WINCLIENT application
//

#if !defined(AFX_WINCLIENT_H__00B12DF7_6C0B_45C7_A07B_6FA52B9005C1__INCLUDED_)
#define AFX_WINCLIENT_H__00B12DF7_6C0B_45C7_A07B_6FA52B9005C1__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000

#ifndef __AFXWIN_H__
	#error include 'stdafx.h' before including this file for PCH
#endif

#include "resource.h"		// main symbols

/////////////////////////////////////////////////////////////////////////////
// CWinclientApp:
// See winclient.cpp for the implementation of this class
//

class CWinclientApp : public CWinApp
{
public:
	CWinclientApp();

// Overrides
	// ClassWizard generated virtual function overrides
	//{{AFX_VIRTUAL(CWinclientApp)
	public:
	virtual BOOL InitInstance();
	//}}AFX_VIRTUAL

// Implementation

	//{{AFX_MSG(CWinclientApp)
		// NOTE - the ClassWizard will add and remove member functions here.
		//    DO NOT EDIT what you see in these blocks of generated code !
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
};


/////////////////////////////////////////////////////////////////////////////

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ will insert additional declarations immediately before the previous line.

#endif // !defined(AFX_WINCLIENT_H__00B12DF7_6C0B_45C7_A07B_6FA52B9005C1__INCLUDED_)
