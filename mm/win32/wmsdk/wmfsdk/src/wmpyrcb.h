#ifndef INC_WMPYRCB
#define INC_WMPYRCB

interface IWMPyReaderCallback: public IWMReaderCallback
{
	virtual HRESULT STDMETHODCALLTYPE SetListener( 
            /* [in] */		PyObject *pyobj) = 0;
	virtual HRESULT STDMETHODCALLTYPE WaitOpen(
            /* [in] */		DWORD dwMilliseconds,
			/* [out] */		DWORD *pdwWaitRes) = 0;
	virtual HRESULT STDMETHODCALLTYPE WaitForCompletion(
            /* [in] */		DWORD dwMilliseconds,
			/* [out] */		DWORD *pdwWaitRes) = 0;				
};

HRESULT STDMETHODCALLTYPE WMCreatePyReaderCallback(PyObject *pyobj, IWMPyReaderCallback **ppI);


#endif  //INC_WMPYRCB





