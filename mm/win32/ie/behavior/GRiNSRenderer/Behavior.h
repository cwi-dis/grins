// Behavior.h : Declaration of the CBehavior

#ifndef __BEHAVIOR_H_
#define __BEHAVIOR_H_

#include "resource.h"       // main symbols
#include "EventSink.h"

#define HANDLE_RADIUS 10

/////////////////////////////////////////////////////////////////////////////
// CBehavior
class ATL_NO_VTABLE CBehavior : 
	public CComObjectRootEx<CComSingleThreadModel>,
	public CComCoClass<CBehavior, &CLSID_Behavior>,
	public IDispatchImpl<IBehavior, &IID_IBehavior, &LIBID_GRINSRENDERERLib>,
	public IElementBehavior,
	public IHTMLPainter
{
public:
	CComPtr<IElementBehaviorSite>	m_spSite;
	CComPtr<IElementBehaviorSiteOM>	m_spOMSite;
	IHTMLPaintSite*					m_pPaintSite;
	CComPtr<IHTMLElement>           m_spElem;
	CComPtr<IHTMLElement>           m_spParent;
	CComPtr<IHTMLDocument2>			m_spDoc;
	CComPtr<IHTMLWindow2>			m_spWin;
	CComPtr<IHTMLSelectionObject>	m_spSel;
	CComObject<CEventSink>*         m_pEventSink;
	DWORD                           m_dwCookie;
	long							m_lCookie;
	RECT							m_rtElemCorners;
	POINT							m_ptPolyCorners[4];
	long							m_lPartID;

	CBehavior() : 
		m_pEventSink(NULL),
		m_dwCookie(0),
		m_lPartID(-1)
	{
	}

	DECLARE_REGISTRY_RESOURCEID(IDR_BEHAVIOR)
	DECLARE_NOT_AGGREGATABLE(CBehavior)

	BEGIN_COM_MAP(CBehavior)
		//COM_INTERFACE_ENTRY(IBehavior)
		COM_INTERFACE_ENTRY(IDispatch)
		COM_INTERFACE_ENTRY(IElementBehavior)
		COM_INTERFACE_ENTRY(IHTMLPainter)
	END_COM_MAP()

// IElementBehavior
public:
	STDMETHOD(Detach)(void);
	STDMETHOD(Init)(IElementBehaviorSite* pBehaviorSite);
	STDMETHOD(Notify)(LONG lEvent, VARIANT* pVar);

// IHTMLPainter
public:
	STDMETHOD(Draw)(RECT rcBounds, RECT rcUpdate, LONG lDrawFlags, HDC hdc, LPVOID pvDrawObject);
	STDMETHOD(GetPainterInfo)(HTML_PAINTER_INFO *pInfo);
	STDMETHOD(HitTestPoint)(POINT pt, BOOL *pbHit, LONG *plPartID);
	STDMETHOD(OnResize)(SIZE pt);

	// Helper functions
	double Distance(POINT pt1, POINT pt2);
	HRESULT GetEventObject(IHTMLEventObj** event);
};

#endif //__BEHAVIOR_H_
