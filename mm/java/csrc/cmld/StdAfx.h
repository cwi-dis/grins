// stdafx.h : include file for standard system include files,
//  or project specific include files that are used frequently, but
//      are changed infrequently
//

#if !defined(AFX_STDAFX_H__F70E48F1_D684_4199_A23C_16CD208B382C__INCLUDED_)
#define AFX_STDAFX_H__F70E48F1_D684_4199_A23C_16CD208B382C__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000

#define VC_EXTRALEAN		// Exclude rarely-used stuff from Windows headers

// Sockets
#pragma comment (lib,"ws2_32.lib")

#ifdef FD_SETSIZE
#undef FD_SETSIZE
#endif
#define FD_SETSIZE 16384

#ifndef _WINSOCK2API_
#include <winsock2.h>
#endif

#include <windows.h>

// STL
#pragma warning(disable: 4786) // Long names trunc

#include <iostream>
#include <fstream>

#include <string>
#include <vector>
#include <list>
#include <map>
#include <set>
#include <stack>

#include <algorithm>

using namespace std;

#include <math.h>
#include <time.h>


template <class T> string& operator<<(string& s, T c) { s+=c; return s;}

template <class T> ostream& operator<<(ostream& os, const set<T>& s)
	{
	for(set<T>::const_iterator i=s.begin();i!=s.end();i++)
		os << (*i) << endl;
	return os;
	}

inline string trim(const string& s)
	{
	int i1 = s.find_first_not_of(" \r\n\t\v");
	if(i1==string::npos) return "";

	int i2 = s.length()-1;
	while(i2>=0 && isspace(s[i2])) i2--;
	if(i2==-1) return "";

	return string(s.c_str()+i1,s.c_str()+i2+1);
	}

inline const char* XMLQuote(string& s)
	{
	string sc(s);
	s="";
	for(int i=0;i<sc.length();i++)
		{
		char ch = sc.at(i);
        if(ch=='<') s+="&lt;";
        else if(ch=='>') s+="&gt;";
        else if(ch=='&') s+="&amp;";
        else s+=ch;
		}
	return s.c_str();
	}

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ will insert additional declarations immediately before the previous line.

#endif // !defined(AFX_STDAFX_H__F70E48F1_D684_4199_A23C_16CD208B382C__INCLUDED_)
