// ContainerWnd.h : header file
//

/////////////////////////////////////////////////////////////////////////////
// CContainerWnd window

#include "html.h"

#define MAX_NAMES   10
#define WM_RETRIEVE (WM_USER+10)

class CContainerWnd : public CWnd
{
// Construction
public:
	CContainerWnd();

// Attributes
public:
	CDC*		m_pMemDC;	  // Memory dc
	CBitmap*	m_pBitmap;	  // Bitmap for client area

	BOOL		m_ctrl_cr;    // indicates wheather the html ctrl has been created 

	HWND		m_Status;
	CHTML		m_html;
	int			m_id;
	BOOL        m_bCmifHit;   //indiactes wheather a cmif anchor has 
							  //just been hit
	BOOL        m_bfurl;      //indicates weather at least url
							  //one has been retrieved successfully  
	BOOL        m_bnewReq;
	CString		m_title;						  
	CString		m_newurl;
	CString     m_strPath;    //the full path of the latest Html request
							  //used because the OCX control does
							  //not searches the current directory to
							  //retrieve a requested doc	

	DWORD		m_count;
	BYTE		m_cursor_type;
	CString     m_strCmif;
	
// Operations
public:
	void Retrieve(const char* url);
	void UpdateWnd();
	void MoveWnd();

// Overrides
	// ClassWizard generated virtual function overrides
	//{{AFX_VIRTUAL(CContainerWnd)
	//}}AFX_VIRTUAL

// Implementation
public:
	virtual ~CContainerWnd();

	// Generated message map functions
protected:
	LONG OnRetrieve(UINT wParam, LONG lParam); 
	//{{AFX_MSG(CContainerWnd)
	afx_msg void OnSize(UINT nType, int cx, int cy);
	afx_msg void OnMouseMove(UINT nFlags, CPoint point);
	afx_msg void OnPaint();
	afx_msg void OnContextMenu(CWnd* pWnd, CPoint point);
	afx_msg void OnDoRequestSubmitHtml(LPCTSTR URL, LPDISPATCH Form, LPDISPATCH DocOutput, BOOL FAR* EnableDefault);
	//}}AFX_MSG
	//Event Handlers
	void OnBeginRetrievalHtml();
	void OnEndRetrievalHtml();
	void OnParseCompleteHtml();
	void OnLayoutCompleteHtml();
	void OnErrorHtml(short Number, BSTR FAR* Description, long Scode, LPCTSTR Source, LPCTSTR HelpFile, long HelpContext, BOOL FAR* CancelDisplay) ;
	void OnUpdateRetrievalHtml();
	void OnDoRequestDocHtml(LPCTSTR URL, LPDISPATCH Element, LPDISPATCH DocInput, BOOL FAR* EnableDefault);
	DECLARE_EVENTSINK_MAP()
	DECLARE_MESSAGE_MAP()

};

/////////////////////////////////////////////////////////////////////////////
