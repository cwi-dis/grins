// DbWnd.cpp : implementation file
//

#include "stdafx.h"
#include "DbWnd.h"
#include "gridctrl.h"


#define IDC_GRIDCTRL 101

#define MIN_W 400
#define MIN_H 400   //limits in twips

#ifdef _DEBUG
#define new DEBUG_NEW
#undef THIS_FILE
static char THIS_FILE[] = __FILE__;
#endif

/////////////////////////////////////////////////////////////////////////////
// CDbWnd

CDbWnd::CDbWnd()
{
	//initialise members
	m_cols = m_rows = 0 ;
	m_bgrid = FALSE;
	m_bfirst = TRUE;
	for (UINT i=0; i<MAX_ROWS; i++)
	{
		for(UINT k=0; k<MAX_COLS; k++)
		{
			m_table[i][k] = 0;
			m_btable[i][k] = NONE;
		}
	}


}

CDbWnd::~CDbWnd()
{
}


BEGIN_MESSAGE_MAP(CDbWnd, CWnd)
	//{{AFX_MSG_MAP(CDbWnd)
	ON_WM_PAINT()
	ON_WM_SIZE()
	//}}AFX_MSG_MAP
END_MESSAGE_MAP()


/////////////////////////////////////////////////////////////////////////////
// CDbWnd message handlers

void CDbWnd::OnPaint() 
{
	CPaintDC dc(this); // device context for painting
	CRect rc;
	int k,i,j;
	int scalew, scaleh;
	CString s, str;
	

	dc.SetMapMode(MM_TWIPS);  //conform to the grid system (twips)
	
			
	GetClientRect(&rc);
	dc.DPtoLP(&rc);           //use logical coordinates

	LONG wid = rc.right - rc.left;
	LONG heg = rc.top - rc.bottom ;

	if (m_rows>1 && m_cols>1)
	{
		 scalew = (int) (wid/(m_cols));
		 scaleh = (int) (heg/(m_rows));
	}
	

	TRACE("scales: %d, %d", scalew, scaleh);
	s.Format("scales: %d, %d", scalew, scaleh);
	//AfxMessageBox(s, MB_OK);

	int l = max(m_cols, m_rows);

	for (k=0; k< l; k++)
	{
		TRACE("for loop\n");
		if (k<m_cols)
		{
			if (scalew > MIN_W)              //width not less than MIN_W twips
			m_grid.SetColWidth(k, (scalew)); 
			else
			m_grid.SetColWidth(k, MIN_W);
		}

		if (k<m_rows)
		{
			if (scaleh > MIN_H)				//height not less than MIN_H twips	
			m_grid.SetRowHeight(k, (scaleh));
			else
			m_grid.SetRowHeight(k, MIN_H);
		}
	}

	for (i=0; i<m_rows; i++){
		for (j=0; j<m_cols; j++){

			switch (m_btable[i][j])
			{
			 case NONE :
				break;
			 case INT_NUM:
				 {

					m_grid.SetRow(i);
					m_grid.SetCol(j);
					str.Format("%d", m_table[i][j]);
					m_grid.SetText(str);
					break;
				 }
			 case TEXT:
				 {
					m_grid.SetRow(i);
					m_grid.SetCol(j);
					
					str.Format("%s", m_strtable[i][j]);
					m_grid.SetText(str);
					break;
				 }
			 default:
				 break;

			}
		}
	}

	
}


void CDbWnd::OnSize(UINT nType, int cx, int cy) 
{
	CRect rc;

	CWnd::OnSize(nType, cx, cy);

	if (m_bfirst == TRUE)
	{
		m_bfirst = FALSE;
		return;
	}


	GetClientRect(&rc);
	
	m_grid.DestroyWindow();
	
	BOOL bRet = m_grid.Create(NULL, WS_VISIBLE|WS_BORDER,
						rc, this, IDC_GRIDCTRL);

	m_grid.SetRows(m_rows);
	m_grid.SetCols(m_cols);

		
}
