
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

class ErrorSink : public IPyErrorSink
	{
	public:
	ErrorSink();
	~ErrorSink();

	// IUnknown
    STDMETHOD (QueryInterface ) (THIS_ REFIID ID, void** ppInterfaceObj);
    STDMETHOD_(UINT32, AddRef ) (THIS);
    STDMETHOD_(UINT32, Release) (THIS);

	// IRMAErrorSink
    STDMETHOD(ErrorOccurred)	(THIS_
				const UINT8	unSeverity,  
				const ULONG32	ulRMACode,
				const ULONG32	ulUserCode,
				const char*	pUserString,
				const char*	pMoreInfoURL
				);
	
	// ++ IPyErrorSink
    STDMETHOD(SetPyErrorSink)(THIS_
				PyObject *obj);
    STDMETHOD(SetErrorMessagesSupplier)(THIS_
		IRMAErrorMessages* p){
		m_pIRMAErrorMessages = p;p->AddRef();return PNR_OK;
		}
	
	private:
    LONG m_cRef;

	PyObject *m_pyErrorSink;
	
    void ConvertErrorToString(const ULONG32 ulRMACode, char* pszBuffer);
	const char* ConvertErrorTypeToString(int type);	
	IRMAErrorMessages *m_pIRMAErrorMessages;
	};

HRESULT STDMETHODCALLTYPE CreateErrorSink(
			IPyErrorSink **ppI)
	{
	*ppI = new ErrorSink();
	return S_OK;
	}


ErrorSink::ErrorSink()
:	m_cRef(1),
	m_pyErrorSink(NULL),
	m_pIRMAErrorMessages(NULL)
	{
	}

ErrorSink::~ErrorSink()
	{
	Py_XDECREF(m_pyErrorSink);
	}

STDMETHODIMP
ErrorSink::QueryInterface(
    REFIID riid,
    void **ppvObject)
	{
    if (IsEqualIID(riid,IID_IUnknown))
		{
		AddRef();
		*ppvObject = this;
		return PNR_OK;
		}
	else if(IsEqualIID(riid,IID_IRMAErrorSink))
		{
		AddRef();
		*ppvObject = (IRMAErrorSink*)this;
		return PNR_OK;
		}
    *ppvObject = NULL;	
	return PNR_NOINTERFACE;
	}

STDMETHODIMP_(UINT32)
ErrorSink::AddRef()
	{
    return  InterlockedIncrement(&m_cRef);
	}

STDMETHODIMP_(UINT32)
ErrorSink::Release()
	{
    ULONG uRet = InterlockedDecrement(&m_cRef);
	if(uRet==0) 
		{
		delete this;
		}
    return uRet;
	}

STDMETHODIMP 
ErrorSink::ErrorOccurred
	(
	const UINT8	unSeverity,  
	const ULONG32	ulRMACode,
	const ULONG32	ulUserCode,
	const char*	pUserString,
	const char*	pMoreInfoURL
	)
	{
    char RMADefine[256]="\0";
	IRMABuffer* pIRMABuffer=NULL;
	if(m_pIRMAErrorMessages)
		{
		// GetErrorText seems to return NULL
		// but I think that what the RMACore has to say
		// is in ulRMACode and pUserString
		pIRMABuffer=m_pIRMAErrorMessages->GetErrorText(ulRMACode);
		if(pIRMABuffer)
			{
			ULONG32 l=pIRMABuffer->GetSize();
			l=min(l,255);
			strncpy(RMADefine,(char*)pIRMABuffer->GetBuffer(),l);
			RMADefine[l]='\0';
			}
		}
	if(!pIRMABuffer)
		ConvertErrorToString(ulRMACode, RMADefine);

	// Crack RMACode to error type, subtype
#ifndef _WIN32
	int shift=16;
#else
	int shift=6;
#endif
	int type = 0xFF & (ulRMACode >> shift);
	int subtype = 0x3F & ulRMACode;

 	// ulRMACode is returned and its meaning can be found RMASDK::pnresult.h
    char msg[512];
#if 0
    sprintf(msg, "RMA error report:\n(%d, 0x%x, \"%s\", %ld, \"%s\", \"%s\")\nCategory: %s (E%d.%d)\n",
		    unSeverity,
		    ulRMACode,
		    (pUserString && *pUserString) ? pUserString : "(NULL)",
		    ulUserCode,
		    (pMoreInfoURL && *pMoreInfoURL) ? pMoreInfoURL : "(NULL)",
            RMADefine,
			ConvertErrorTypeToString(type),type,subtype
			);
#else
	msg[0] = '\0';
	if ( *RMADefine ) 
		strcpy(msg, RMADefine);
	else {
		if ( pUserString && *pUserString )
			strcpy(msg, pUserString);
		else
			sprintf(msg, "RMA error %d 0x%x", unSeverity, ulRMACode);
		}
	if ( pMoreInfoURL && *pMoreInfoURL ) {
		strcat(msg, " See ");
		strcat(msg, pMoreInfoURL);
	}
#endif
	CallbackHelper helper("ErrorOccurred",m_pyErrorSink);
	if(helper.cancall())
		{
		PyObject *args = Py_BuildValue("(s)",msg);
		helper.call(args);
		}
    return PNR_OK;
	}

STDMETHODIMP 
ErrorSink::SetPyErrorSink(PyObject *obj)
	{
	Py_XDECREF(m_pyErrorSink);
	if(obj==Py_None)m_pyErrorSink=NULL;
	else m_pyErrorSink=obj;
	Py_XINCREF(m_pyErrorSink);
	return PNR_OK;
	}

// ConvertErrorToString uses complete 
// extern errorlist from rma.cpp
extern struct errors {
	PN_RESULT error;
	char *name;
} errorlist [];

void
ErrorSink::ConvertErrorToString(const ULONG32 ulRMACode, char* pszBuffer)
	{
    PN_RESULT theErr = (PN_RESULT) ulRMACode;
	struct errors *p;
	for (p = errorlist; p->name; p++)
		if (p->error == theErr) {
			strcpy(pszBuffer,"PNR_");
			strcat(pszBuffer,p->name);
			return;
		}
	}

const char* 
ErrorSink::ConvertErrorTypeToString(int type)
	{
	switch(type)
		{
		case SS_GLO: return "General errors";
		case SS_NET: return "Networking errors";
		case SS_FIL: return "File errors";
		case SS_PRT: return "Protocol Error";
		case SS_AUD: return "Audio error";
		case SS_INT: return "General internal errors";
		case SS_USR: return "The user is broken.";
		case SS_MSC: return "Miscellaneous";
		case SS_DEC: return "Decoder errors";
		case SS_ENC: return "Encoder errors";
		case SS_REG: return "Registry (not Windows registry ;) errors";
		case SS_PPV: return "Pay Per View errors";
		case SS_RSC: return "Errors for PNXRES";
		case SS_UPG: return "Auto-upgrade & Certificate Errors";
		case SS_PLY: return "RealPlayer/Plus specific errors (USE ONLY IN /rpmisc/pub/rpresult.h)";
		case SS_RMT: return "RMTools Errors";
		case SS_CFG: return "AutoConfig Errors";
		case SS_RPX: return "RealPix-related Errors";
		case SS_XML: return "XML-related Errors";
		case SS_DPR: return "Deprecated errors";
		}
	return "Uknown Error";
	}
