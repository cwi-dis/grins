// EventSink.cpp : Implementation of CEventSink
#include "stdafx.h"
#include "GRiNSRenderer.h"
#include "Behavior.h"
#include "EventSink.h"

#include "appconst.h"

/////////////////////////////////////////////////////////////////////////////
// CEventSink
STDMETHODIMP
CEventSink::Invoke(
    DISPID dispidMember,
    REFIID riid,
    LCID lcid,
    WORD wFlags,
    DISPPARAMS* pdispparams,
    VARIANT* pvarResult,
    EXCEPINFO* pexcepinfo,
    UINT* puArgErr)
{
	long X = NULL;
	long Y = NULL;

	HRESULT hr = NULL;
	IHTMLEventObj* pEvent = NULL;

    switch (dispidMember)
	{
		case DISPID_HTMLDOCUMENTEVENTS_ONMOUSEDOWN:
			// Calculate parameters for ClipCursor
			POINT ptElemOriginLocal, ptElemOriginGlobal;
			IHTMLWindow3* pWin3;
			long winTop, winLeft;
			RECT clipRect;

			ptElemOriginLocal.x = HANDLE_RADIUS;
			ptElemOriginLocal.y = HANDLE_RADIUS;

			m_pBehavior->m_pPaintSite->TransformLocalToGlobal(ptElemOriginLocal, &ptElemOriginGlobal);

			m_pBehavior->m_spWin->QueryInterface(IID_IHTMLWindow3, (void**)&pWin3);
			pWin3->get_screenTop(&winTop);
			pWin3->get_screenLeft(&winLeft);
			pWin3->Release();

			clipRect.top = m_pBehavior->m_rtElemCorners.top + ptElemOriginGlobal.y + winTop;
			clipRect.bottom = m_pBehavior->m_rtElemCorners.bottom + ptElemOriginGlobal.y + winTop;
			clipRect.left = m_pBehavior->m_rtElemCorners.left + ptElemOriginGlobal.x + winLeft;
			clipRect.right = m_pBehavior->m_rtElemCorners.right + ptElemOriginGlobal.x + winLeft;
			
			// Invoke ClipCursor
			ClipCursor(&clipRect);

			// Prevent selection on this element
			m_pBehavior->m_spSel->empty();
			OnClick();
			break;
		
		case DISPID_HTMLDOCUMENTEVENTS2_ONMOUSEUP:
			// Prevent selection on this element
			m_pBehavior->m_spSel->empty();
			mouseDown = FALSE;

			// Free mouse cursor to move anywhere on screen
			ClipCursor(NULL);

			m_pBehavior->m_lPartID = -1;
			m_pBehavior->m_pPaintSite->InvalidateRect(NULL);
			break;

		case DISPID_HTMLDOCUMENTEVENTS2_ONMOUSEMOVE:
			// Prevent selection on this element
			m_pBehavior->m_spSel->empty();
			
			// If mouse button is not down, don't do anything
			if (mouseDown != TRUE) break;

			// Otherwise, recalculate position of the handle being moved and redraw
			hr = m_pBehavior->GetEventObject(&pEvent);

			// Obtain X & Y
			hr = pEvent->get_offsetY(&Y);
			hr = pEvent->get_offsetX(&X);

			m_pBehavior->m_ptPolyCorners[m_pBehavior->m_lPartID].x = X;
			m_pBehavior->m_ptPolyCorners[m_pBehavior->m_lPartID].y = Y;

			m_pBehavior->m_pPaintSite->InvalidateRect(NULL);
			pEvent->Release();

			break;

		default:
			break;
    }

    return S_OK;
}

void
CEventSink::OnClick()
{
	if (!m_pBehavior) return;

	HRESULT hr = NULL;
	IHTMLEventObj* pEvent = NULL;
		
	long X = NULL;
	long Y = NULL;
				
	hr = m_pBehavior->GetEventObject(&pEvent);
		
	// Obtain X & Y
	hr = pEvent->get_offsetY(&Y);
	hr = pEvent->get_offsetX(&X);
  		
	POINT mousePoint;
	mousePoint.x = X;
	mousePoint.y = Y;

	m_pBehavior->m_lPartID = -1;

	for (int i = 0; i < 4; i++)
	{
		if (m_pBehavior->Distance(mousePoint, m_pBehavior->m_ptPolyCorners[i]) <= HANDLE_RADIUS)
		{
			m_pBehavior->m_lPartID = i;
			m_pBehavior->m_pPaintSite->InvalidateRect(NULL);
			mouseDown = TRUE;
		}
	}

	pEvent->Release();
}

