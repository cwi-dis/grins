/****************************************************************************
 * 
 *  $Id$
 *  
 */
#ifndef _EXSITSUP_H_
#define _EXSITSUP_H_


/****************************************************************************
 *
 *  ExampleSiteSupplier Class
 *
 *  Implementation for ragui's IRMASiteSupplier.
 */
class ExampleSiteSupplier :  public IRMASiteSupplier
{
    /****** Private Class Variables ****************************************/
    INT32 m_lRefCount;
    IRMASiteManager* m_pSiteManager;
    IRMACommonClassFactory* m_pCCF;
    IUnknown* m_pUnkPlayer;
    FiveMinuteMap m_CreatedSites;

	PNxWindow m_PNxWindow;
	BOOL m_showInNewWnd;
	
	PNxPoint m_positionInWindow;
	PNxSize  m_sizeInWindow;
	BOOL m_posSizeValid;

    public:
    /****** Public Class Methods ******************************************/
    ExampleSiteSupplier(IUnknown* pUnkPlayer);
    

    /************************************************************************
     *  Custom Interface Methods                     
	 */
	void SetOsWindow(void* p){m_PNxWindow.window=p;}
	void ShowInNewWindow(BOOL f){m_showInNewWnd=f;}
	void SetOsWindowPosSize(PNxPoint p, PNxSize s) {
		m_positionInWindow = p;
		m_sizeInWindow = s;
		// Try by Jack
		m_PNxWindow.x = p.x;
		m_PNxWindow.y = p.y;
		m_PNxWindow.width = s.cx;
		m_PNxWindow.height = s.cy;
		m_PNxWindow.clipRect.left = p.x;
		m_PNxWindow.clipRect.top = p.y;
		m_PNxWindow.clipRect.right = p.x+s.cx;
		m_PNxWindow.clipRect.bottom = p.y+s.cy;
		// End try
		
		m_posSizeValid = 1;
	}


    /************************************************************************
     *  IRMASiteSupplier Interface Methods                     ref:  rmawin.h
     */
    STDMETHOD(SitesNeeded) (THIS_ UINT32 uRequestID, IRMAValues* pSiteProps);
    STDMETHOD(SitesNotNeeded) (THIS_ UINT32 uRequestID);
    STDMETHOD(BeginChangeLayout) (THIS);
    STDMETHOD(DoneChangeLayout) (THIS);


    /************************************************************************
     *  IUnknown COM Interface Methods                          ref:  pncom.h
     */
    STDMETHOD (QueryInterface ) (THIS_ REFIID ID, void** ppInterfaceObj);
    STDMETHOD_(UINT32, AddRef ) (THIS);
    STDMETHOD_(UINT32, Release) (THIS);

    private:
    /****** Private Class Methods ******************************************/
    ~ExampleSiteSupplier();
    
    PRIVATE_DESTRUCTORS_ARE_NOT_A_CRIME       // Avoids GCC compiler warning
};


#endif /* _EXSITSUP_H_ */

