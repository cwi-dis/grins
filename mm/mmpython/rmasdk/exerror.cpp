/****************************************************************************
 * 
 *  $Id$
 *
 *  Copyright (C) 1995,1996,1997 RealNetworks, Inc.
 *  All rights reserved.
 *
 *  http://www.real.com/devzone
 *
 *  This program contains proprietary information of RealNetworks, Inc.,
 *  and is licensed subject to restrictions on use and distribution.
 * 
 *  exerror.cpp
 *
 *  Sample Implementation of IRMAErrorSink Interface
 *
 */


/****************************************************************************
 * Includes
 */
#include "pntypes.h"
#include "pncom.h"
#include "rmacomm.h"
#include "rmaerror.h"

#include "os.h"
#include "exerror.h"


/****************************************************************************
 *  ExampleErrorSink::ExampleErrorSink                        ref:  exerror.h
 *
 *  Constructor
 */
ExampleErrorSink::ExampleErrorSink() 
    :m_lRefCount(0)
{
}


/****************************************************************************
 *  ExampleErrorSink::~ExampleErrorSink                       ref:  exerror.h
 *
 *  Destructor
 */
ExampleErrorSink::~ExampleErrorSink()
{
}


// IRMAErrorSink Interface Methods

/****************************************************************************
 *  IRMAErrorSink::ErrorOccurred                             ref:  rmaerror.h
 *
 */
STDMETHODIMP 
ExampleErrorSink::ErrorOccurred(const UINT8	unSeverity,  
				const ULONG32	ulRMACode,
				const ULONG32	ulUserCode,
				const char*	pUserString,
				const char*	pMoreInfoURL
				)
{
    char RMADefine[256];

    ConvertErrorToString(ulRMACode, RMADefine);

    fprintf(stdout, "Report(%d, 0x%x, \"%s\", %ld, \"%s\", \"%s\")\n",
		    unSeverity,
		    ulRMACode,
		    (pUserString && *pUserString) ? pUserString : "(NULL)",
		    ulUserCode,
		    (pMoreInfoURL && *pMoreInfoURL) ? pMoreInfoURL : "(NULL)",
                    RMADefine);

    return PNR_OK;
}

void
ExampleErrorSink::ConvertErrorToString(const ULONG32 ulRMACode, char* pszBuffer)
{
    PN_RESULT theErr = (PN_RESULT) ulRMACode;

    switch (theErr)
    {
        case PNR_NOTIMPL:
            strcpy(pszBuffer, "PNR_NOTIMPL");
            break;
        case PNR_OUTOFMEMORY:
            strcpy(pszBuffer, "PNR_OUTOFMEMORY");
            break;
        case PNR_INVALID_PARAMETER: 
            strcpy(pszBuffer, "PNR_INVALID_PARAMETER");
            break;
        case PNR_NOINTERFACE:
            strcpy(pszBuffer, "PNR_NOINTERFACE");
            break;
        case PNR_POINTER:
            strcpy(pszBuffer, "PNR_POINTER");
            break;
        case PNR_HANDLE:
            strcpy(pszBuffer, "PNR_HANDLE");
            break;
        case PNR_ABORT:
            strcpy(pszBuffer, "PNR_ABORT");
            break;
        case PNR_FAIL:
            strcpy(pszBuffer, "PNR_FAIL");
            break;
        case PNR_ACCESSDENIED:
            strcpy(pszBuffer, "PNR_ACCESSDENIED");
            break;
        case PNR_OK:
            strcpy(pszBuffer, "PNR_OK");
            break;

        case PNR_INVALID_OPERATION:
            strcpy(pszBuffer, "PNR_INVALID_OPERATION");
            break;
        case PNR_INVALID_VERSION:
            strcpy(pszBuffer, "PNR_INVALID_VERSION");
            break;
        case PNR_INVALID_REVISION:
            strcpy(pszBuffer, "PNR_INVALID_REVISION");
            break;
        case PNR_NOT_INITIALIZED:
            strcpy(pszBuffer, "PNR_NOT_INITIALIZED");
            break;
        case PNR_DOC_MISSING:
            strcpy(pszBuffer, "PNR_DOC_MISSING");
            break;
        case PNR_UNEXPECTED:
            strcpy(pszBuffer, "PNR_UNEXPECTED");
            break;
        case PNR_NO_FILEFORMAT:
            strcpy(pszBuffer, "PNR_NO_FILEFORMAT");
            break;
        case PNR_NO_RENDERER:
            strcpy(pszBuffer, "PNR_NO_RENDERER");
            break;

        case PNR_BUFFERING:
            strcpy(pszBuffer, "PNR_BUFFERING");
            break;
        case PNR_PAUSED:
            strcpy(pszBuffer, "PNR_PAUSED");
            break;
        case PNR_NO_DATA:
            strcpy(pszBuffer, "PNR_NO_DATA");
            break;
        case PNR_STREAM_DONE:
            strcpy(pszBuffer, "PNR_STREAM_DONE");
            break;
        case PNR_NET_SOCKET_INVALID:
            strcpy(pszBuffer, "PNR_NET_SOCKET_INVALID");
            break;
        case PNR_NET_CONNECT:
            strcpy(pszBuffer, "PNR_NET_CONNECT");
            break;
        case PNR_BIND:
            strcpy(pszBuffer, "PNR_BIND");
            break;
        case PNR_SOCKET_CREATE:
            strcpy(pszBuffer, "PNR_SOCKET_CREATE");
            break;
        case PNR_INVALID_HOST:
            strcpy(pszBuffer, "PNR_INVALID_HOST");
            break;
        case PNR_NET_READ:
            strcpy(pszBuffer, "PNR_NET_READ");
            break;
        case PNR_NET_WRITE:
            strcpy(pszBuffer, "PNR_NET_WRITE");
            break;
        case PNR_NET_UDP:
            strcpy(pszBuffer, "PNR_NET_UDP");
            break;
        case PNR_RETRY:
            strcpy(pszBuffer, "PNR_RETRY");
            break;
        case PNR_SERVER_TIMEOUT:
            strcpy(pszBuffer, "PNR_SERVER_TIMEOUT");
            break;
        case PNR_SERVER_DISCONNECTED:
            strcpy(pszBuffer, "PNR_SERVER_DISCONNECTED");
            break;
        case PNR_WOULD_BLOCK:
            strcpy(pszBuffer, "PNR_WOULD_BLOCK");
            break;
        case PNR_GENERAL_NONET:
            strcpy(pszBuffer, "PNR_GENERAL_NONET");
            break;
        case PNR_BLOCK_CANCELED:
            strcpy(pszBuffer, "PNR_BLOCK_CANCELED");
            break;
        case PNR_MULTICAST_JOIN:
            strcpy(pszBuffer, "PNR_MULTICAST_JOIN");
            break;
        case PNR_GENERAL_MULTICAST:
            strcpy(pszBuffer, "PNR_GENERAL_MULTICAST");
            break;
        case PNR_MULTICAST_UDP:
            strcpy(pszBuffer, "PNR_MULTICAST_UDP");
            break;
        case PNR_AT_INTERRUPT:
            strcpy(pszBuffer, "PNR_AT_INTERRUPT");
            break;

        case PNR_AT_END:
            strcpy(pszBuffer, "PNR_AT_END");
            break;
        case PNR_INVALID_FILE:
            strcpy(pszBuffer, "PNR_INVALID_FILE");
            break;
        case PNR_INVALID_PATH:
            strcpy(pszBuffer, "PNR_INVALID_PATH");
            break;
        case PNR_RECORD:
            strcpy(pszBuffer, "PNR_RECORD");
            break;
        case PNR_RECORD_WRITE:
            strcpy(pszBuffer, "PNR_RECORD_WRITE");
            break;
        case PNR_TEMP_FILE:
            strcpy(pszBuffer, "PNR_TEMP_FILE");
            break;
        case PNR_ALREADY_OPEN:
            strcpy(pszBuffer, "PNR_ALREADY_OPEN");
            break;
        case PNR_SEEK_PENDING:
            strcpy(pszBuffer, "PNR_SEEK_PENDING");
            break;
        case PNR_CANCELLED:
            strcpy(pszBuffer, "PNR_CANCELLED");
            break;
        case PNR_FILE_NOT_FOUND:
            strcpy(pszBuffer, "PNR_FILE_NOT_FOUND");
            break;
        case PNR_WRITE_ERROR:
            strcpy(pszBuffer, "PNR_WRITE_ERROR");
            break;
        case PNR_FILE_EXISTS:
            strcpy(pszBuffer, "PNR_FILE_EXISTS");
            break;

        case PNR_BAD_SERVER:
            strcpy(pszBuffer, "PNR_BAD_SERVER");
            break;
        case PNR_ADVANCED_SERVER:
            strcpy(pszBuffer, "PNR_ADVANCED_SERVER");
            break;
        case PNR_OLD_SERVER:
            strcpy(pszBuffer, "PNR_OLD_SERVER");
            break;
        case PNR_REDIRECTION:
            strcpy(pszBuffer, "PNR_REDIRECTION");
            break;
        case PNR_SERVER_ALERT:
            strcpy(pszBuffer, "PNR_SERVER_ALERT");
            break;
        case PNR_PROXY:
            strcpy(pszBuffer, "PNR_PROXY");
            break;
        case PNR_PROXY_RESPONSE:
            strcpy(pszBuffer, "PNR_PROXY_RESPONSE");
            break;
        case PNR_ADVANCED_PROXY:
            strcpy(pszBuffer, "PNR_ADVANCED_PROXY");
            break;
        case PNR_OLD_PROXY:
            strcpy(pszBuffer, "PNR_OLD_PROXY");
            break;
        case PNR_INVALID_PROTOCOL:
            strcpy(pszBuffer, "PNR_INVALID_PROTOCOL");
            break;
        case PNR_INVALID_URL_OPTION:
            strcpy(pszBuffer, "PNR_INVALID_URL_OPTION");
            break;
        case PNR_INVALID_URL_HOST:
            strcpy(pszBuffer, "PNR_INVALID_URL_HOST");
            break;
        case PNR_INVALID_URL_PATH:
            strcpy(pszBuffer, "PNR_INVALID_URL_PATH");
            break;
        case PNR_HTTP_CONTENT_NOT_FOUND:
            strcpy(pszBuffer, "PNR_HTTP_CONTENT_NOT_FOUND");
            break;
        case PNR_NOT_AUTHORIZED:
            strcpy(pszBuffer, "PNR_NOT_AUTHORIZED");
            break;
        case PNR_UNEXPECTED_MSG:
            strcpy(pszBuffer, "PNR_UNEXPECTED_MSG");
            break;
        case PNR_BAD_TRANSPORT:
            strcpy(pszBuffer, "PNR_BAD_TRANSPORT");
            break;
        case PNR_NO_SESSION_ID:
            strcpy(pszBuffer, "PNR_NO_SESSION_ID");
            break;

        case PNR_AUDIO_DRIVER:
            strcpy(pszBuffer, "PNR_AUDIO_DRIVER");
            break;

        case PNR_OPEN_NOT_PROCESSED:
            strcpy(pszBuffer, "PNR_OPEN_NOT_PROCESSED");
            break;

        case PNR_EXPIRED:
            strcpy(pszBuffer, "PNR_EXPIRED");
            break;

        case PNR_INVALID_INTERLEAVER:
            strcpy(pszBuffer, "PNR_INVALID_INTERLEAVER");
            break;
        case PNR_BAD_FORMAT:
            strcpy(pszBuffer, "PNR_BAD_FORMAT");
            break;
        case PNR_CHUNK_MISSING:
            strcpy(pszBuffer, "PNR_CHUNK_MISSING");
            break;
        case PNR_INVALID_STREAM:
            strcpy(pszBuffer, "PNR_INVALID_STREAM");
            break;
        case PNR_DNR:
            strcpy(pszBuffer, "PNR_DNR");
            break;
        case PNR_OPEN_DRIVER:
            strcpy(pszBuffer, "PNR_OPEN_DRIVER");
            break;
        case PNR_UPGRADE:
            strcpy(pszBuffer, "PNR_UPGRADE");
            break;
        case PNR_NOTIFICATION:
            strcpy(pszBuffer, "PNR_NOTIFICATION");
            break;
        case PNR_NOT_NOTIFIED:
            strcpy(pszBuffer, "PNR_NOT_NOTIFIED");
            break;

        case PNR_STOPPED:
            strcpy(pszBuffer, "PNR_STOPPED");
            break;
        case PNR_CLOSED:
            strcpy(pszBuffer, "PNR_CLOSED");
            break;
        case PNR_INVALID_WAV_FILE:
            strcpy(pszBuffer, "PNR_INVALID_WAV_FILE");
            break;
        case PNR_NO_SEEK:
            strcpy(pszBuffer, "PNR_NO_SEEK");
            break;

        case PNR_DEC_INITED:
            strcpy(pszBuffer, "PNR_DEC_INITED");
            break;
        case PNR_DEC_NOT_FOUND:
            strcpy(pszBuffer, "PNR_DEC_NOT_FOUND");
            break;
        case PNR_DEC_INVALID:
            strcpy(pszBuffer, "PNR_DEC_INVALID");
            break;
        case PNR_DEC_TYPE_MISMATCH:
            strcpy(pszBuffer, "PNR_DEC_TYPE_MISMATCH");
            break;
        case PNR_DEC_INIT_FAILED:
            strcpy(pszBuffer, "PNR_DEC_INIT_FAILED");
            break;
        case PNR_DEC_NOT_INITED:
            strcpy(pszBuffer, "PNR_DEC_NOT_INITED");
            break;
        case PNR_DEC_DECOMPRESS:
            strcpy(pszBuffer, "PNR_DEC_DECOMPRESS");
            break;

        case PNR_ENC_FILE_TOO_SMALL:
            strcpy(pszBuffer, "PNR_ENC_FILE_TOO_SMALL");
            break;
        case PNR_ENC_UNKNOWN_FILE:
            strcpy(pszBuffer, "PNR_ENC_UNKNOWN_FILE");
            break;
        case PNR_ENC_BAD_CHANNELS:
            strcpy(pszBuffer, "PNR_ENC_BAD_CHANNELS");
            break;
        case PNR_ENC_BAD_SAMPSIZE:
            strcpy(pszBuffer, "PNR_ENC_BAD_SAMPSIZE");
            break;
        case PNR_ENC_BAD_SAMPRATE:
            strcpy(pszBuffer, "PNR_ENC_BAD_SAMPRATE");
            break;
        case PNR_ENC_INVALID:
            strcpy(pszBuffer, "PNR_ENC_INVALID");
            break;
        case PNR_ENC_NO_OUTPUT_FILE:
            strcpy(pszBuffer, "PNR_ENC_NO_OUTPUT_FILE");
            break;
        case PNR_ENC_NO_INPUT_FILE:
            strcpy(pszBuffer, "PNR_ENC_NO_INPUT_FILE");
            break;
        case PNR_ENC_NO_OUTPUT_PERMISSIONS:
            strcpy(pszBuffer, "PNR_ENC_NO_OUTPUT_PERMISSIONS");
            break;
        case PNR_ENC_BAD_FILETYPE:
            strcpy(pszBuffer, "PNR_ENC_BAD_FILETYPE");
            break;

        case PNR_ENC_INVALID_VIDEO:
            strcpy(pszBuffer, "PNR_ENC_INVALID_VIDEO");
            break;
        case PNR_ENC_INVALID_AUDIO:
            strcpy(pszBuffer, "PNR_ENC_INVALID_AUDIO");
            break;
        case PNR_ENC_NO_VIDEO_CAPTURE:
            strcpy(pszBuffer, "PNR_ENC_NO_VIDEO_CAPTURE");
            break;
        case PNR_ENC_INVALID_VIDEO_CAPTURE:
            strcpy(pszBuffer, "PNR_ENC_INVALID_VIDEO_CAPTURE");
            break;
        case PNR_ENC_NO_AUDIO_CAPTURE:
            strcpy(pszBuffer, "PNR_ENC_NO_AUDIO_CAPTURE");
            break;
        case PNR_ENC_INVALID_AUDIO_CAPTURE:
            strcpy(pszBuffer, "PNR_ENC_INVALID_AUDIO_CAPTURE");
            break;
        case PNR_ENC_TOO_SLOW_FOR_LIVE:
            strcpy(pszBuffer, "PNR_ENC_TOO_SLOW_FOR_LIVE");
            break;
        case PNR_ENC_ENGINE_NOT_INITIALIZED:
            strcpy(pszBuffer, "PNR_ENC_ENGINE_NOT_INITIALIZED");
            break;
        case PNR_ENC_CODEC_NOT_FOUND:
            strcpy(pszBuffer, "PNR_ENC_CODEC_NOT_FOUND");
            break;
        case PNR_ENC_CODEC_NOT_INITIALIZED:
            strcpy(pszBuffer, "PNR_ENC_CODEC_NOT_INITIALIZED");
            break;
        case PNR_ENC_INVALID_INPUT_DIMENSIONS:
            strcpy(pszBuffer, "PNR_ENC_INVALID_INPUT_DIMENSIONS");
            break;

        case PNR_PROP_NOT_FOUND:
            strcpy(pszBuffer, "PNR_PROP_NOT_FOUND");
            break;
        case PNR_PROP_NOT_COMPOSITE:
            strcpy(pszBuffer, "PNR_PROP_NOT_COMPOSITE");
            break;
        case PNR_PROP_DUPLICATE:
            strcpy(pszBuffer, "PNR_PROP_DUPLICATE");
            break;
        case PNR_PROP_TYPE_MISMATCH:
            strcpy(pszBuffer, "PNR_PROP_TYPE_MISMATCH");
            break;

        case PNR_COULDNOTINITCORE:
            strcpy(pszBuffer, "PNR_COULDNOTINITCORE");
            break;
        case PNR_PERFECTPLAY_NOT_SUPPORTED:
            strcpy(pszBuffer, "PNR_PERFECTPLAY_NOT_SUPPORTED");
            break;
        case PNR_NO_LIVE_PERFECTPLAY:
            strcpy(pszBuffer, "PNR_NO_LIVE_PERFECTPLAY");
            break;
        case PNR_PERFECTPLAY_NOT_ALLOWED:
            strcpy(pszBuffer, "PNR_PERFECTPLAY_NOT_ALLOWED");
            break;
        case PNR_NO_CODECS:
            strcpy(pszBuffer, "PNR_NO_CODECS");
            break;
        case PNR_SLOW_MACHINE:
            strcpy(pszBuffer, "PNR_SLOW_MACHINE");
            break;
        case PNR_FORCE_PERFECTPLAY:
            strcpy(pszBuffer, "PNR_FORCE_PERFECTPLAY");
            break;
        case PNR_INVALID_HTTP_PROXY_HOST:
            strcpy(pszBuffer, "PNR_INVALID_HTTP_PROXY_HOST");
            break;
        case PNR_INVALID_METAFILE:
            strcpy(pszBuffer, "PNR_INVALID_METAFILE");
            break;

        default:
            strcpy(pszBuffer, "Unknown");
            break;
    }
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
