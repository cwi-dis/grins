#include "pywintoolbox.h"

#include "Python.h"

#include <windows.h>

#include <QTML.h>
#include <TextUtils.h>

//////////
// Convert some std file references to an os path form
// 1. file:///D|/<filepath>
// 2. file:/D|/<filepath>
// 3. file:////<filepath>
// 4. file:////<drive>:\<filepat> 
void UrlConvert(char *pszUrl)
	{
	int l = strlen(pszUrl);
	if(strncmp(pszUrl,"file:////",9)==0 && l>11 && pszUrl[10]==':')
		{
		char *ps = pszUrl+9;
		char *pd = pszUrl;
		while(*ps){
			if(*ps=='/'){*pd++='\\';ps++;}
			else {*pd++ = *ps++;}
			}
		*pd='\0';
		}
	else if(strncmp(pszUrl,"file:////",9)==0 && l>9 && strstr(pszUrl,"|")==NULL) // UNC
		{
		pszUrl[0]='\\';pszUrl[1]='\\';
		char *ps = pszUrl+9;
		char *pd = pszUrl+2;
		while(*ps){
			if(*ps=='/'){*pd++='\\';ps++;}
			else {*pd++ = *ps++;}
			}
		*pd='\0';
		}
	else if(strncmp(pszUrl,"file:///",8)==0 && l>10 && pszUrl[9]=='|')
		{
		pszUrl[0]=pszUrl[8];
		pszUrl[1]=':';
		char *ps = pszUrl+10;
		char *pd = pszUrl+2;
		while(*ps){
			if(*ps=='/'){*pd++='\\';ps++;}
			else {*pd++ = *ps++;}
			}
		*pd='\0';
		}
	else if(strncmp(pszUrl,"file:/",6)==0 && l>8 && pszUrl[7]=='|')
		{
		pszUrl[0]=pszUrl[6];
		pszUrl[1]=':';
		char *ps = pszUrl+8;
		char *pd = pszUrl+2;
		while(*ps){
			if(*ps=='/'){*pd++='\\';ps++;}
			else {*pd++ = *ps++;}
			}
		*pd='\0';
		}
	//else no change
	}

PyObject* OSType_FromLong(long t) 
	{
	BYTE *p = (BYTE*)&t;
	t = MAKEFOURCC(p[3], p[2], p[1], p[0]);
	return PyString_FromStringAndSize((char*)&t, 4);
	}

