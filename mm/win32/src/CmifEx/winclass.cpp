#include <afxwin.h>
#include "winclass.h"

IMPLEMENT_DYNAMIC(myWin, CWnd);

BEGIN_MESSAGE_MAP (myWin, CWnd)
    ON_WM_CREATE ()
    //ON_WM_PAINT ()
    //ON_WM_SIZE ()
    ON_WM_VSCROLL ()
END_MESSAGE_MAP ()


// Constructor
myWin::myWin ()
{
    single_anchor = FALSE;
	m_nScrollPos = 0;
	m_nOldScrollPos = 0;
	m_nPageSize = 0;
	VHeight = 0;
	m_cyChar = 0;
	difer = 0;
	align = "";
}



int myWin::OnCreate (LPCREATESTRUCT lpcs)
{
    if (CWnd::OnCreate (lpcs) == -1)
        return -1;

	SCROLLINFO si;
	si.fMask = SIF_PAGE | SIF_RANGE | SIF_POS;
	si.nMin = 0;
	si.nMax = 0;
	si.nPos = m_nScrollPos;
	si.nPage = m_nPageSize;

	SetScrollInfo (SB_VERT, &si, TRUE);
	
 return 0;
}


void myWin::OnVScroll (UINT nCode, UINT nPos, CScrollBar* pScrollBar)
{
    int nDelta;
    int nMaxPos = VHeight - m_nPageSize;

	
	m_nOldScrollPos = m_nScrollPos;
		
	switch (nCode) 
	{
		case SB_LINEUP:
			if (m_nScrollPos <= 0)
				return;
			nDelta = -(min (m_cyChar, m_nScrollPos));
			break;

		case SB_PAGEUP:
			if (m_nScrollPos <= 0)
				return;
			nDelta = -(min (m_nPageSize, m_nScrollPos));
			break;

		case SB_THUMBPOSITION:
			nDelta = (int) nPos - m_nScrollPos;
			break;

		case SB_PAGEDOWN:
			if (m_nScrollPos >= nMaxPos)
				return;
			nDelta = min (m_nPageSize, nMaxPos - m_nScrollPos);
			break;

		case SB_LINEDOWN:
			if (m_nScrollPos >= nMaxPos)
				return;
			nDelta = min (m_cyChar, nMaxPos - m_nScrollPos);
			break;

		default: // Ignore other scroll bar messages
			return;
		}

		m_nScrollPos += nDelta;
		difer = m_nOldScrollPos-m_nScrollPos;
		SetScrollPos (SB_VERT, m_nScrollPos, TRUE);
		//InvalidateRect(NULL,TRUE);
		::SendMessage(this->m_hWnd,WM_PAINT,(WPARAM)GetDC()->m_hDC,0);
	
}



/*
FUNCTION : SetScroll
ATTRIBUTES :
    CString str: The text of the window 
NOTES:
	If str is too long to fit in the window this function shows
a vertical scrollbar.
*/


void myWin::SetScroll(CString str)
{
	RECT rect,windowrect;
	
	if(!align.IsEmpty()) return;
	
	HDC dc = ::GetDC(this->m_hWnd);
	::GetClientRect(this->m_hWnd,&rect);
	VHeight = countlines (dc,clearstring(expandtabs(str,align)),(char*)facename,m_cyChar,rect);
	::ReleaseDC(this->m_hWnd,dc);

	m_nScrollPos = 0;

	if(VHeight>rect.bottom) 
	{
		GetWindowRect(&windowrect);
		if(rect.right>windowrect.right-windowrect.left-(::GetSystemMetrics(SM_CXVSCROLL)))
		{
			rect.right -= ::GetSystemMetrics(SM_CXVSCROLL);
			//rect.right -= ::GetSystemMetrics(SM_CXVSCROLL);
			VHeight = countlines (dc,clearstring(expandtabs(str,align)),(char*)facename,m_cyChar,rect);
		}
		m_nPageSize=rect.bottom;
	}
	else
	{
		m_nScrollPos = 0;
		m_nPageSize = 0;
		VHeight = 0;
	}
	
	SCROLLINFO si;
	si.fMask = SIF_PAGE | SIF_RANGE | SIF_POS;
	si.nMin = 0;
	si.nMax = VHeight;
	si.nPos = m_nScrollPos;
	si.nPage = m_nPageSize;

	SetScrollInfo (SB_VERT, &si, TRUE);
	RedrawWindow();
	//::SendMessage(this->m_hWnd,WM_PAINT,(WPARAM)GetDC()->m_hDC,0);
}



/*
FUNCTION : GetDim
ATTRIBUTES :
    CString s: The align of the channel
	char* fcname: The face name of the font of the window
	int size: The size of the font of the window 
NOTES:
	This function sets some variables for the window. Only 
align is critical.
*/



void myWin::GetDim(CString s,char* fcname,int size)
{
	align = s;
	strcpy(facename,fcname);
	m_cyChar = size;
}

#ifdef _DEBUG
void myWin::Dump( CDumpContext &dc ) const
{
	dc << "A textex.pys myWin object!";
	CWnd::Dump(dc);
}
void myWin::AssertValid() const
{
	CWnd::AssertValid();
}
#endif
