/****************************************************************************
 * 
 *  $Id$
 *
 *
 *  GRiNS Implementation of IRMAErrorSink Interface
 *
 */


/****************************************************************************
 * Includes
 */
#include "Std.h"
#include "PyCppApi.h"

#include "pncom.h"
#include "rmacomm.h"
#include "rmaerror.h"

#include "os.h"
#include "exerror.h"
#include "mtpycall.h"

extern char *geterrorstring(PN_RESULT res, char *pszBuffer);

// we need IRMABuffer
#include "rmapckts.h"  /* IRMABuffer, IRMAPacket, IRMAValues */

/****************************************************************************
 *  ExampleErrorSink::ExampleErrorSink                        ref:  exerror.h
 *
 *  Constructor
 */
ExampleErrorSink::ExampleErrorSink(IUnknown* /*IN*/pUnknown) 
    :m_lRefCount(0),
	m_pIRMAErrorMessages(NULL),
	m_pyErrorSink(NULL)
{
	PN_RESULT res=pUnknown->QueryInterface(IID_IRMAErrorMessages, (void**)&m_pIRMAErrorMessages);
	if(res!=PNR_OK || m_pIRMAErrorMessages == NULL)
		{
		m_pIRMAErrorMessages=NULL;
		MessageLog("Failed to create IRMAErrorMessages");
		}

}


/****************************************************************************
 *  ExampleErrorSink::~ExampleErrorSink                       ref:  exerror.h
 *
 *  Destructor
 */
ExampleErrorSink::~ExampleErrorSink()
{
	Py_XDECREF(m_pyErrorSink);
	m_pyErrorSink=NULL;
	if(m_pIRMAErrorMessages)
		m_pIRMAErrorMessages->Release();
}


void ExampleErrorSink::SetPyErrorSink(PyObject *obj)
	{
	Py_XDECREF(m_pyErrorSink);
	m_pyErrorSink=obj;
	Py_XINCREF(m_pyErrorSink);
	}

// IRMAErrorSink Interface Methods

/****************************************************************************
 *  IRMAErrorSink::ErrorOccurred                             ref:  rmaerror.h
 *  pUserString contains the RMACore explanation of the error
 */
STDMETHODIMP 
ExampleErrorSink::ErrorOccurred(const UINT8	unSeverity,  
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
	else
	if ( pUserString && *pUserString )
		strcpy(msg, pUserString);
	else
		sprintf(msg, "RMA error %d 0x%x", unSeverity, ulRMACode);
	if ( pMoreInfoURL && *pMoreInfoURL ) {
		strcat(msg, " See ");
		strcat(msg, pMoreInfoURL);
	}
#endif
	if(m_pyErrorSink)
		{
		CallbackHelper helper("ErrorOccurred",m_pyErrorSink);
		if(helper.cancall())
			{
			PyObject *arg = Py_BuildValue("(s)", msg);
			helper.call(arg);
			}
		}
	else
		MessageLog(msg);
    return PNR_OK;
}

void
ExampleErrorSink::ConvertErrorToString(const ULONG32 ulRMACode, char* pszBuffer)
{
    PN_RESULT theErr = (PN_RESULT) ulRMACode;
	geterrorstring(theErr, pszBuffer);
}

const char* ExampleErrorSink::ConvertErrorTypeToString(int type)
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

// IUnknown COM Interface Methods

/****************************************************************************
 *  IUnknown::AddRef                                            ref:  pncom.h
 *
 *  This routine increases the object reference count in a thread safe
 *  manner. The reference count is used to manage the lifetime of an object.
 *  This method must be explicitly called by the user whenever a new
 *  reference to an object is used.
 */
STDMETHODIMP_(ULONG32)
ExampleErrorSink::AddRef()
{
    return InterlockedIncrement(&m_lRefCount);
}


/****************************************************************************
 *  IUnknown::Release                                           ref:  pncom.h
 *
 *  This routine decreases the object reference count in a thread safe
 *  manner, and deletes the object if no more references to it exist. It must
 *  be called explicitly by the user whenever an object is no longer needed.
 */
STDMETHODIMP_(ULONG32)
ExampleErrorSink::Release()
{
    if (InterlockedDecrement(&m_lRefCount) > 0)
    {
        return m_lRefCount;
    }

    delete this;
    return 0;
}


/****************************************************************************
 *  IUnknown::QueryInterface                                    ref:  pncom.h
 *
 *  This routine indicates which interfaces this object supports. If a given
 *  interface is supported, the object's reference count is incremented, and
 *  a reference to that interface is returned. Otherwise a NULL object and
 *  error code are returned. This method is called by other objects to
 *  discover the functionality of this object.
 */
STDMETHODIMP
ExampleErrorSink::QueryInterface(REFIID riid, void** ppvObj)
{
    if (IsEqualIID(riid, IID_IUnknown))
    {
	AddRef();
	*ppvObj = (IUnknown*)(IRMAErrorSink*)this;
	return PNR_OK;
    }
    else if (IsEqualIID(riid, IID_IRMAErrorSink))
    {
	AddRef();
	*ppvObj = (IRMAErrorSink*) this;
	return PNR_OK;
    }

    *ppvObj = NULL;
    return PNR_NOINTERFACE;
}
