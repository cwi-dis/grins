/****************************************************************************
 * 
 *  $Id$

/****************************************************************************
 * Includes
 */
#include "pntypes.h"
#include "pncom.h"
#include "rmacomm.h"
#include "rmamon.h"
#include "rmacore.h"

#include "os.h"
#include "rmaclsnk.h"
#include "exadvsnk.h"

#include "std.h"
#include "PyCppApi.h"


/****************************************************************************
 * Globals
 */
BOOL bShowMeTheStatistics=FALSE;


/****************************************************************************
 *  ExampleClientAdviceSink::ExampleClientAdviceSink         ref:  exadvsnk.h
 *
 *  Constructor
 */
ExampleClientAdviceSink::ExampleClientAdviceSink(IUnknown* pUnknown)
    : m_lRefCount (0)
    , m_pUnknown (NULL)
    , m_pRegistry (NULL)
	, m_pyAdviceSink(NULL)
	{
    if (pUnknown)
		{
		m_pUnknown = pUnknown;
		m_pUnknown->AddRef();

		if (PNR_OK != m_pUnknown->QueryInterface(IID_IRMAPNRegistry, (void**)&m_pRegistry))
			m_pRegistry = NULL;

		IRMAPlayer* pPlayer;
		if(PNR_OK == m_pUnknown->QueryInterface(IID_IRMAPlayer,
						(void**)&pPlayer))
			{
			pPlayer->AddAdviseSink(this);
			pPlayer->Release();
			}
		}
	}


/****************************************************************************
 *  ExampleClientAdviceSink::~ExampleClientAdviceSink        ref:  exadvsnk.h
 *
 *  Destructor
 */
ExampleClientAdviceSink::~ExampleClientAdviceSink(void)
	{
	Py_XDECREF(m_pyAdviceSink);
	m_pyAdviceSink=NULL;

    if (m_pRegistry)
		{
		m_pRegistry->Release();
		m_pRegistry = NULL;
		}

    if (m_pUnknown)
		{
		m_pUnknown->Release();
		m_pUnknown = NULL;
		}
	}

void ExampleClientAdviceSink::SetPyAdviceSink(PyObject *obj)
	{
	Py_XDECREF(m_pyAdviceSink);
	if(obj==Py_None)m_pyAdviceSink=NULL;
	else m_pyAdviceSink=obj;
	Py_XINCREF(m_pyAdviceSink);
	}
PyObject* ExampleClientAdviceSink::GetPyAdviceSink()
	{
	return m_pyAdviceSink;
	}

/****************************************************************************
 *  ExampleClientAdviceSink::ShowMeTheStatistics             ref:  exadvsnk.h
 *
 */
void ExampleClientAdviceSink::ShowMeTheStatistics (char* pszRegistryKey)
{
    char    szRegistryValue[MAX_DISPLAY_NAME] = {0};
    INT32   lValue = 0;
    INT32   i = 0;
    INT32   lStatistics = 8;
    
    if (!bShowMeTheStatistics)
    {
	return;
    }

    // collect statistic
    for (i = 0; i < lStatistics; i++)
    {
	switch (i)
	{
	case 0:
	    sprintf(szRegistryValue, "%s.Normal", pszRegistryKey);
	    break;
	case 1:
	    sprintf(szRegistryValue, "%s.Recovered", pszRegistryKey);
	    break;
	case 2:
	    sprintf(szRegistryValue, "%s.Received", pszRegistryKey);
	    break;
	case 3:
	    sprintf(szRegistryValue, "%s.Lost", pszRegistryKey);
	    break;
	case 4:
	    sprintf(szRegistryValue, "%s.Late", pszRegistryKey);
	    break;
	case 5:
	    sprintf(szRegistryValue, "%s.ClipBandwidth", pszRegistryKey);
	    break;
	case 6:
	    sprintf(szRegistryValue, "%s.AverageBandwidth", pszRegistryKey);
	    break;
	case 7:
	    sprintf(szRegistryValue, "%s.CurrentBandwidth", pszRegistryKey);
	    break;
	default:
	    break;
	}

	m_pRegistry->GetIntByName(szRegistryValue, lValue);
	fprintf(stdout, "%s = %ld\n", szRegistryValue, lValue);
    }
}


// IRMAClientAdviseSink Interface Methods

/****************************************************************************
 *  IRMAClientAdviseSink::OnPosLength                        ref:  rmaclsnk.h
 *
 *  Called to advise the client that the position or length of the
 *  current playback context has changed.
 */
STDMETHODIMP
ExampleClientAdviceSink::OnPosLength(UINT32	  ulPosition,
				   UINT32	  ulLength)
	{
    //fprintf(stdout, "OnPosLength(%ld, %ld)\n", ulPosition, ulLength);  
	if(m_pyAdviceSink)
		{
		CallerHelper helper("OnPosLength",m_pyAdviceSink);
		if(helper.HaveHandler())helper.call(ulPosition,ulLength);
		}
    return PNR_OK;
	}


/****************************************************************************
 *  IRMAClientAdviseSink::OnPresentationOpened               ref:  rmaclsnk.h
 *
 *  Called to advise the client a presentation has been opened.
 */
STDMETHODIMP
ExampleClientAdviceSink::OnPresentationOpened()
{
    //fprintf(stdout, "OnPresentationOpened()\n");
	if(m_pyAdviceSink)
		{
		CallerHelper helper("OnPresentationOpened",m_pyAdviceSink);
		if(helper.HaveHandler())helper.call();
		}
    return PNR_OK;
}


/****************************************************************************
 *  IRMAClientAdviseSink::OnPresentationClosed               ref:  rmaclsnk.h
 *
 *  Called to advise the client a presentation has been closed.
 */
STDMETHODIMP
ExampleClientAdviceSink::OnPresentationClosed()
	{
    //fprintf(stdout, "OnPresentationClosed()\n");
	if(m_pyAdviceSink)
		{
		CallerHelper helper("OnPresentationClosed",m_pyAdviceSink);
		if(helper.HaveHandler())helper.call();
		}
    return PNR_OK;
	}


/****************************************************************************
 *  IRMAClientAdviseSink::OnStatisticsChanged                ref:  rmaclsnk.h
 *
 *  Called to advise the client that the presentation statistics
 *  have changed. 
 */
STDMETHODIMP
ExampleClientAdviceSink::OnStatisticsChanged(void)
{
    fprintf(stdout, "OnStatisticsChanged():\n");

    UINT32  unPlayerIndex = 0;
    UINT32  unSourceIndex = 0;
    UINT32  unStreamIndex = 0;

    INT32   nRegistryValue = 0;

    char*   pszRegistryPrefix = "Statistics";
    char    szRegistryName[MAX_DISPLAY_NAME] = {0};
   
    // display the content of whole statistic registry
    if (m_pRegistry)
    {
	// ok, let's start from the top (player)
	sprintf(szRegistryName, "%s.Player%ld", pszRegistryPrefix, unPlayerIndex);
	while (PT_COMPOSITE == m_pRegistry->GetTypeByName(szRegistryName))
	{
	    // display player statistic
	    ShowMeTheStatistics(szRegistryName);

	    sprintf(szRegistryName, "%s.Source%ld", szRegistryName, unSourceIndex);
	    while (PT_COMPOSITE == m_pRegistry->GetTypeByName(szRegistryName))
	    {
		// display source statistic
		ShowMeTheStatistics(szRegistryName);

		sprintf(szRegistryName, "%s.Stream%ld", szRegistryName, unStreamIndex);
		while (PT_COMPOSITE == m_pRegistry->GetTypeByName(szRegistryName))
		{
		    // display stream statistic
		    ShowMeTheStatistics(szRegistryName);

		    unStreamIndex++;

		    sprintf(szRegistryName, "%s.Player%ld.Source%ld.Stream%ld", 
			    pszRegistryPrefix, unPlayerIndex, unSourceIndex, unStreamIndex);
		}

		unSourceIndex++;

		sprintf(szRegistryName, "%s.Player%ld.Source%ld",
			pszRegistryPrefix, unPlayerIndex, unSourceIndex);
	    }

	    unPlayerIndex++;

	    sprintf(szRegistryName, "%s.Player%ld", pszRegistryPrefix, unPlayerIndex);
	}
    }

    return PNR_OK;
}


/****************************************************************************
 *  IRMAClientAdviseSink::OnPreSeek                          ref:  rmaclsnk.h
 *
 *  Called by client engine to inform the client that a seek is
 *  about to occur. The render is informed the last time for the 
 *  stream's time line before the seek, as well as the first new
 *  time for the stream's time line after the seek will be completed.
 */
STDMETHODIMP
ExampleClientAdviceSink::OnPreSeek(	UINT32	ulOldTime,
						UINT32	ulNewTime)
	{
	//fprintf(stdout, "OnPreSeek(%ld, %ld)\n", ulOldTime, ulNewTime);
	if(m_pyAdviceSink)
		{
		CallerHelper helper("OnPreSeek",m_pyAdviceSink);
		if(helper.HaveHandler())helper.call(ulOldTime,ulNewTime);
		}
    return PNR_OK;
	}


/****************************************************************************
 *  IRMAClientAdviseSink::OnPostSeek                         ref:  rmaclsnk.h
 *
 *  Called by client engine to inform the client that a seek has
 *  just occured. The render is informed the last time for the 
 *  stream's time line before the seek, as well as the first new
 *  time for the stream's time line after the seek.
 */
STDMETHODIMP
ExampleClientAdviceSink::OnPostSeek(	UINT32	ulOldTime,
						UINT32	ulNewTime)
	{
    //fprintf(stdout, "OnPostSeek(%ld, %ld)\n", ulOldTime, ulNewTime);
 	if(m_pyAdviceSink)
		{
		CallerHelper helper("OnPostSeek",m_pyAdviceSink);
		if(helper.HaveHandler())helper.call(ulOldTime,ulNewTime);
		}
   return PNR_OK;
	}


/****************************************************************************
 *  IRMAClientAdviseSink::OnStop                             ref:  rmaclsnk.h
 *
 *  Called by client engine to inform the client that a stop has
 *  just occured. 
 */
STDMETHODIMP
ExampleClientAdviceSink::OnStop(void)
	{
    //fprintf(stdout, "OnStop()\n");
	if(m_pyAdviceSink)
		{
		CallerHelper helper("OnStop",m_pyAdviceSink);
		if(helper.HaveHandler())helper.call();
		}
    return PNR_OK;
	}


/****************************************************************************
 *  IRMAClientAdviseSink::OnPause                            ref:  rmaclsnk.h
 *
 *  Called by client engine to inform the client that a pause has
 *  just occured. The render is informed the last time for the 
 *  stream's time line before the pause.
 */
STDMETHODIMP
ExampleClientAdviceSink::OnPause(UINT32 ulTime)
	{
    //fprintf(stdout, "OnPause(%ld)\n", ulTime);
	if(m_pyAdviceSink)
		{
		CallerHelper helper("OnPause",m_pyAdviceSink);
		if(helper.HaveHandler())helper.call((int)ulTime);
		}
    return PNR_OK;
	}


/****************************************************************************
 *  IRMAClientAdviseSink::OnBegin                            ref:  rmaclsnk.h
 *
 *  Called by client engine to inform the client that a begin or
 *  resume has just occured. The render is informed the first time 
 *  for the stream's time line after the resume.
 */
STDMETHODIMP
ExampleClientAdviceSink::OnBegin(UINT32 ulTime)
	{
    //fprintf(stdout, "OnBegin(%ld)\n", ulTime);
	if(m_pyAdviceSink)
		{
		CallerHelper helper("OnBegin",m_pyAdviceSink);
		if(helper.HaveHandler())helper.call((int)ulTime);
		}
    return PNR_OK;
	}


/****************************************************************************
 *  IRMAClientAdviseSink::OnBuffering                        ref:  rmaclsnk.h
 *
 *  Called by client engine to inform the client that buffering
 *  of data is occuring. The render is informed of the reason for
 *  the buffering (start-up of stream, seek has occured, network
 *  congestion, etc.), as well as percentage complete of the 
 *  buffering process.
 */
STDMETHODIMP
ExampleClientAdviceSink::OnBuffering
(
    UINT32 ulFlags,
    UINT16 unPercentComplete
)
	{
    //fprintf(stdout, "OnBuffering(%ld, %d)\n", ulFlags, unPercentComplete);
	if(m_pyAdviceSink)
		{
		CallerHelper helper("OnBuffering",m_pyAdviceSink);
		if(helper.HaveHandler())helper.call(ulFlags,unPercentComplete);
		}
    return PNR_OK;
	}


/****************************************************************************
 *  IRMAClientAdviseSink::OnContacting                       ref:  rmaclsnk.h
 *
 *  Called by client engine to inform the client is contacting hosts(s).
 */
STDMETHODIMP
ExampleClientAdviceSink::OnContacting(const char* pHostName)
	{
    //fprintf(stdout, "OnContacting(\"%s\")\n", pHostName);
	if(m_pyAdviceSink)
		{
		CallerHelper helper("OnContacting",m_pyAdviceSink);
		if(helper.HaveHandler())helper.call(pHostName);
		}
    return PNR_OK;
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
STDMETHODIMP_(UINT32) ExampleClientAdviceSink::AddRef()
{
	Py_XINCREF(m_pyAdviceSink);
    return InterlockedIncrement(&m_lRefCount);
}


/****************************************************************************
 *  IUnknown::Release                                           ref:  pncom.h
 *
 *  This routine decreases the object reference count in a thread safe
 *  manner, and deletes the object if no more references to it exist. It must
 *  be called explicitly by the user whenever an object is no longer needed.
 */
STDMETHODIMP_(UINT32) ExampleClientAdviceSink::Release()
{
	if(m_pyAdviceSink && m_pyAdviceSink->ob_refcnt==1)
		{
		Py_XDECREF(m_pyAdviceSink);
		m_pyAdviceSink=NULL;
		}
	else Py_XDECREF(m_pyAdviceSink);
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
STDMETHODIMP ExampleClientAdviceSink::QueryInterface(REFIID riid, void** ppvObj)
{
    if (IsEqualIID(riid, IID_IUnknown))
    {
	AddRef();
	*ppvObj = (IUnknown*)(IRMAClientAdviseSink*)this;
	return PNR_OK;
    }
    else if (IsEqualIID(riid, IID_IRMAClientAdviseSink))
    {
	AddRef();
	*ppvObj = (IRMAClientAdviseSink*)this;
	return PNR_OK;
    }

    *ppvObj = NULL;
    return PNR_NOINTERFACE;
}
