#ifndef _TEXTEX_H
#define _TEXTEX_H

#include <string.h>
#include <math.h>
#include "cmifex.h"
#include "ezfont.h"
#include "winclass.h"

void GetAnchorList(myWin* hwnd, CString str, char* facename,
				   int sz,int id,CString align);
CString getanchor(CString& str, CString& tmp);

BOOL CheckIfIsSingleAnchor(CString str);
BOOL IsBlank(CString wrd);
void findxy(HWND hwnd,int& county,CString& str,CString name,
			int x,char* facename,int sz,int id,RECT rect2);
CString clearstring(CString str);

void puttext(HWND hwnd, char* str,char* facename,int size,int trasp,COLORREF bkcolor,COLORREF fontcolor,CString align);

CString findmaxword(HDC dc,CString word);
int countlines (HDC dc,CString str,char* fcname,int sz,RECT rect);
void findrect(HDC dc,CString str,char* fcname,int sz,CString bigline,CString algn,RECT r,RECT &r2);

BOOL IsAnchor(CString str);

#ifdef __cplusplus
extern "C" {
#endif

void PyErr_Print(void);
void TextExErrorFunc(char *str);
void SaveList(int ID,CString anchor,int x1,int y1,int x2,int y2);

#ifdef __cplusplus
}
#endif

#endif