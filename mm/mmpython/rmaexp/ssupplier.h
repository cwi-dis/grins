#ifndef INC_SSUPPLIER
#define INC_SSUPPLIER

struct IPySiteSupplier: public IRMASiteSupplier
	{
    STDMETHOD(SetOsWindow)(THIS_
				void* p, 
				PyObject *pw) PURE;
    STDMETHOD(SetOsWindowPosSize)(THIS_
				PNxPoint p, 
				PNxSize s) PURE;
	};

HRESULT STDMETHODCALLTYPE CreateSiteSupplier(IPySiteSupplier **ppI);

#endif
