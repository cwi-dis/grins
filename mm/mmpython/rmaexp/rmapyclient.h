#ifndef INC_RMAPYCLIENT
#define INC_RMAPYCLIENT

struct IPyClientContext: public IUnknown
	{
	};

struct IPyClientAdviseSink: public IRMAClientAdviseSink
	{
    STDMETHOD(SetPyAdviceSink)(THIS_
				PyObject *obj) PURE;
	};

struct IPyErrorSink: public IRMAErrorSink
	{
    STDMETHOD(SetPyErrorSink)(THIS_
				PyObject *obj) PURE;
	};

struct IPySiteSupplier: public IRMASiteSupplier
	{
    STDMETHOD(SetOsWindow)(THIS_
				void* p, 
				PyObject *pw) PURE;
    STDMETHOD(SetOsWindowPosSize)(THIS_
				PNxPoint p, 
				PNxSize s) PURE;
	};

struct IPyAuthenticationManager: public IRMAAuthenticationManager
	{
	};

HRESULT STDMETHODCALLTYPE CreateClientContext(IPyClientContext **ppI);
HRESULT STDMETHODCALLTYPE CreateClientAdviseSink(IPyClientAdviseSink **ppI);
HRESULT STDMETHODCALLTYPE CreateErrorSink(IPyErrorSink **ppI);
HRESULT STDMETHODCALLTYPE CreateSiteSupplier(IPySiteSupplier **ppI);
HRESULT STDMETHODCALLTYPE CreateAuthenticationManager(IPyAuthenticationManager **ppI);


#endif  // INC_RMAPYCLIENT
