// Behavior.cpp : Implementation of CBehavior
#include "stdafx.h"
#include "GRiNSRenderer.h"
#include "EventSink.h"
#include "Behavior.h"
#include "math.h"

#include "appconst.h"

#include <ddraw.h>
#define _DEFINE_GUID(name, l, w1, w2, b1, b2, b3, b4, b5, b6, b7, b8) \
        EXTERN_C const GUID name \
                = { l, w1, w2, { b1, b2,  b3,  b4,  b5,  b6,  b7,  b8 } }
_DEFINE_GUID(IID_IDirectDrawSurface,0x6C14DB81,0xA733,0x11CE,0xA5,0x21,0x00,0x20,0xAF,0x0B,0xE5,0x60);

/////////////////////////////////////////////////////////////////////////////
// CBehavior

///////////////////////////////////////////////
// IElementBehavior implementation
//
STDMETHODIMP
CBehavior::Detach(void)
{
	// Release cached EventSink and PaintSite pointers
	// (Note: Other cached pointers are smart pointers and
	// automatically release themselves)
	m_pEventSink->Release();
	m_pPaintSite->Release();

	return S_OK;
}

STDMETHODIMP
CBehavior::Init(IElementBehaviorSite* pBehaviorSite)
{
	HRESULT hr;

	// Cache the IElementBehaviorSite interface pointer.
	m_spSite = pBehaviorSite;

	// Cache the IElementBehaviorSiteOM interface pointer.
	hr = m_spSite->QueryInterface(
							IID_IElementBehaviorSiteOM,
							(void**)&m_spOMSite);
	if (FAILED(hr)) return hr;
	
	// Cache the IHTMLPaintSite interface pointer.
	hr = m_spSite->QueryInterface(
							IID_IHTMLPaintSite,
							(void**)&m_pPaintSite);
	if (FAILED(hr)) return hr;


	return hr;
}

STDMETHODIMP
CBehavior::Notify(LONG lEvent, VARIANT* pVar)
{
	HRESULT hr = S_OK;

	switch (lEvent)
	{
		// The HTML document has been parsed. The DOM is available
		case BEHAVIOREVENT_DOCUMENTREADY:
			if (!m_spSite) break;
			
			// Cache the IHTMLElement interface pointer for this element
			// and its parent
			hr = m_spSite->GetElement(&m_spElem);
			hr = m_spElem->get_offsetParent(&m_spParent);

			// Cache the IHTMLDocument2 interface pointer
			IDispatch* pDisp;
			hr = m_spElem->get_document(&pDisp);
			hr = pDisp->QueryInterface(IID_IHTMLDocument2, (void**)&m_spDoc);
			pDisp->Release();

			// Cache the IHTMLWindow2 interface pointer
			hr = m_spDoc->get_parentWindow(&m_spWin);

			// Cache the IHTMLSelectionObject interface pointer
			hr = m_spDoc->get_selection(&m_spSel);
			
			// Change mouse cursor to arrow only for this element
			IHTMLStyle* pStyle;
			hr = m_spElem->get_style(&pStyle);
			hr = pStyle->put_cursor(L"default");
			pStyle->Release();

			long lHeight, lWidth;

			m_spElem->get_offsetHeight(&lHeight);
			m_spElem->get_offsetWidth(&lWidth);
			
			// Cache the initial coordinates of the element's 
			// corner points
			m_rtElemCorners.top = 0;
			m_rtElemCorners.bottom = lHeight; 
			m_rtElemCorners.left = 0;
			m_rtElemCorners.right = lWidth;
			
			// Set the initial coordinates of the polygon to
			// the element's corner points
			m_ptPolyCorners[0].x = lWidth/8;
			m_ptPolyCorners[0].y = lHeight/8;
			m_ptPolyCorners[1].x = 3*lWidth/4;
			m_ptPolyCorners[1].y = lHeight/8;
			m_ptPolyCorners[2].x = 3*lWidth/4;
			m_ptPolyCorners[2].y = 3*lHeight/4;
			m_ptPolyCorners[3].x = lWidth/8;
			m_ptPolyCorners[3].y = 3*lHeight/4;

	
			// Create and connect the event sink.
			hr = CComObject<CEventSink>::CreateInstance(&m_pEventSink);
			if (SUCCEEDED(hr))
			{
				m_pEventSink->AddRef();
				m_pEventSink->m_pBehavior = this;

				hr = AtlAdvise(m_spElem, (IDispatch*)m_pEventSink,
									DIID_HTMLElementEvents,
									&m_dwCookie);
			}
			break;

		default:
			break;
	}

	return S_OK;
}

///////////////////////////////////////////
// IHTMLPainter Method Implementation
//
HRESULT CBehavior::Draw(RECT rcBounds, RECT rcUpdate, LONG lDrawFlags, HDC hdc, LPVOID pvDrawObject)
{
	if (!m_pEventSink) return S_OK;

	IDirectDrawSurface *dds = (IDirectDrawSurface*)pvDrawObject;
	HRESULT hr = dds->GetDC(&hdc);
	if (FAILED(hr)) return hr;
	
	HBRUSH blackBrush     = (HBRUSH)GetStockObject(BLACK_BRUSH);
	HBRUSH coloredBrush   = CreateSolidBrush(RGB(0x99,0x66,0x99));
	HBRUSH highlightBrush = CreateSolidBrush(RGB(0xff, 0xff, 0x00));
	HPEN   blackPen       = (HPEN)GetStockObject(BLACK_PEN);

	HPEN   oldPen         = (HPEN)SelectObject(hdc,blackPen);
	HBRUSH oldBrush       = (HBRUSH)SelectObject(hdc,coloredBrush);
	
	POINT	ptGlobalCorners[4];
	
	for (int i = 0; i < 4; i++)
	{
		ptGlobalCorners[i].x = m_ptPolyCorners[i].x + rcBounds.left + HANDLE_RADIUS;
		ptGlobalCorners[i].y = m_ptPolyCorners[i].y + rcBounds.top + HANDLE_RADIUS;
	}
	
	Polygon(hdc, ptGlobalCorners, 4);

	for (i = 0; i < 4; i++)
	{
		if (m_pEventSink->mouseDown && m_lPartID == i)
			SelectObject(hdc, highlightBrush);
		else
			SelectObject(hdc, blackBrush);

		Ellipse(hdc,
				ptGlobalCorners[i].x - HANDLE_RADIUS,
				ptGlobalCorners[i].y - HANDLE_RADIUS,
				ptGlobalCorners[i].x + HANDLE_RADIUS,
				ptGlobalCorners[i].y + HANDLE_RADIUS);
	}

	SelectObject(hdc, oldPen);
	SelectObject(hdc, oldBrush);
	
	DeleteObject(coloredBrush);
	DeleteObject(highlightBrush);

	dds->ReleaseDC(hdc);
	
	return S_OK;
}

HRESULT CBehavior::GetPainterInfo(HTML_PAINTER_INFO *pInfo)
{
	//pInfo->lFlags = HTMLPAINTER_OPAQUE | HTMLPAINTER_HITTEST;
	pInfo->lFlags = HTMLPAINTER_OPAQUE | HTMLPAINTER_HITTEST | HTMLPAINTER_SURFACE;
	pInfo->lZOrder = HTMLPAINT_ZORDER_ABOVE_CONTENT;

	// request an IDirectDrawSurface
	//memset(&pInfo->iidDrawObject, 0, sizeof(IID));
	memcpy(&pInfo->iidDrawObject, &IID_IDirectDrawSurface, sizeof(IID));

	pInfo->rcExpand.left = HANDLE_RADIUS;
	pInfo->rcExpand.right = HANDLE_RADIUS;
	pInfo->rcExpand.top = HANDLE_RADIUS;
	pInfo->rcExpand.bottom = HANDLE_RADIUS;

	return S_OK;
}

HRESULT CBehavior::HitTestPoint(POINT pt, BOOL *pbHit, LONG *plPartID)
{
	if (!m_pEventSink) return S_OK;
	if (m_pEventSink->mouseDown) return S_OK;

	*pbHit = FALSE;
	*plPartID = NULL;
	m_lPartID = -1;

	// Convert point coordinates, which are given with respect to the element's
	// expanded region, to reflect the element without its expanded region
	pt.x = pt.x - HANDLE_RADIUS;
	pt.y = pt.y - HANDLE_RADIUS;

	for (int i = 0; i < 4; i++)
	{
		if (Distance(pt, m_ptPolyCorners[i]) <= HANDLE_RADIUS)
		{
			// Setting pbHit to TRUE will trigger an event that can be handled
			// by IEventSink::Invoke
			*pbHit = TRUE;
			*plPartID = i;
			m_lPartID = i;
		}
	}

	return S_OK;
}

HRESULT CBehavior::OnResize(SIZE pt)
{
	if (!m_spElem) return E_FAIL;

	long lHeight, lWidth, lOldElemHeight, lOldElemWidth;
	float ratioX, ratioY;

	lOldElemHeight = m_rtElemCorners.bottom;
	lOldElemWidth = m_rtElemCorners.right;

	m_spElem->get_offsetHeight(&lHeight);
	m_spElem->get_offsetWidth(&lWidth);

	m_rtElemCorners.top = 0;
	m_rtElemCorners.bottom = lHeight; 
	m_rtElemCorners.left = 0;
	m_rtElemCorners.right = lWidth;

	ratioX = (float)lWidth/(float)lOldElemWidth;
	ratioY = (float)lHeight/(float)lOldElemHeight;

	for (int i = 0; i < 4; i++)
	{
		m_ptPolyCorners[i].x = (long)(ratioX * m_ptPolyCorners[i].x);
		m_ptPolyCorners[i].y = (long)(ratioY * m_ptPolyCorners[i].y);
	}

	return S_OK;
}

/////////////////////////////////////////////
// Helper functions
//
// Calculates the distance between two points
double
CBehavior::Distance(POINT pt1, POINT pt2)
{
	return _hypot((pt1.x - pt2.x), (pt1.y - pt2.y));
}

// Retrieves the window's IHTMLEventObj interface
HRESULT
CBehavior::GetEventObject(IHTMLEventObj** ppEvent)
{
	HRESULT				hr;
	
	hr = m_spWin->get_event(ppEvent);
	if (*ppEvent == NULL) hr =  E_FAIL;

	return hr;
}

