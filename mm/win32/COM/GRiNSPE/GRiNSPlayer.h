// GRiNSPlayer.h : Declaration of the GRiNSPlayer

#ifndef __GRINSPLAYER_H_
#define __GRINSPLAYER_H_

#include "resource.h"       // main symbols
#include <atlctl.h>


/////////////////////////////////////////////////////////////////////////////
// GRiNSPlayer
class ATL_NO_VTABLE GRiNSPlayer : 
	public CComObjectRootEx<CComSingleThreadModel>,
	public IDispatchImpl<IGRiNSPlayer, &IID_IGRiNSPlayer, &LIBID_GRINSPELib>,
	public CComControl<GRiNSPlayer>,
	public IPersistStreamInitImpl<GRiNSPlayer>,
	public IOleControlImpl<GRiNSPlayer>,
	public IOleObjectImpl<GRiNSPlayer>,
	public IOleInPlaceActiveObjectImpl<GRiNSPlayer>,
	public IViewObjectExImpl<GRiNSPlayer>,
	public IOleInPlaceObjectWindowlessImpl<GRiNSPlayer>,
	public IPersistStorageImpl<GRiNSPlayer>,
	public ISpecifyPropertyPagesImpl<GRiNSPlayer>,
	public IQuickActivateImpl<GRiNSPlayer>,
	public IDataObjectImpl<GRiNSPlayer>,
	public IProvideClassInfo2Impl<&CLSID_GRiNSPlayer, NULL, &LIBID_GRINSPELib>,
	public CComCoClass<GRiNSPlayer, &CLSID_GRiNSPlayer>
{
public:
	GRiNSPlayer()
	{
	}

DECLARE_REGISTRY_RESOURCEID(IDR_GRINSPLAYER)

DECLARE_PROTECT_FINAL_CONSTRUCT()

BEGIN_COM_MAP(GRiNSPlayer)
	COM_INTERFACE_ENTRY(IGRiNSPlayer)
	COM_INTERFACE_ENTRY(IDispatch)
	COM_INTERFACE_ENTRY(IViewObjectEx)
	COM_INTERFACE_ENTRY(IViewObject2)
	COM_INTERFACE_ENTRY(IViewObject)
	COM_INTERFACE_ENTRY(IOleInPlaceObjectWindowless)
	COM_INTERFACE_ENTRY(IOleInPlaceObject)
	COM_INTERFACE_ENTRY2(IOleWindow, IOleInPlaceObjectWindowless)
	COM_INTERFACE_ENTRY(IOleInPlaceActiveObject)
	COM_INTERFACE_ENTRY(IOleControl)
	COM_INTERFACE_ENTRY(IOleObject)
	COM_INTERFACE_ENTRY(IPersistStreamInit)
	COM_INTERFACE_ENTRY2(IPersist, IPersistStreamInit)
	COM_INTERFACE_ENTRY(ISpecifyPropertyPages)
	COM_INTERFACE_ENTRY(IQuickActivate)
	COM_INTERFACE_ENTRY(IPersistStorage)
	COM_INTERFACE_ENTRY(IDataObject)
	COM_INTERFACE_ENTRY(IProvideClassInfo)
	COM_INTERFACE_ENTRY(IProvideClassInfo2)
END_COM_MAP()

BEGIN_PROP_MAP(GRiNSPlayer)
	PROP_DATA_ENTRY("_cx", m_sizeExtent.cx, VT_UI4)
	PROP_DATA_ENTRY("_cy", m_sizeExtent.cy, VT_UI4)
	// Example entries
	// PROP_ENTRY("Property Description", dispid, clsid)
	// PROP_PAGE(CLSID_StockColorPage)
END_PROP_MAP()

BEGIN_MSG_MAP(GRiNSPlayer)
	CHAIN_MSG_MAP(CComControl<GRiNSPlayer>)
	DEFAULT_REFLECTION_HANDLER()
END_MSG_MAP()
// Handler prototypes:
//  LRESULT MessageHandler(UINT uMsg, WPARAM wParam, LPARAM lParam, BOOL& bHandled);
//  LRESULT CommandHandler(WORD wNotifyCode, WORD wID, HWND hWndCtl, BOOL& bHandled);
//  LRESULT NotifyHandler(int idCtrl, LPNMHDR pnmh, BOOL& bHandled);



// IViewObjectEx
	DECLARE_VIEW_STATUS(VIEWSTATUS_SOLIDBKGND | VIEWSTATUS_OPAQUE)

// IGRiNSPlayer
public:
	STDMETHOD(Pause)();
	STDMETHOD(Stop)();
	STDMETHOD(Play)();
	STDMETHOD(Open)(/*[in]*/ BSTR fileOrUrl);

	HRESULT OnDraw(ATL_DRAWINFO& di)
	{
		RECT& rc = *(RECT*)di.prcBounds;
		Rectangle(di.hdcDraw, rc.left, rc.top, rc.right, rc.bottom);

		SetTextAlign(di.hdcDraw, TA_CENTER|TA_BASELINE);
		LPCTSTR pszText = _T("GRiNS Player for SMIL20");
		TextOut(di.hdcDraw, 
			(rc.left + rc.right) / 2, 
			(rc.top + rc.bottom) / 2, 
			pszText, 
			lstrlen(pszText));

		return S_OK;
	}
};

#endif //__GRINSPLAYER_H_
