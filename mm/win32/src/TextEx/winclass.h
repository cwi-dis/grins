#include "ezfont.h"

class myWin : public CWnd
{
 public:
    BOOL single_anchor;
	int m_nPageSize;
	int VHeight;
	int m_cyChar;
	int difer;
	int m_nScrollPos,m_nOldScrollPos;
	CString align;
	//RECT rect;
	char facename[50];
    myWin ();
	friend CString clearstring(CString str);
	friend CString expandtabs(CString str,CString align);
    void SetScroll(CString str);
	void GetDim(CString s,char* fcname,int size);
	friend int countlines (HDC dc,CString str,char* fcname,int sz,RECT rect);
	afx_msg int OnCreate (LPCREATESTRUCT);
    //afx_msg void OnPaint ();
    //afx_msg void OnSize (UINT, int, int);
    afx_msg void OnVScroll (UINT, UINT, CScrollBar*);

    DECLARE_MESSAGE_MAP ()
};