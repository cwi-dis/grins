#ifndef INC_DSCOM
#define INC_DSCOM

DEFINE_GUID(IID_IRealConverter,
0xe8d61c44, 0xd313, 0x472a, 0x84, 0x68, 0x2b, 0x1e, 0xd5, 0xb0, 0x5c, 0xab);
interface IRealConverter : public IUnknown
	{
	virtual HRESULT __stdcall SetInterface(IUnknown *p,LPCOLESTR hint)=0;
	};

	
// {34F6B2C9-16AD-4454-A76D-2EB8EEA06C80}
DEFINE_GUID(IID_IRendererAdviceSink, 
0x34f6b2c9, 0x16ad, 0x4454, 0xa7, 0x6d, 0x2e, 0xb8, 0xee, 0xa0, 0x6c, 0x80);
interface IRendererAdviceSink : public IUnknown
	{
	virtual HRESULT __stdcall OnSetMediaType(const CMediaType *pmt) = 0;
	virtual HRESULT __stdcall OnActive() = 0;
	virtual HRESULT __stdcall OnInactive() = 0;
	virtual HRESULT __stdcall OnRenderSample(IMediaSample *pMediaSample) = 0; 
	};

// {BDBC884C-0FCE-414f-9941-035F900E43B6}
DEFINE_GUID(IID_IPipe,
0xbdbc884c, 0xfce, 0x414f, 0x99, 0x41, 0x3, 0x5f, 0x90, 0xe, 0x43, 0xb6);
interface IPipe : public IUnknown
	{
	virtual HRESULT __stdcall SetRendererAdviceSink(IRendererAdviceSink *pI) = 0;
	};

// {F9EA0C30-85C8-42f8-8FEE-04E248AAE59C}
DEFINE_GUID(IID_IPyListener,
0xf9ea0c30, 0x85c8, 0x42f8, 0x8f, 0xee, 0x4, 0xe2, 0x48, 0xaa, 0xe5, 0x9c);
interface IPyListener: public IUnknown
	{
	virtual HRESULT __stdcall SetPyListener(PyObject *pyobj) = 0;
	};

HRESULT STDMETHODCALLTYPE CreatePyRenderingListener(PyObject *pyobj, IPyListener **ppI);


#endif

