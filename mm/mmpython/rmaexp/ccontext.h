#ifndef INC_CCONTEXT
#define INC_CCONTEXT

struct IClientContext: public IUnknown
	{
	};

HRESULT STDMETHODCALLTYPE CreateClientContext(IClientContext **ppI);


#endif  //INC_CCONTEXT
