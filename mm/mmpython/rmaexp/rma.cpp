
/***********************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

#include "Python.h"

#include "pntypes.h" 

#if defined(_ABIO32) && _ABIO32 != 0
typedef int bool;
enum { false, true, };
#endif


#include "pncom.h"
#include "pnresult.h"

#include "rmacore.h"

#define INITGUID
#include "pnwintyp.h"
#include "rmawin.h"
#include "rmaerror.h"
#include "rmaclsnk.h"
#include "rmaauth.h"

// our client context interfaces
#include "rmapyclient.h"

/////////////////////

static PyObject *ErrorObject;

void seterror(const char *msg){PyErr_SetString(ErrorObject, msg);}

#define RELEASE(x) if(x) x->Release();x=NULL;

/////////////////////

struct errors {
	PN_RESULT error;
	char *name;
} errorlist [] = {
	{ PNR_NOTIMPL              ,"NOTIMPL ", },     
	{ PNR_OUTOFMEMORY		,"OUTOFMEMORY", }, 		
	{ PNR_INVALID_PARAMETER	,"INVALID_PARAMETER", }, 	
	{ PNR_NOINTERFACE          ,"NOINTERFACE", },           
	{ PNR_POINTER              ,"POINTER", },               
	{ PNR_HANDLE               ,"HANDLE", },                
	{ PNR_ABORT                ,"ABORT", },                 
	{ PNR_FAIL                 ,"FAIL", },                  
	{ PNR_ACCESSDENIED         ,"ACCESSDENIED", },          
	{ PNR_IGNORE			,"IGNORE", }, 			
	{ PNR_OK				,"OK", }, 				

	{ PNR_INVALID_OPERATION	,"INVALID_OPERATION", }, 	
	{ PNR_INVALID_VERSION	,"INVALID_VERSION", }, 	
	{ PNR_INVALID_REVISION	,"INVALID_REVISION", }, 	
	{ PNR_NOT_INITIALIZED	,"NOT_INITIALIZED", }, 	
	{ PNR_DOC_MISSING		,"DOC_MISSING", }, 		
	{ PNR_UNEXPECTED         ,"UNEXPECTED", },            
	{ PNR_INCOMPLETE		,"INCOMPLETE", }, 		
	{ PNR_BUFFERTOOSMALL	,"BUFFERTOOSMALL", }, 	
	{ PNR_UNSUPPORTED_VIDEO	,"UNSUPPORTED_VIDEO", }, 	
	{ PNR_UNSUPPORTED_AUDIO	,"UNSUPPORTED_AUDIO", }, 	
	{ PNR_INVALID_BANDWIDTH	,"INVALID_BANDWIDTH", }, 	
	{ PNR_NO_FILEFORMAT		,"NO_FILEFORMAT", }, 		
	{ PNR_NO_RENDERER		,"NO_RENDERER", }, 		
	{ PNR_NO_RENDERER		,"NO_RENDERER", }, 		
	{ PNR_NO_FILEFORMAT		,"NO_FILEFORMAT", }, 		
	{ PNR_MISSING_COMPONENTS,"MISSING_COMPONENTS", }, 
	{ PNR_ELEMENT_NOT_FOUND	,"ELEMENT_NOT_FOUND", }, 	
	{ PNR_NOCLASS			,"NOCLASS", }, 			
	{ PNR_CLASS_NOAGGREGATION,"CLASS_NOAGGREGATION", }, 
	{ PNR_NOT_LICENSED		,"NOT_LICENSED", }, 		
	{ PNR_NO_FILESYSTEM		,"NO_FILESYSTEM", }, 		

	{ PNR_BUFFERING			,"BUFFERING", }, 			
	{ PNR_PAUSED			,"PAUSED", }, 		
	{ PNR_NO_DATA			,"NO_DATA", },			
	{ PNR_STREAM_DONE		,"STREAM_DONE", },		
	{ PNR_NET_SOCKET_INVALID,"NET_SOCKET_INVALID", },
	{ PNR_NET_CONNECT		,"NET_CONNECT", },		
	{ PNR_BIND				,"BIND", },				
	{ PNR_SOCKET_CREATE		,"SOCKET_CREATE", },		
	{ PNR_INVALID_HOST		,"INVALID_HOST", },		
	{ PNR_NET_READ			,"NET_READ", },			
	{ PNR_NET_WRITE			,"NET_WRITE", },			
	{ PNR_NET_UDP			,"NET_UDP", },			
	{ PNR_RETRY				,"RETRY", },				
	{ PNR_SERVER_TIMEOUT	,"SERVER_TIMEOUT", },	
	{ PNR_SERVER_DISCONNECTED,"SERVER_DISCONNECTED", },
	{ PNR_WOULD_BLOCK		,"WOULD_BLOCK", },		
	{ PNR_GENERAL_NONET		,"GENERAL_NONET", },		
	{ PNR_BLOCK_CANCELED	,"BLOCK_CANCELED", },	
	{ PNR_MULTICAST_JOIN	,"MULTICAST_JOIN", },	
	{ PNR_GENERAL_MULTICAST	,"GENERAL_MULTICAST", },	
	{ PNR_MULTICAST_UDP		,"MULTICAST_UDP", },		
	{ PNR_AT_INTERRUPT      ,"AT_INTERRUPT", },         
	{ PNR_MSG_TOOLARGE		,"MSG_TOOLARGE", },		
	{ PNR_NET_TCP			,"NET_TCP", },			
	{ PNR_TRY_AUTOCONFIG	,"TRY_AUTOCONFIG", },	
	{ PNR_NOTENOUGH_BANDWIDTH,"NOTENOUGH_BANDWIDTH", },
	{ PNR_HTTP_CONNECT		,"HTTP_CONNECT", },		
	{ PNR_PORT_IN_USE		,"PORT_IN_USE", },		

	{ PNR_AT_END			,"AT_END", },			
	{ PNR_INVALID_FILE		,"INVALID_FILE", },		
	{ PNR_INVALID_PATH		,"INVALID_PATH", },		
	{ PNR_RECORD			,"RECORD", },			
	{ PNR_RECORD_WRITE		,"RECORD_WRITE", },		
	{ PNR_TEMP_FILE			,"TEMP_FILE", },			
	{ PNR_ALREADY_OPEN         ,"ALREADY_OPEN", },         
	{ PNR_SEEK_PENDING         ,"SEEK_PENDING", },         
	{ PNR_CANCELLED            ,"CANCELLED", },            
	{ PNR_FILE_NOT_FOUND       ,"FILE_NOT_FOUND", },       
	{ PNR_WRITE_ERROR          ,"WRITE_ERROR", },          
	{ PNR_FILE_EXISTS          ,"FILE_EXISTS", },          
	{ PNR_FILE_NOT_OPEN	,"FILE_NOT_OPEN", },	
	{ PNR_ADVISE_PREFER_LINEAR,"ADVISE_PREFER_LINEAR", },		
	{ PNR_PARSE_ERROR		,"PARSE_ERROR", },		
													
	{ PNR_BAD_SERVER		,"BAD_SERVER", },		
	{ PNR_ADVANCED_SERVER	,"ADVANCED_SERVER", },	
	{ PNR_OLD_SERVER		,"OLD_SERVER", },		
	{ PNR_REDIRECTION		,"REDIRECTION", },		
	{ PNR_SERVER_ALERT		,"SERVER_ALERT", },						
	{ PNR_PROXY				,"PROXY", },								
	{ PNR_PROXY_RESPONSE	,"PROXY_RESPONSE", },					
	{ PNR_ADVANCED_PROXY	,"ADVANCED_PROXY", },					
	{ PNR_OLD_PROXY			,"OLD_PROXY", },							
	{ PNR_INVALID_PROTOCOL	,"INVALID_PROTOCOL", },					
	{ PNR_INVALID_URL_OPTION,"INVALID_URL_OPTION", },			
	{ PNR_INVALID_URL_HOST	,"INVALID_URL_HOST", },					
	{ PNR_INVALID_URL_PATH	,"INVALID_URL_PATH", },					
	{ PNR_HTTP_CONTENT_NOT_FOUND,"HTTP_CONTENT_NOT_FOUND", },     
	{ PNR_NOT_AUTHORIZED       ,"NOT_AUTHORIZED", },                 
	{ PNR_UNEXPECTED_MSG       ,"UNEXPECTED_MSG", },                 
	{ PNR_BAD_TRANSPORT        ,"BAD_TRANSPORT", },                  
	{ PNR_NO_SESSION_ID        ,"NO_SESSION_ID", },                  
	{ PNR_PROXY_DNR			,"PROXY_DNR", },							
	{ PNR_PROXY_NET_CONNECT	,"PROXY_NET_CONNECT", },					

	{ PNR_AUDIO_DRIVER		,"AUDIO_DRIVER", },						
	{ PNR_LATE_PACKET		,"LATE_PACKET", },						
	{ PNR_OVERLAPPED_PACKET	,"OVERLAPPED_PACKET", },					
	{ PNR_OUTOFORDER_PACKET	,"OUTOFORDER_PACKET", },					
	{ PNR_NONCONTIGUOUS_PACKET,"NONCONTIGUOUS_PACKET", },				

	{ PNR_OPEN_NOT_PROCESSED,"OPEN_NOT_PROCESSED", },				

	{ PNR_EXPIRED			,"EXPIRED", },					

	{ PNR_INVALID_INTERLEAVER,"INVALID_INTERLEAVER", },
	{ PNR_BAD_FORMAT		,"BAD_FORMAT", },			
	{ PNR_CHUNK_MISSING		,"CHUNK_MISSING", },				
	{ PNR_INVALID_STREAM       ,"INVALID_STREAM", },         
	{ PNR_DNR                  ,"DNR", },                    
	{ PNR_OPEN_DRIVER          ,"OPEN_DRIVER", },            
	{ PNR_UPGRADE              ,"UPGRADE", },                
	{ PNR_NOTIFICATION         ,"NOTIFICATION", },           
	{ PNR_NOT_NOTIFIED         ,"NOT_NOTIFIED", },           
	{ PNR_STOPPED              ,"STOPPED", },                
	{ PNR_CLOSED               ,"CLOSED", },                 
	{ PNR_INVALID_WAV_FILE     ,"INVALID_WAV_FILE", },       
	{ PNR_NO_SEEK              ,"NO_SEEK", },                

	{ PNR_DEC_INITED		,"DEC_INITED", },				
	{ PNR_DEC_NOT_FOUND		,"DEC_NOT_FOUND", },				
	{ PNR_DEC_INVALID		,"DEC_INVALID", },				
	{ PNR_DEC_TYPE_MISMATCH	,"DEC_TYPE_MISMATCH", },			
	{ PNR_DEC_INIT_FAILED	,"DEC_INIT_FAILED", },			
	{ PNR_DEC_NOT_INITED	,"DEC_NOT_INITED", },			
	{ PNR_DEC_DECOMPRESS	,"DEC_DECOMPRESS", },			
	{ PNR_OBSOLETE_VERSION	,"OBSOLETE_VERSION", },			

	{ PNR_ENC_FILE_TOO_SMALL,"ENC_FILE_TOO_SMALL", },
	{ PNR_ENC_UNKNOWN_FILE	,"ENC_UNKNOWN_FILE", },			
	{ PNR_ENC_BAD_CHANNELS	,"ENC_BAD_CHANNELS", },			
	{ PNR_ENC_BAD_SAMPSIZE	,"ENC_BAD_SAMPSIZE", },			
	{ PNR_ENC_BAD_SAMPRATE	,"ENC_BAD_SAMPRATE", },			
	{ PNR_ENC_INVALID		,"ENC_INVALID", },				
	{ PNR_ENC_NO_OUTPUT_FILE,"ENC_NO_OUTPUT_FILE", },		
	{ PNR_ENC_NO_INPUT_FILE	,"ENC_NO_INPUT_FILE", },			
	{ PNR_ENC_NO_OUTPUT_PERMISSIONS,"ENC_NO_OUTPUT_PERMISSIONS", },	
	{ PNR_ENC_BAD_FILETYPE	,"ENC_BAD_FILETYPE", },			
	{ PNR_ENC_INVALID_VIDEO	,"ENC_INVALID_VIDEO", },			
	{ PNR_ENC_INVALID_AUDIO	,"ENC_INVALID_AUDIO", },			
	{ PNR_ENC_NO_VIDEO_CAPTURE,"ENC_NO_VIDEO_CAPTURE", },		
	{ PNR_ENC_INVALID_VIDEO_CAPTURE,"ENC_INVALID_VIDEO_CAPTURE", },		
	{ PNR_ENC_NO_AUDIO_CAPTURE,"ENC_NO_AUDIO_CAPTURE", },					
	{ PNR_ENC_INVALID_AUDIO_CAPTURE,"ENC_INVALID_AUDIO_CAPTURE", },		
	{ PNR_ENC_TOO_SLOW_FOR_LIVE,"ENC_TOO_SLOW_FOR_LIVE", },					
	{ PNR_ENC_ENGINE_NOT_INITIALIZED,"ENC_ENGINE_NOT_INITIALIZED", },	
	{ PNR_ENC_CODEC_NOT_FOUND,"ENC_CODEC_NOT_FOUND", },					
	{ PNR_ENC_CODEC_NOT_INITIALIZED,"ENC_CODEC_NOT_INITIALIZED", },		
	{ PNR_ENC_INVALID_INPUT_DIMENSIONS,"ENC_INVALID_INPUT_DIMENSIONS", },
	{ PNR_ENC_MESSAGE_IGNORED,"ENC_MESSAGE_IGNORED", },					
	{ PNR_ENC_NO_SETTINGS	,"ENC_NO_SETTINGS", },						
	{ PNR_ENC_NO_OUTPUT_TYPES,"ENC_NO_OUTPUT_TYPES", },					
	{ PNR_ENC_IMPROPER_STATE,"ENC_IMPROPER_STATE", },					
	{ PNR_ENC_INVALID_SERVER,"ENC_INVALID_SERVER", },					
	{ PNR_ENC_INVALID_TEMP_PATH,"ENC_INVALID_TEMP_PATH", },		
	{ PNR_ENC_MERGE_FAIL	,"ENC_MERGE_FAIL", },			
	{ PNR_BIN_DATA_NOT_FOUND,"BIN_DATA_NOT_FOUND", },	    	    
	{ PNR_BIN_END_OF_DATA	,"BIN_END_OF_DATA", },			
	{ PNR_BIN_DATA_PURGED	,"BIN_DATA_PURGED", },			
	{ PNR_BIN_FULL			,"BIN_FULL", },			
	{ PNR_BIN_OFFSET_PAST_END,"BIN_OFFSET_PAST_END", },					   
	{ PNR_ENC_NO_ENCODED_DATA,"ENC_NO_ENCODED_DATA", },					
	{ PNR_ENC_INVALID_DLL	,"ENC_INVALID_DLL", },						
	{ PNR_NOT_INDEXABLE		,"NOT_INDEXABLE", },							
	{ PNR_ENC_NO_BROWSER	,"ENC_NO_BROWSER", },						
	{ PNR_ENC_NO_FILE_TO_SERVER,"ENC_NO_FILE_TO_SERVER", },					
	{ PNR_ENC_INSUFFICIENT_DISK_SPACE,"ENC_INSUFFICIENT_DISK_SPACE_SPACE", },

	{ PNR_RMT_USAGE_ERROR	,"RMT_USAGE_ERROR", },					
	{ PNR_RMT_INVALID_ENDTIME,"RMT_INVALID_ENDTIME", },				
	{ PNR_RMT_MISSING_INPUT_FILE,"RMT_MISSING_INPUT_FILE", },	
	{ PNR_RMT_MISSING_OUTPUT_FILE,"RMT_MISSING_OUTPUT_FILE", },	
	{ PNR_RMT_INPUT_EQUALS_OUTPUT_FILE,"RMT_INPUT_EQUALS_OUTPUT_FILE", },	
	{ PNR_RMT_UNSUPPORTED_AUDIO_VERSION,"RMT_UNSUPPORTED_AUDIO_VERSIO_VERSION", },	
	{ PNR_RMT_DIFFERENT_AUDIO,"RMT_DIFFERENT_AUDIO", },					
	{ PNR_RMT_DIFFERENT_VIDEO,"RMT_DIFFERENT_VIDEO", },					
	{ PNR_RMT_PASTE_MISSING_STREAM,"RMT_PASTE_MISSING_STREAM", },	
	{ PNR_RMT_END_OF_STREAM	,"RMT_END_OF_STREAM", },					
	{ PNR_RMT_IMAGE_MAP_PARSE_ERROR,"RMT_IMAGE_MAP_PARSE_ERROR", },	
	{ PNR_RMT_INVALID_IMAGEMAP_FILE,"RMT_INVALID_IMAGEMAP_FILE", },	
	{ PNR_RMT_EVENT_PARSE_ERROR,"RMT_EVENT_PARSE_ERROR", },				
	{ PNR_RMT_INVALID_EVENT_FILE,"RMT_INVALID_EVENT_FILE", },	
	{ PNR_RMT_INVALID_OUTPUT_FILE,"RMT_INVALID_OUTPUT_FILE", },
	{ PNR_RMT_INVALID_DURATION,"RMT_INVALID_DURATION", },				
	{ PNR_RMT_NO_DUMP_FILES	,"RMT_NO_DUMP_FILES", },					
	{ PNR_RMT_NO_EVENT_DUMP_FILE,"RMT_NO_EVENT_DUMP_FILE", },	
	{ PNR_RMT_NO_IMAP_DUMP_FILE,"RMT_NO_IMAP_DUMP_FILE", },				
	{ PNR_RMT_NO_DATA		,"RMT_NO_DATA", },						
	{ PNR_RMT_EMPTY_STREAM	,"RMT_EMPTY_STREAM", },					
	{ PNR_RMT_READ_ONLY_FILE,"RMT_READ_ONLY_FILE", },				


	{ PNR_PROP_NOT_FOUND	,"PROP_NOT_FOUND", },			
	{ PNR_PROP_NOT_COMPOSITE,"PROP_NOT_COMPOSITE", },		
	{ PNR_PROP_DUPLICATE	,"PROP_DUPLICATE", },			
	{ PNR_PROP_TYPE_MISMATCH,"PROP_TYPE_MISMATCH", },		
	{ PNR_PROP_ACTIVE		,"PROP_ACTIVE", },				
	{ PNR_PROP_INACTIVE		,"PROP_INACTIVE", },				

	{ PNR_COULDNOTINITCORE	,"COULDNOTINITCORE", },			
	{ PNR_PERFECTPLAY_NOT_SUPPORTED,"PERFECTPLAY_NOT_SUPPORTED", },	
	{ PNR_NO_LIVE_PERFECTPLAY,"NO_LIVE_PERFECTPLAY", },				
	{ PNR_PERFECTPLAY_NOT_ALLOWED,"PERFECTPLAY_NOT_ALLOWED", },	
	{ PNR_NO_CODECS			,"NO_CODECS", },							
	{ PNR_SLOW_MACHINE		,"SLOW_MACHINE", },						
	{ PNR_FORCE_PERFECTPLAY	,"FORCE_PERFECTPLAY", },					
	{ PNR_INVALID_HTTP_PROXY_HOST,"INVALID_HTTP_PROXY_HOST", },	
	{ PNR_INVALID_METAFILE	,"INVALID_METAFILE", },					
	{ PNR_BROWSER_LAUNCH	,"BROWSER_LAUNCH", },					
	{ PNR_VIEW_SOURCE_NOCLIP,"VIEW_SOURCE_NOCLIP", },				
	{ PNR_VIEW_SOURCE_DISSABLED,"VIEW_SOURCE_DISSABLED", },				

	{ PNR_RESOURCE_NOT_CACHED,"RESOURCE_NOT_CACHED", },				
	{ PNR_RESOURCE_NOT_FOUND,"RESOURCE_NOT_FOUND", },				
	{ PNR_RESOURCE_CLOSE_FILE_FIRST,"RESOURCE_CLOSE_FILE_FIRST", },	
	{ PNR_RESOURCE_NODATA	,"RESOURCE_NODATA", },					
	{ PNR_RESOURCE_BADFILE	,"RESOURCE_BADFILE", },					
	{ PNR_RESOURCE_PARTIALCOPY,"RESOURCE_PARTIALCOPY", },				

	{ PNR_PPV_NO_USER		,"PPV_NO_USER", },						
	{ PNR_PPV_GUID_READ_ONLY,"PPV_GUID_READ_ONLY", },				
	{ PNR_PPV_GUID_COLLISION,"PPV_GUID_COLLISION	", },			
	{ PNR_REGISTER_GUID_EXISTS,"REGISTER_GUID_EXISTS", },				
	{ PNR_PPV_AUTHORIZATION_FAILED,"PPV_AUTHORIZATION_FAILED", },
	{ PNR_PPV_OLD_PLAYER	,"PPV_OLD_PLAYER", },					
	{ PNR_PPV_ACCOUNT_LOCKED,"PPV_ACCOUNT_LOCKED", },				
// 	{ PNR_PPV_PROTOCOL_IGNORES,"PPV_PROTOCOL_IGNORES", },				
	{ PNR_PPV_DBACCESS_ERROR   ,"PPV_DBACCESS_ERROR", },             
	{ PNR_PPV_USER_ALREADY_EXISTS,"PPV_USER_ALREADY_EXISTS", },   

//eruto-upgrade (RealUpdate) errors
	{ PNR_UPG_AUTH_FAILED	,"UPG_AUTH_FAILED", },			
	{ PNR_UPG_CERT_AUTH_FAILED,"UPG_CERT_AUTH_FAILED", },		
	{ PNR_UPG_CERT_EXPIRED	,"UPG_CERT_EXPIRED", },			
	{ PNR_UPG_CERT_REVOKED	,"UPG_CERT_REVOKED", },			
	{ PNR_UPG_RUP_BAD		,"UPG_RUP_BAD", },				

// auto-config errorsuto-config errors
	{ PNR_AUTOCFG_SUCCESS	,"AUTOCFG_SUCCESS", },			
	{ PNR_AUTOCFG_FAILED	,"AUTOCFG_FAILED", },			
	{ PNR_AUTOCFG_ABORT		,"AUTOCFG_ABORT", },		

	{ PNR_FAILED			,"FAILED", },
	0,
};


static void
seterror(const char *funcname, PN_RESULT res)
{
	struct errors *p;

	for (p = errorlist; p->name; p++)
		if (p->error == res) {
			PyErr_Format(ErrorObject, "%s failed, error = %s", funcname, p->name);
			return;
		}
	PyErr_Format(ErrorObject, "%s failed, error = %x", funcname, res);
}


///////////////////////////////////////////
///////////////////////////////////////////
// Objects declarations

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IRMAClientEngine* pI;

	// engine's dll ref
	HINSTANCE hDll;
	// cashed pointers
	FPRMCREATEENGINE fpCreateEngine;
	FPRMCLOSEENGINE fpCloseEngine;
} RMAClientEngineObject;

staticforward PyTypeObject RMAClientEngineType;

static RMAClientEngineObject *
newRMAClientEngineObject()
{
	RMAClientEngineObject *self;

	self = PyObject_NEW(RMAClientEngineObject, &RMAClientEngineType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	self->hDll=NULL;
	self->fpCreateEngine=NULL;
	self->fpCloseEngine=NULL;
	/* XXXX Add your own initializers here */
	return self;
}

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IRMAPlayer* pI;

	// player's engine ref
	RMAClientEngineObject* pEngine;
} RMAPlayerObject;

staticforward PyTypeObject RMAPlayerType;

static RMAPlayerObject *
newRMAPlayerObject()
{
	RMAPlayerObject *self;

	self = PyObject_NEW(RMAPlayerObject, &RMAPlayerType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	self->pEngine = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IRMAErrorSinkControl* pI;

} RMAErrorSinkControlObject;

staticforward PyTypeObject RMAErrorSinkControlType;

static RMAErrorSinkControlObject *
newRMAErrorSinkControlObject()
{
	RMAErrorSinkControlObject *self;

	self = PyObject_NEW(RMAErrorSinkControlObject, &RMAErrorSinkControlType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}


//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
    IPyClientContext *pI;	
} ClientContextObject;

staticforward PyTypeObject ClientContextType;

static ClientContextObject *
newClientContextObject()
{
	ClientContextObject *self;
	self = PyObject_NEW(ClientContextObject, &ClientContextType);
	if (self == NULL)
		return NULL;
	self->pI=NULL;
	/* XXXX Add your own initializers here */
	return self;
}

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IPySiteSupplier* pI;
} SiteSupplierObject;

staticforward PyTypeObject SiteSupplierType;

static SiteSupplierObject *
newSiteSupplierObject()
{
	SiteSupplierObject *self;
	self = PyObject_NEW(SiteSupplierObject, &SiteSupplierType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IPyClientAdviseSink* pI;
} ClientAdviseSinkObject;

staticforward PyTypeObject ClientAdviseSinkType;

static ClientAdviseSinkObject *
newClientAdviseSinkObject()
{
	ClientAdviseSinkObject *self;
	self = PyObject_NEW(ClientAdviseSinkObject, &ClientAdviseSinkType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IPyErrorSink* pI;
} ErrorSinkObject;

staticforward PyTypeObject ErrorSinkType;

static ErrorSinkObject *
newErrorSinkObject()
{
	ErrorSinkObject *self;
	self = PyObject_NEW(ErrorSinkObject, &ErrorSinkType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IPyAuthenticationManager* pI;
} AuthenticationManagerObject;

staticforward PyTypeObject AuthenticationManagerType;

static AuthenticationManagerObject *
newAuthenticationManagerObject()
{
	AuthenticationManagerObject *self;
	self = PyObject_NEW(AuthenticationManagerObject, &AuthenticationManagerType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

//(general but defined here for indepentance)
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IUnknown* pI;
} UnknownObject;

staticforward PyTypeObject UnknownType;

static UnknownObject *
newUnknownObject()
{
	UnknownObject *self;

	self = PyObject_NEW(UnknownObject, &UnknownType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

///////////////////////////////////////////
///////////////////////////////////////////
// Objects definitions


////////////////////////////////////////////
// RMAClientEngine object 

static char RMAClientEngine_CreatePlayer__doc__[] =
""
;
static PyObject *
RMAClientEngine_CreatePlayer(RMAClientEngineObject *self, PyObject *args)
{
	PN_RESULT res;
	RMAPlayerObject *obj;
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	obj = newRMAPlayerObject();
	res = self->pI->CreatePlayer(obj->pI);
	if (FAILED(res)) {
		obj->pI = NULL;
		Py_DECREF(obj);
		seterror("RMAClientEngine_CreatePlayer", res);
		return NULL;
	}
	
	// keep engine alive
	obj->pEngine=self;
	Py_INCREF(self);
	
	return (PyObject*)obj;
}

static char RMAClientEngine_EventOccurred__doc__[] =
""
;
static PyObject *
RMAClientEngine_EventOccurred(RMAClientEngineObject *self, PyObject *args)
{
	PNxEvent pn_event;
	PN_RESULT res;
	
	/* Event = PyArg_ParseTuple(blabla) */
#ifdef _MACINTOSH
	EventRecord ev;
	if (!PyArg_ParseTuple(args, "O&", PyMac_GetEventRecord, &ev))
		return NULL;
	pn_event.event = ev.what;
	pn_event.window = 0;
	pn_event.param1 = &ev;
	pn_event.param2 = 0;
#else
	/* What _may_ work on unix is passing a zeroed struct. See the main program of
	** the minimal playback engine for details.
	** On Windows this magically seems to be unneeded at all.
	*/
	PyErr_SetString(PyExc_SystemError, 
			"rma PNxEvent mapping not implemented on this platform yet");
	return NULL;
#endif
	res = self->pI->EventOccurred(&pn_event);
	return Py_BuildValue("i", res);
}

static struct PyMethodDef RMAClientEngine_methods[] = {
	{"CreatePlayer", (PyCFunction)RMAClientEngine_CreatePlayer, METH_VARARGS, RMAClientEngine_CreatePlayer__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
RMAClientEngine_dealloc(RMAClientEngineObject *self)
{
	/* XXXX Add your own cleanup code here */
	if (self->pI) {
		self->fpCloseEngine(self->pI);
		self->pI = NULL;
	}
	if (self->hDll) {
		FreeLibrary(self->hDll);
		self->hDll = NULL;
	}
	PyMem_DEL(self);
}

static PyObject *
RMAClientEngine_getattr(RMAClientEngineObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(RMAClientEngine_methods, (PyObject *)self, name);
}

static char RMAClientEngineType__doc__[] =
""
;

static PyTypeObject RMAClientEngineType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"RMAClientEngine",			/*tp_name*/
	sizeof(RMAClientEngineObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)RMAClientEngine_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)RMAClientEngine_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0,		/*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	RMAClientEngineType__doc__ /* Documentation string */
};

// End of code for RMAClientEngine object 
////////////////////////////////////////////

////////////////////////////////////////////
// RMAPlayer object 

static char RMAPlayer_OpenURL__doc__[] =
""
;
static PyObject *
RMAPlayer_OpenURL(RMAPlayerObject *self, PyObject *args)
{
	PN_RESULT res;
	char *psz;
	if (!PyArg_ParseTuple(args, "s", &psz))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->OpenURL(psz);
	Py_END_ALLOW_THREADS
	if (FAILED(res)){
		seterror("RMAPlayer_OpenURL", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char RMAPlayer_Begin__doc__[] =
""
;
static PyObject *
RMAPlayer_Begin(RMAPlayerObject *self, PyObject *args)
{
	PN_RESULT res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->Begin();
	Py_END_ALLOW_THREADS
	if (FAILED(res)){
		seterror("RMAPlayer_Begin", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char RMAPlayer_Stop__doc__[] =
""
;
static PyObject *
RMAPlayer_Stop(RMAPlayerObject *self, PyObject *args)
{
	PN_RESULT res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->Stop();
	Py_END_ALLOW_THREADS
	if (FAILED(res)){
		seterror("RMAPlayer_Stop", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char RMAPlayer_Pause__doc__[] =
""
;
static PyObject *
RMAPlayer_Pause(RMAPlayerObject *self, PyObject *args)
{
	PN_RESULT res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->Pause();
	Py_END_ALLOW_THREADS
	if (FAILED(res)){
		seterror("RMAPlayer_Pause", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char RMAPlayer_IsDone__doc__[] =
""
;
static PyObject *
RMAPlayer_IsDone(RMAPlayerObject *self, PyObject *args)
{
	BOOL res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	Py_BEGIN_ALLOW_THREADS
	res=self->pI->IsDone();
	Py_END_ALLOW_THREADS
	return Py_BuildValue("i",res);
}

static char RMAPlayer_IsLive__doc__[] =
""
;
static PyObject *
RMAPlayer_IsLive(RMAPlayerObject *self, PyObject *args)
{
	BOOL res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	Py_BEGIN_ALLOW_THREADS
	res=self->pI->IsLive();
	Py_END_ALLOW_THREADS
	return Py_BuildValue("i",res);
}

static char RMAPlayer_GetCurrentPlayTime__doc__[] =
""
;
static PyObject *
RMAPlayer_GetCurrentPlayTime(RMAPlayerObject *self, PyObject *args)
{
	ULONG32 res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	Py_BEGIN_ALLOW_THREADS
	res=self->pI->GetCurrentPlayTime();
	Py_END_ALLOW_THREADS
	return Py_BuildValue("i",res);
}

static char RMAPlayer_Seek__doc__[] =
""
;
static PyObject *
RMAPlayer_Seek(RMAPlayerObject *self, PyObject *args)
{
	ULONG32 val;
	PN_RESULT res;
	if (!PyArg_ParseTuple(args, "i", &val))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	res=self->pI->Seek(val);
	Py_END_ALLOW_THREADS
	return Py_BuildValue("i",res);
}

static char RMAPlayer_SetClientContext__doc__[] =
""
;
static PyObject *
RMAPlayer_SetClientContext(RMAPlayerObject *self, PyObject *args)
{
	PN_RESULT res;
	ClientContextObject *obj;
	if (!PyArg_ParseTuple(args, "O!",&ClientContextType,&obj))
		return NULL;
	
	Py_BEGIN_ALLOW_THREADS
	res= self->pI->SetClientContext(obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(res)){
		seterror("RMAPlayer_SetClientContext", res);
		return NULL;
	}	
	Py_INCREF(Py_None);
	return Py_None;	
}


static char RMAPlayer_AddAdviseSink__doc__[] =
""
;
static PyObject *
RMAPlayer_AddAdviseSink(RMAPlayerObject *self, PyObject *args)
{
	PN_RESULT res;
	ClientAdviseSinkObject *obj;
	if (!PyArg_ParseTuple(args, "O!",&ClientAdviseSinkType,&obj))
		return NULL;

	IRMAClientAdviseSink* pI=NULL;
	res=self->pI->QueryInterface(IID_IRMAErrorSinkControl,(void**)&pI);
	if (FAILED(res)){
		seterror("RMAPlayer_QueryIRMAErrorSinkControl", res);
		return NULL;
	}	

	Py_BEGIN_ALLOW_THREADS
	res= self->pI->AddAdviseSink(pI);
	Py_END_ALLOW_THREADS
	if (FAILED(res)){
		seterror("RMAPlayer_AddAdviseSink", res);
		return NULL;
	}	
	Py_INCREF(Py_None);
	return Py_None;	
}


static char RMAPlayer_QueryIRMAErrorSinkControl__doc__[] =
""
;
static PyObject *
RMAPlayer_QueryIRMAErrorSinkControl(RMAPlayerObject *self, PyObject *args)
{
	PN_RESULT res;
	RMAErrorSinkControlObject *obj;	
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	obj = newRMAErrorSinkControlObject();
	if(obj==NULL) return NULL;
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->QueryInterface(IID_IRMAErrorSinkControl,(void**)&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(res)){
		Py_DECREF(obj);
		seterror("RMAPlayer_QueryIRMAErrorSinkControl", res);
		return NULL;
	}
	return (PyObject*)obj;
}

static struct PyMethodDef RMAPlayer_methods[] = {
	{"OpenURL", (PyCFunction)RMAPlayer_OpenURL, METH_VARARGS, RMAPlayer_OpenURL__doc__},
	{"Begin", (PyCFunction)RMAPlayer_Begin, METH_VARARGS, RMAPlayer_Begin__doc__},
	{"Stop", (PyCFunction)RMAPlayer_Stop, METH_VARARGS, RMAPlayer_Stop__doc__},
	{"Pause", (PyCFunction)RMAPlayer_Pause, METH_VARARGS, RMAPlayer_Pause__doc__},
	{"IsDone", (PyCFunction)RMAPlayer_IsDone, METH_VARARGS, RMAPlayer_IsDone__doc__},
	{"IsLive", (PyCFunction)RMAPlayer_IsLive, METH_VARARGS, RMAPlayer_IsLive__doc__},
	{"GetCurrentPlayTime", (PyCFunction)RMAPlayer_GetCurrentPlayTime, METH_VARARGS, RMAPlayer_GetCurrentPlayTime__doc__},
	{"Seek", (PyCFunction)RMAPlayer_Seek, METH_VARARGS, RMAPlayer_Seek__doc__},
	{"SetClientContext", (PyCFunction)RMAPlayer_SetClientContext, METH_VARARGS, RMAPlayer_SetClientContext__doc__},
	{"AddAdviseSink", (PyCFunction)RMAPlayer_AddAdviseSink, METH_VARARGS, RMAPlayer_AddAdviseSink__doc__},
	{"QueryIRMAErrorSinkControl", (PyCFunction)RMAPlayer_QueryIRMAErrorSinkControl, METH_VARARGS, RMAPlayer_QueryIRMAErrorSinkControl__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
RMAPlayer_dealloc(RMAPlayerObject *self)
{
	/* XXXX Add your own cleanup code here */
	if (self->pI) {
		self->pEngine->pI->ClosePlayer(self->pI);
		self->pI->Release();
		self->pI = NULL;
		Py_DECREF(self->pEngine);
	}
	PyMem_DEL(self);
}

static PyObject *
RMAPlayer_getattr(RMAPlayerObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(RMAPlayer_methods, (PyObject *)self, name);
}

static char RMAPlayerType__doc__[] =
""
;

static PyTypeObject RMAPlayerType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"RMAPlayer",			/*tp_name*/
	sizeof(RMAPlayerObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)RMAPlayer_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)RMAPlayer_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0,		/*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	RMAPlayerType__doc__ /* Documentation string */
};

// End of code for RMAPlayer object 
////////////////////////////////////////////

////////////////////////////////////////////
// RMAErrorSinkControl object 

static char RMAErrorSinkControl_QueryIUnknown__doc__[] =
""
;
static PyObject *
RMAErrorSinkControl_QueryIUnknown(RMAErrorSinkControlObject *self, PyObject *args)
{
	PN_RESULT res;
	UnknownObject *obj;	
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	obj = newUnknownObject();
	if(obj==NULL) return NULL;
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->QueryInterface(IID_IUnknown,(void**)&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(res)){
		Py_DECREF(obj);
		seterror("RMAErrorSinkControl_QueryIUnknown", res);
		return NULL;
	}
	return (PyObject*)obj;
}

static char RMAErrorSinkControl_AddErrorSink__doc__[] =
""
;
static PyObject *
RMAErrorSinkControl_AddErrorSink(RMAErrorSinkControlObject *self, PyObject *args)
{
	PN_RESULT res;
	ErrorSinkObject *obj;
	int low_severity=PNLOG_EMERG,hi_severity=PNLOG_INFO;
	if (!PyArg_ParseTuple(args, "O!|ii", &ErrorSinkType,&obj,
		&low_severity,&hi_severity))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->AddErrorSink((IRMAErrorSink*)obj->pI,UINT8(low_severity),UINT8(hi_severity));
	Py_END_ALLOW_THREADS
	if (FAILED(res)){
		seterror("RMAErrorSinkControl_AddErrorSink", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef RMAErrorSinkControl_methods[] = {
	{"QueryIUnknown", (PyCFunction)RMAErrorSinkControl_QueryIUnknown, METH_VARARGS, RMAErrorSinkControl_QueryIUnknown__doc__},
	{"AddErrorSink", (PyCFunction)RMAErrorSinkControl_AddErrorSink, METH_VARARGS, RMAErrorSinkControl_AddErrorSink__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
RMAErrorSinkControl_dealloc(RMAErrorSinkControlObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI)
	PyMem_DEL(self);
}

static PyObject *
RMAErrorSinkControl_getattr(RMAErrorSinkControlObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(RMAErrorSinkControl_methods, (PyObject *)self, name);
}

static char RMAErrorSinkControlType__doc__[] =
""
;

static PyTypeObject RMAErrorSinkControlType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"RMAErrorSinkControl",			/*tp_name*/
	sizeof(RMAErrorSinkControlObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)RMAErrorSinkControl_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)RMAErrorSinkControl_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0,		/*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	RMAErrorSinkControlType__doc__ /* Documentation string */
};

// End of code for RMAErrorSinkControl object 
////////////////////////////////////////////

////////////////////////////////////////////
// ClientContext object 


static char ClientContext_AddInterface__doc__[] =
""
;
static PyObject *
ClientContext_AddInterface(ClientContextObject *self, PyObject *args)
{
	PN_RESULT res;
	UnknownObject *obj;
	if (!PyArg_ParseTuple(args, "O!", &UnknownType,&obj))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->AddInterface(obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(res)){
		seterror("ClientContext_AddInterface", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef ClientContext_methods[] = {
	{"AddInterface", (PyCFunction)ClientContext_AddInterface, METH_VARARGS, ClientContext_AddInterface__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
ClientContext_dealloc(ClientContextObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI)
	PyMem_DEL(self);
}

static PyObject *
ClientContext_getattr(ClientContextObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(ClientContext_methods, (PyObject *)self, name);
}

static char ClientContextType__doc__[] =
""
;

static PyTypeObject ClientContextType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"ClientContext",			/*tp_name*/
	sizeof(ClientContextObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)ClientContext_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)ClientContext_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0,		/*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	ClientContextType__doc__ /* Documentation string */
};

// End of code for ClientContext object 
////////////////////////////////////////////


////////////////////////////////////////////
// ClientAdviseSink object 

static char ClientAdviseSink_QueryIUnknown__doc__[] =
""
;
static PyObject *
ClientAdviseSink_QueryIUnknown(ClientAdviseSinkObject *self, PyObject *args)
{
	PN_RESULT res;
	UnknownObject *obj;	
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	obj = newUnknownObject();
	if(obj==NULL) return NULL;
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->QueryInterface(IID_IUnknown,(void**)&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(res)){
		Py_DECREF(obj);
		seterror("ClientAdviseSink_QueryIUnknown", res);
		return NULL;
	}
	return (PyObject*)obj;
}

static char ClientAdviseSink_SetPyListener__doc__[] =
""
;
static PyObject *
ClientAdviseSink_SetPyListener(ClientAdviseSinkObject *self, PyObject *args)
{
	PyObject *obj;	
	if (!PyArg_ParseTuple(args, "O",&obj))
		return NULL;	
	self->pI->SetPyAdviceSink(obj);
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef ClientAdviseSink_methods[] = {
	{"QueryIUnknown", (PyCFunction)ClientAdviseSink_QueryIUnknown, METH_VARARGS, ClientAdviseSink_QueryIUnknown__doc__},
	{"SetPyListener", (PyCFunction)ClientAdviseSink_SetPyListener, METH_VARARGS, ClientAdviseSink_SetPyListener__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
ClientAdviseSink_dealloc(ClientAdviseSinkObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI)
	PyMem_DEL(self);
}

static PyObject *
ClientAdviseSink_getattr(ClientAdviseSinkObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(ClientAdviseSink_methods, (PyObject *)self, name);
}

static char ClientAdviseSinkType__doc__[] =
""
;

static PyTypeObject ClientAdviseSinkType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"ClientAdviseSink",			/*tp_name*/
	sizeof(ClientAdviseSinkObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)ClientAdviseSink_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)ClientAdviseSink_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0,		/*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	ClientAdviseSinkType__doc__ /* Documentation string */
};

// End of code for ClientAdviseSink object 
////////////////////////////////////////////


////////////////////////////////////////////
// ErrorSink object 

static char ErrorSink_QueryIUnknown__doc__[] =
""
;
static PyObject *
ErrorSink_QueryIUnknown(ErrorSinkObject *self, PyObject *args)
{
	PN_RESULT res;
	UnknownObject *obj;	
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	obj = newUnknownObject();
	if(obj==NULL) return NULL;
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->QueryInterface(IID_IUnknown,(void**)&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(res)){
		Py_DECREF(obj);
		seterror("ErrorSink_QueryIUnknown", res);
		return NULL;
	}
	return (PyObject*)obj;
}

static struct PyMethodDef ErrorSink_methods[] = {
	{"QueryIUnknown", (PyCFunction)ErrorSink_QueryIUnknown, METH_VARARGS, ErrorSink_QueryIUnknown__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
ErrorSink_dealloc(ErrorSinkObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI)
	PyMem_DEL(self);
}

static PyObject *
ErrorSink_getattr(ErrorSinkObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(ErrorSink_methods, (PyObject *)self, name);
}

static char ErrorSinkType__doc__[] =
""
;

static PyTypeObject ErrorSinkType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"ErrorSink",			/*tp_name*/
	sizeof(ErrorSinkObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)ErrorSink_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)ErrorSink_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0,		/*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	ErrorSinkType__doc__ /* Documentation string */
};

// End of code for ErrorSink object 
////////////////////////////////////////////


////////////////////////////////////////////
// SiteSupplier object 

static char SiteSupplier_QueryIUnknown__doc__[] =
""
;
static PyObject *
SiteSupplier_QueryIUnknown(SiteSupplierObject *self, PyObject *args)
{
	PN_RESULT res;
	UnknownObject *obj;	
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	obj = newUnknownObject();
	if(obj==NULL) return NULL;
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->QueryInterface(IID_IUnknown,(void**)&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(res)){
		Py_DECREF(obj);
		seterror("SiteSupplier_QueryIUnknown", res);
		return NULL;
	}
	return (PyObject*)obj;
}

static struct PyMethodDef SiteSupplier_methods[] = {
	{"QueryIUnknown", (PyCFunction)SiteSupplier_QueryIUnknown, METH_VARARGS, SiteSupplier_QueryIUnknown__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
SiteSupplier_dealloc(SiteSupplierObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI)
	PyMem_DEL(self);
}

static PyObject *
SiteSupplier_getattr(SiteSupplierObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(SiteSupplier_methods, (PyObject *)self, name);
}

static char SiteSupplierType__doc__[] =
""
;

static PyTypeObject SiteSupplierType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"SiteSupplier",			/*tp_name*/
	sizeof(SiteSupplierObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)SiteSupplier_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)SiteSupplier_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0,		/*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	SiteSupplierType__doc__ /* Documentation string */
};

// End of code for SiteSupplier object 
////////////////////////////////////////////


////////////////////////////////////////////
// AuthenticationManager object 

static char AuthenticationManager_QueryIUnknown__doc__[] =
""
;
static PyObject *
AuthenticationManager_QueryIUnknown(SiteSupplierObject *self, PyObject *args)
{
	PN_RESULT res;
	UnknownObject *obj;	
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	obj = newUnknownObject();
	if(obj==NULL) return NULL;
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->QueryInterface(IID_IUnknown,(void**)&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(res)){
		Py_DECREF(obj);
		seterror("AuthenticationManager_QueryIUnknown", res);
		return NULL;
	}
	return (PyObject*)obj;
}

static struct PyMethodDef AuthenticationManager_methods[] = {
	{"QueryIUnknown", (PyCFunction)AuthenticationManager_QueryIUnknown, METH_VARARGS, AuthenticationManager_QueryIUnknown__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
AuthenticationManager_dealloc(AuthenticationManagerObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI)
	PyMem_DEL(self);
}

static PyObject *
AuthenticationManager_getattr(AuthenticationManagerObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(AuthenticationManager_methods, (PyObject *)self, name);
}

static char AuthenticationManagerType__doc__[] =
""
;

static PyTypeObject AuthenticationManagerType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"AuthenticationManager",			/*tp_name*/
	sizeof(AuthenticationManagerObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)AuthenticationManager_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)AuthenticationManager_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0,		/*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	AuthenticationManagerType__doc__ /* Documentation string */
};

// End of code for AuthenticationManager object 
////////////////////////////////////////////

////////////////////////////////////////////
// Unknown object (general but defined here for indepentance) 

static struct PyMethodDef Unknown_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
Unknown_dealloc(UnknownObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
Unknown_getattr(UnknownObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(Unknown_methods, (PyObject *)self, name);
}

static char UnknownType__doc__[] =
""
;

static PyTypeObject UnknownType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"Unknown",			/*tp_name*/
	sizeof(UnknownObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)Unknown_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)Unknown_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0,		/*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	UnknownType__doc__ /* Documentation string */
};

// End of code for Unknown object 
////////////////////////////////////////////


///////////////////////////////////////////
///////////////////////////////////////////
// MODULE
//

static bool
CreateRMAClientEngine(RMAClientEngineObject *obj)
{
	// initialize the globals
	obj->fpCreateEngine = NULL;
	obj->fpCloseEngine = NULL;

	// prepare/load the RMACore module
	char szDllName[_MAX_PATH];
    
#if defined(_UNIX)
	strcpy(szDllName, "rmacore.dll");

#elif defined(_MACINTOSH)
	// ASSUME rmacore is in System Folder:Extensions:Real:Common
	// SHOULD obtain value from preference file
	OSErr macErr;

	// set szDllName to empty string
	szDllName[0] = '\0'; 

	// find the Extensions folder
	short vRefNum;
	long dirID;
#if 0
	/* Older G2 beta's had the engine in the extensions folder */
	macErr = FindFolder (kOnSystemDisk, kExtensionFolderType, kDontCreateFolder, &vRefNum, &dirID);
#else
	macErr = FindFolder (kOnSystemDisk, kApplicationSupportFolderType, kDontCreateFolder, &vRefNum, &dirID);
#endif

	// find the path of the Extensions folder
	DirInfo block;
	Str63 directoryName;
	char tmpName[_MAX_PATH];

	block.ioDrParID = dirID;
	block.ioNamePtr = directoryName;
	do {
		block.ioVRefNum = vRefNum;
		block.ioFDirIndex = -1;
		block.ioDrDirID = block.ioDrParID;

		macErr = PBGetCatInfoSync ((CInfoPBPtr)&block);
		if (macErr == noErr) {
			strcpy (tmpName, szDllName);
			szDllName[0] = '\0';
			strncat (szDllName, (char*)&directoryName[1], directoryName[0]);
			if (strlen(tmpName)) {
				strcat (szDllName, ":");
				strcat (szDllName, tmpName);
			}
		}
	} while ((macErr == noErr) && (block.ioDrDirID != 2));// 2 means root directory of a volume
	strcat (szDllName, ":Real:Common:rmacore60.dll");
	//strcpy(szDllName, "rmacore60.dll");

#elif defined(_WIN32) 
	// get location of rmacore from windows registry 
	DWORD bufSize;
	HKEY hKey; 
	PN_RESULT hRes;
    
	szDllName[0] = '\0'; 
	bufSize = sizeof(szDllName) - 1;

	if(ERROR_SUCCESS == RegOpenKey(HKEY_CLASSES_ROOT,
				       "Software\\RealNetworks\\Preferences\\DT_Common", &hKey)) { 
		// get the path to pnen 
		hRes = RegQueryValue(hKey, "", szDllName, (long *)&bufSize); 
		RegCloseKey(hKey); 
		if(hRes!=ERROR_SUCCESS) return false;
	}
	else {
		// No RealPlayer registry entries
		return false;
	}
	strcat(szDllName, "pnen3260.dll");

#elif defined(_WIN16) 
	strcpy(szDllName, "pnen1660.dll");
#else
#error Unknown platform
#endif
    
	if ((obj->hDll = LoadLibrary(szDllName)) == NULL) {
#ifdef FUNNY_FPRINTFS
#if defined(_UNIX)
		fprintf(stdout, "Failed to load the 'rmacore.so.6.0' shared library\n");
		fprintf(stdout, dlerror());
#else
		fprintf(stdout, "Failed to load the '%s' library.\n", szDllName);
#endif
#endif
		return false;
	}


	// retrieve the proc addresses from the module
	obj->fpCreateEngine = (FPRMCREATEENGINE) GetProcAddress(obj->hDll, "CreateEngine");
	obj->fpCloseEngine  = (FPRMCLOSEENGINE)  GetProcAddress(obj->hDll, "CloseEngine");
 
	if (obj->fpCreateEngine == NULL ||
	    obj->fpCloseEngine == NULL) {
		return false;
	}

	// create client engine 
	if (PNR_OK != obj->fpCreateEngine(&obj->pI)) {
		return false;
	}
	return true;
}


static char RMA_CreateRMAClientEngine__doc__[] =
""
;
static PyObject *
RMA_CreateRMAClientEngine(PyObject *self, PyObject *args)
{
	RMAClientEngineObject *obj;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;

	obj = newRMAClientEngineObject();
	if (obj == NULL)
		return NULL;
	if(!CreateRMAClientEngine(obj)){
		Py_DECREF(obj);
		seterror("CreateRMAClientEngine");
		return NULL;
	}
		
	return (PyObject *) obj;
}

static char RMA_CreateClientContext__doc__[] =
""
;
static PyObject *
RMA_CreateClientContext(PyObject *self, PyObject *args)
{
	PN_RESULT res;
	ClientContextObject *obj;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;

	obj = newClientContextObject();
	if (obj == NULL)
		return NULL;
	res = CreateClientContext(&obj->pI);
	if(FAILED(res)){
		Py_DECREF(obj);
		seterror("CreateClientContext");
		return NULL;
	}
	return (PyObject *) obj;
}

static char RMA_CreateClientAdviseSink__doc__[] =
""
;
static PyObject *
RMA_CreateClientAdviseSink(PyObject *self, PyObject *args)
{
	PN_RESULT res;
	ClientAdviseSinkObject *obj;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;

	obj = newClientAdviseSinkObject();
	if (obj == NULL)
		return NULL;
	res = CreateClientAdviseSink(&obj->pI);
	if(FAILED(res)){
		Py_DECREF(obj);
		seterror("CreateClientAdviseSink");
		return NULL;
	}
	return (PyObject *) obj;
}

static char RMA_CreateErrorSink__doc__[] =
""
;
static PyObject *
RMA_CreateErrorSink(PyObject *self, PyObject *args)
{
	PN_RESULT res;
	ErrorSinkObject *obj;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;

	obj = newErrorSinkObject();
	if (obj == NULL)
		return NULL;
	res = CreateErrorSink(&obj->pI);
	if(FAILED(res)){
		Py_DECREF(obj);
		seterror("CreateErrorSink");
		return NULL;
	}
	return (PyObject *) obj;
}

static char RMA_CreateSiteSupplier__doc__[] =
""
;
static PyObject *
RMA_CreateSiteSupplier(PyObject *self, PyObject *args)
{
	PN_RESULT res;
	SiteSupplierObject *obj;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;

	obj = newSiteSupplierObject();
	if (obj == NULL)
		return NULL;
	res = CreateSiteSupplier(&obj->pI);
	if(FAILED(res)){
		Py_DECREF(obj);
		seterror("CreateSiteSupplier");
		return NULL;
	}
	return (PyObject *) obj;
}

static char RMA_CreateAuthenticationManager__doc__[] =
""
;
static PyObject *
RMA_CreateAuthenticationManager(PyObject *self, PyObject *args)
{
	PN_RESULT res;
	AuthenticationManagerObject *obj;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;

	obj = newAuthenticationManagerObject();
	if (obj == NULL)
		return NULL;
	res = CreateAuthenticationManager(&obj->pI);
	if(FAILED(res)){
		Py_DECREF(obj);
		seterror("CreateAuthenticationManager");
		return NULL;
	}
	return (PyObject *) obj;
}

static struct PyMethodDef rma_methods[] = {
	{"CreateEngine", (PyCFunction)RMA_CreateRMAClientEngine, METH_VARARGS, RMA_CreateRMAClientEngine__doc__},
	{"CreateClientContext", (PyCFunction)RMA_CreateClientContext, METH_VARARGS, RMA_CreateClientContext__doc__},
	{"CreateClientAdviseSink", (PyCFunction)RMA_CreateClientAdviseSink, METH_VARARGS, RMA_CreateClientAdviseSink__doc__},
	{"CreateErrorSink", (PyCFunction)RMA_CreateErrorSink, METH_VARARGS, RMA_CreateErrorSink__doc__},
	{"CreateSiteSupplier", (PyCFunction)RMA_CreateSiteSupplier, METH_VARARGS, RMA_CreateSiteSupplier__doc__},
	{"CreateAuthenticationManager", (PyCFunction)RMA_CreateAuthenticationManager, METH_VARARGS, RMA_CreateAuthenticationManager__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};


/* Initialization function for the module (*must* be called initrma) */

static char rma_module_documentation[] =
""
;

extern "C"
#ifdef _WINDOWS
__declspec(dllexport)
#endif
void
initrma()
{
	PyObject *m, *d;

	/* Create the module and add the functions */
	m = Py_InitModule4("rma", rma_methods,
		rma_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	/* Add some symbolic constants to the module */
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("rma.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	/* Check for errors */
	if (PyErr_Occurred()) {
		Py_FatalError("can't initialize module rma");
	}
}
