
/***********************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

#include "Python.h"

#include "rma.h" 

// our client context interfaces
#include "rmapyclient.h"

// thread python callback helpers
#include "mtpycall.h"

class ClientAdviseSink : public IPyClientAdviseSink
	{
	public:
	ClientAdviseSink();
	~ClientAdviseSink();

	// IUnknown
    STDMETHOD (QueryInterface ) (THIS_ REFIID ID, void** ppInterfaceObj);
    STDMETHOD_(UINT32, AddRef ) (THIS);
    STDMETHOD_(UINT32, Release) (THIS);

    // IRMAClientAdviseSink
    STDMETHOD (OnPosLength)  (THIS_ UINT32 ulPosition, UINT32 ulLength);
    STDMETHOD (OnPresentationOpened) (THIS);
    STDMETHOD (OnPresentationClosed) (THIS);
    STDMETHOD (OnStatisticsChanged)  (THIS);
    STDMETHOD (OnPreSeek)    (THIS_ UINT32 ulOldTime, UINT32 ulNewTime);
    STDMETHOD (OnPostSeek)   (THIS_ UINT32 ulOldTime, UINT32 ulNewTime);
    STDMETHOD (OnStop)       (THIS);
    STDMETHOD (OnPause)      (THIS_ UINT32 ulTime);
    STDMETHOD (OnBegin)	     (THIS_ UINT32 ulTime);
    STDMETHOD (OnBuffering)  (THIS_ UINT32 ulFlags, UINT16 unPercentComplete);
    STDMETHOD (OnContacting) (THIS_ const char* pHostName);
	
	// ++ IPyClientAdviseSink
    STDMETHOD(SetPyAdviceSink)(THIS_
				PyObject *obj);
	
	private:
    LONG m_cRef;

	PyObject *m_pyAdviceSink;	
	};

#include "pythread.h"

HRESULT STDMETHODCALLTYPE CreateClientAdviseSink(
			IPyClientAdviseSink **ppI)
	{
	*ppI = new ClientAdviseSink();
	return S_OK;
	}


ClientAdviseSink::ClientAdviseSink()
:	m_cRef(1),
	m_pyAdviceSink(NULL)
	{
	}

ClientAdviseSink::~ClientAdviseSink()
	{
	Py_XDECREF(m_pyAdviceSink);	
	}

STDMETHODIMP
ClientAdviseSink::QueryInterface(
    REFIID riid,
    void **ppvObject)
	{
    if (IsEqualIID(riid,IID_IUnknown))
		{
		AddRef();
		*ppvObject = this;
		return PNR_OK;
		}
	else if(IsEqualIID(riid,IID_IRMAClientAdviseSink))
		{
		AddRef();
		*ppvObject = (IRMAClientAdviseSink*)this;
		return PNR_OK;
		}
    *ppvObject = NULL;	
	return PNR_NOINTERFACE;
	}

STDMETHODIMP_(UINT32)
ClientAdviseSink::AddRef()
	{
    return InterlockedIncrement(&m_cRef);
	}

STDMETHODIMP_(UINT32)
ClientAdviseSink::Release()
	{
    ULONG uRet = InterlockedDecrement(&m_cRef);
	if(uRet==0) 
		{
		delete this;
		}
    return uRet;
	}

STDMETHODIMP
ClientAdviseSink::OnPosLength(UINT32 ulPosition, UINT32 ulLength)
	{
	CallbackHelper helper("OnPosLength",m_pyAdviceSink);
	if(helper.cancall())
		{
		PyObject *args = Py_BuildValue("(ii)",ulPosition,ulLength);
		helper.call(args);
		}
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnPresentationOpened()
	{
	CallbackHelper helper("OnPresentationOpened",m_pyAdviceSink);
	if(helper.cancall())
		{
		PyObject *args = Py_BuildValue("()");
		helper.call(args);
		}
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnPresentationClosed()
	{
	CallbackHelper helper("OnPresentationClosed",m_pyAdviceSink);
	if(helper.cancall())
		{
		PyObject *args = Py_BuildValue("()");
		helper.call(args);
		}
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnStatisticsChanged()
	{
	CallbackHelper helper("OnStatisticsChanged",m_pyAdviceSink);
	if(helper.cancall())
		{
		PyObject *args = Py_BuildValue("()");
		helper.call(args);
		}
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnPreSeek(UINT32 ulOldTime, UINT32 ulNewTime)
	{
	CallbackHelper helper("OnPreSeek",m_pyAdviceSink);
	if(helper.cancall())
		{
		PyObject *args = Py_BuildValue("(ii)",ulOldTime,ulNewTime);
		helper.call(args);
		}
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnPostSeek(UINT32 ulOldTime, UINT32 ulNewTime)
	{
	CallbackHelper helper("OnPostSeek",m_pyAdviceSink);
	if(helper.cancall())
		{
		PyObject *args = Py_BuildValue("(ii)",ulOldTime,ulNewTime);
		helper.call(args);
		}
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnStop()
	{
	CallbackHelper helper("OnStop",m_pyAdviceSink);
	if(helper.cancall())
		{
		PyObject *args = Py_BuildValue("()");
		helper.call(args);
		}
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnPause(UINT32 ulTime)
	{
	CallbackHelper helper("OnPause",m_pyAdviceSink);
	if(helper.cancall())
		{
		PyObject *args = Py_BuildValue("(i)",ulTime);
		helper.call(args);
		}
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnBegin(UINT32 ulTime)
	{
	CallbackHelper helper("OnBegin",m_pyAdviceSink);
	if(helper.cancall())
		{
		PyObject *args = Py_BuildValue("(i)",ulTime);
		helper.call(args);
		}
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnBuffering(UINT32 ulFlags, UINT16 unPercentComplete)
	{
	CallbackHelper helper("OnBuffering",m_pyAdviceSink);
	if(helper.cancall())
		{
		PyObject *args = Py_BuildValue("(ii)",ulFlags,int(unPercentComplete));
		helper.call(args);
		}	
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnContacting(const char* pHostName)
	{
	CallbackHelper helper("OnContacting",m_pyAdviceSink);
	if(helper.cancall())
		{
		PyObject *args = Py_BuildValue("(s)",pHostName);
		helper.call(args);
		}	
	return PNR_OK;
	}


STDMETHODIMP 
ClientAdviseSink::SetPyAdviceSink(PyObject *obj)
	{
	Py_XDECREF(m_pyAdviceSink);
	if(obj==Py_None)m_pyAdviceSink=NULL;
	else m_pyAdviceSink=obj;
	Py_XINCREF(m_pyAdviceSink);
	return PNR_OK;
	}
