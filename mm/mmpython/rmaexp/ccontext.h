#ifndef INC_CCONTEXT
#define INC_CCONTEXT


struct IClientContext: public IUnknown
	{
	// ...
	
	// IUnknown
    STDMETHOD(QueryInterface)(THIS_
				REFIID riid,
				void** ppvObj) PURE;
    STDMETHOD_(ULONG32,AddRef)	(THIS) PURE;
    STDMETHOD_(ULONG32,Release)	(THIS) PURE;
	};

HRESULT STDMETHODCALLTYPE CreateClientContext(IClientContext **ppI);


#endif  //INC_CCONTEXT
