// stdafx.h : include file for standard system include files,
//  or project specific include files that are used frequently, but
//      are changed infrequently
//

#if !defined(AFX_STDAFX_H__745BDE99_1122_11D3_B26E_00A0246BC0BD__INCLUDED_)
#define AFX_STDAFX_H__745BDE99_1122_11D3_B26E_00A0246BC0BD__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000

#include <windows.h>
#include <tchar.h>
#include <crtdbg.h>
#include <stdio.h>
#include <assert.h>
#include <conio.h>

// STL
#pragma warning(disable: 4786) // Long names trunc

#include <iostream>
#include <fstream>

#include <string>
#include <vector>
#include <list>
#include <map>
#include <set>

#include <algorithm>

using namespace::std;

#include <math.h>


// std addins
#include "strfmt.h"

inline void AfxMessageLog(LPCTSTR str)
	{
	ofstream ofs("log.txt",ios::app);
	if(ofs) ofs << str << endl;
	ofs.close();
	}

// TODO: reference additional headers your program requires here

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ will insert additional declarations immediately before the previous line.

#endif // !defined(AFX_STDAFX_H__745BDE99_1122_11D3_B26E_00A0246BC0BD__INCLUDED_)
