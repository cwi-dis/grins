/***********************************************************
Copyright 1991-1999 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

#include "Python.h"

#define INITGUID

#include "pntypes.h"
#include "pnwintyp.h"
#include "pnresult.h"
#include "pncom.h"

#include "rmaenum.h"
#include "engtypes.h"
#include "engtargs.h"
#include "engcodec.h"
#include "rmbldeng.h"
#include "rmmetain.h"
#include "rmapckts.h"
#include "progsink.h"

#define APP_MAX_PATH	255

static PyObject *ErrorObject;

struct errors {
	HRESULT error;
	char *name;
} errorlist [] = {
	{ PNR_NOTIMPL, "NOTIMPL", },
	{ PNR_OUTOFMEMORY, "OUTOFMEMORY", },
	{ PNR_INVALID_PARAMETER, "INVALID_PARAMETER", },
	{ PNR_NOINTERFACE, "NOINTERFACE", },
	{ PNR_POINTER, "POINTER", },
	{ PNR_HANDLE, "HANDLE", },
	{ PNR_ABORT, "ABORT", },
	{ PNR_FAIL, "FAIL", },
	{ PNR_ACCESSDENIED, "ACCESSDENIED", },
	{ PNR_IGNORE, "IGNORE", },
	{ PNR_OK, "OK", },
	{ PNR_INVALID_OPERATION, "INVALID_OPERATION", },
	{ PNR_INVALID_VERSION, "INVALID_VERSION", },
	{ PNR_INVALID_REVISION, "INVALID_REVISION", },
	{ PNR_NOT_INITIALIZED, "NOT_INITIALIZED", },
	{ PNR_DOC_MISSING, "DOC_MISSING", },
	{ PNR_UNEXPECTED, "UNEXPECTED", },
	{ PNR_NO_FILEFORMAT, "NO_FILEFORMAT", },
	{ PNR_NO_RENDERER, "NO_RENDERER", },
	{ PNR_INCOMPLETE, "INCOMPLETE", },
	{ PNR_BUFFERTOOSMALL, "BUFFERTOOSMALL", },
	{ PNR_UNSUPPORTED_VIDEO, "UNSUPPORTED_VIDEO", },
	{ PNR_UNSUPPORTED_AUDIO, "UNSUPPORTED_AUDIO", },
	{ PNR_INVALID_BANDWIDTH, "INVALID_BANDWIDTH", },
	{ PNR_MISSING_COMPONENTS, "MISSING_COMPONENTS", },
	{ PNR_ELEMENT_NOT_FOUND, "ELEMENT_NOT_FOUND", },
	{ PNR_NOCLASS, "NOCLASS", },
	{ PNR_CLASS_NOAGGREGATION, "CLASS_NOAGGREGATION", },
	{ PNR_NOT_LICENSED, "NOT_LICENSED", },
	{ PNR_NO_FILESYSTEM, "NO_FILESYSTEM", },
	{ PNR_BUFFERING, "BUFFERING", },
	{ PNR_PAUSED, "PAUSED", },
	{ PNR_NO_DATA, "NO_DATA", },
	{ PNR_STREAM_DONE, "STREAM_DONE", },
	{ PNR_NET_SOCKET_INVALID, "NET_SOCKET_INVALID", },
	{ PNR_NET_CONNECT, "NET_CONNECT", },
	{ PNR_BIND, "BIND", },
	{ PNR_SOCKET_CREATE, "SOCKET_CREATE", },
	{ PNR_INVALID_HOST, "INVALID_HOST", },
	{ PNR_NET_READ, "NET_READ", },
	{ PNR_NET_WRITE, "NET_WRITE", },
	{ PNR_NET_UDP, "NET_UDP", },
	{ PNR_RETRY, "RETRY", },
	{ PNR_SERVER_TIMEOUT, "SERVER_TIMEOUT", },
	{ PNR_SERVER_DISCONNECTED, "SERVER_DISCONNECTED", },
	{ PNR_WOULD_BLOCK, "WOULD_BLOCK", },
	{ PNR_GENERAL_NONET, "GENERAL_NONET", },
	{ PNR_BLOCK_CANCELED, "BLOCK_CANCELED", },
	{ PNR_MULTICAST_JOIN, "MULTICAST_JOIN", },
	{ PNR_GENERAL_MULTICAST, "GENERAL_MULTICAST", },
	{ PNR_MULTICAST_UDP, "MULTICAST_UDP", },
	{ PNR_AT_INTERRUPT, "AT_INTERRUPT", },
	{ PNR_MSG_TOOLARGE, "MSG_TOOLARGE", },
	{ PNR_NET_TCP, "NET_TCP", },
	{ PNR_TRY_AUTOCONFIG, "TRY_AUTOCONFIG", },
	{ PNR_NOTENOUGH_BANDWIDTH, "NOTENOUGH_BANDWIDTH", },
	{ PNR_HTTP_CONNECT, "HTTP_CONNECT", },
	{ PNR_PORT_IN_USE, "PORT_IN_USE", },
	{ PNR_AT_END, "AT_END", },
	{ PNR_INVALID_FILE, "INVALID_FILE", },
	{ PNR_INVALID_PATH, "INVALID_PATH", },
	{ PNR_RECORD, "RECORD", },
	{ PNR_RECORD_WRITE, "RECORD_WRITE", },
	{ PNR_TEMP_FILE, "TEMP_FILE", },
	{ PNR_ALREADY_OPEN, "ALREADY_OPEN", },
	{ PNR_SEEK_PENDING, "SEEK_PENDING", },
	{ PNR_CANCELLED, "CANCELLED", },
	{ PNR_FILE_NOT_FOUND, "FILE_NOT_FOUND", },
	{ PNR_WRITE_ERROR, "WRITE_ERROR", },
	{ PNR_FILE_EXISTS, "FILE_EXISTS", },
#define	PNR_FILE_NOT_OPEN		MAKE_PN_RESULT(1,SS_FIL,12)
	{ PNR_ADVISE_PREFER_LINEAR, "ADVISE_PREFER_LINEAR", },
	{ PNR_PARSE_ERROR, "PARSE_ERROR", },
	{ PNR_BAD_SERVER, "BAD_SERVER", },
	{ PNR_ADVANCED_SERVER, "ADVANCED_SERVER", },
	{ PNR_OLD_SERVER, "OLD_SERVER", },
	{ PNR_REDIRECTION, "REDIRECTION", },
	{ PNR_SERVER_ALERT, "SERVER_ALERT", },
	{ PNR_PROXY, "PROXY", },
	{ PNR_PROXY_RESPONSE, "PROXY_RESPONSE", },
	{ PNR_ADVANCED_PROXY, "ADVANCED_PROXY", },
	{ PNR_OLD_PROXY, "OLD_PROXY", },
	{ PNR_INVALID_PROTOCOL, "INVALID_PROTOCOL", },
	{ PNR_INVALID_URL_OPTION, "INVALID_URL_OPTION", },
	{ PNR_INVALID_URL_HOST, "INVALID_URL_HOST", },
	{ PNR_INVALID_URL_PATH, "INVALID_URL_PATH", },
	{ PNR_HTTP_CONTENT_NOT_FOUND, "HTTP_CONTENT_NOT_FOUND", },
	{ PNR_NOT_AUTHORIZED, "NOT_AUTHORIZED", },
	{ PNR_UNEXPECTED_MSG, "UNEXPECTED_MSG", },
	{ PNR_BAD_TRANSPORT, "BAD_TRANSPORT", },
	{ PNR_NO_SESSION_ID, "NO_SESSION_ID", },
	{ PNR_PROXY_DNR, "PROXY_DNR", },
	{ PNR_PROXY_NET_CONNECT, "PROXY_NET_CONNECT", },
	{ PNR_AUDIO_DRIVER, "AUDIO_DRIVER", },
	{ PNR_LATE_PACKET, "LATE_PACKET", },
	{ PNR_OVERLAPPED_PACKET, "OVERLAPPED_PACKET", },
	{ PNR_OUTOFORDER_PACKET, "OUTOFORDER_PACKET", },
	{ PNR_NONCONTIGUOUS_PACKET, "NONCONTIGUOUS_PACKET", },
	{ PNR_OPEN_NOT_PROCESSED, "OPEN_NOT_PROCESSED", },
	{ PNR_EXPIRED, "EXPIRED", },
	{ PNR_INVALID_INTERLEAVER, "INVALID_INTERLEAVER", },
	{ PNR_BAD_FORMAT, "BAD_FORMAT", },
	{ PNR_CHUNK_MISSING, "CHUNK_MISSING", },
	{ PNR_INVALID_STREAM, "INVALID_STREAM", },
	{ PNR_DNR, "DNR", },
	{ PNR_OPEN_DRIVER, "OPEN_DRIVER", },
	{ PNR_UPGRADE, "UPGRADE", },
	{ PNR_NOTIFICATION, "NOTIFICATION", },
	{ PNR_NOT_NOTIFIED, "NOT_NOTIFIED", },
	{ PNR_STOPPED, "STOPPED", },
	{ PNR_CLOSED, "CLOSED", },
	{ PNR_INVALID_WAV_FILE, "INVALID_WAV_FILE", },
	{ PNR_NO_SEEK, "NO_SEEK", },
	{ PNR_DEC_INITED, "DEC_INITED", },
	{ PNR_DEC_NOT_FOUND, "DEC_NOT_FOUND", },
	{ PNR_DEC_INVALID, "DEC_INVALID", },
	{ PNR_DEC_TYPE_MISMATCH, "DEC_TYPE_MISMATCH", },
	{ PNR_DEC_INIT_FAILED, "DEC_INIT_FAILED", },
	{ PNR_DEC_NOT_INITED, "DEC_NOT_INITED", },
	{ PNR_DEC_DECOMPRESS, "DEC_DECOMPRESS", },
	{ PNR_OBSOLETE_VERSION, "OBSOLETE_VERSION", },
	{ PNR_ENC_FILE_TOO_SMALL, "ENC_FILE_TOO_SMALL", },
	{ PNR_ENC_UNKNOWN_FILE, "ENC_UNKNOWN_FILE", },
	{ PNR_ENC_BAD_CHANNELS, "ENC_BAD_CHANNELS", },
	{ PNR_ENC_BAD_SAMPSIZE, "ENC_BAD_SAMPSIZE", },
	{ PNR_ENC_BAD_SAMPRATE, "ENC_BAD_SAMPRATE", },
	{ PNR_ENC_INVALID, "ENC_INVALID", },
	{ PNR_ENC_NO_OUTPUT_FILE, "ENC_NO_OUTPUT_FILE", },
	{ PNR_ENC_NO_INPUT_FILE, "ENC_NO_INPUT_FILE", },
	{ PNR_ENC_NO_OUTPUT_PERMISSIONS, "ENC_NO_OUTPUT_PERMISSIONS", },
	{ PNR_ENC_BAD_FILETYPE, "ENC_BAD_FILETYPE", },
	{ PNR_ENC_INVALID_VIDEO, "ENC_INVALID_VIDEO", },
	{ PNR_ENC_INVALID_AUDIO, "ENC_INVALID_AUDIO", },
	{ PNR_ENC_NO_VIDEO_CAPTURE, "ENC_NO_VIDEO_CAPTURE", },
	{ PNR_ENC_INVALID_VIDEO_CAPTURE, "ENC_INVALID_VIDEO_CAPTURE", },
	{ PNR_ENC_NO_AUDIO_CAPTURE, "ENC_NO_AUDIO_CAPTURE", },
	{ PNR_ENC_INVALID_AUDIO_CAPTURE, "ENC_INVALID_AUDIO_CAPTURE", },
	{ PNR_ENC_TOO_SLOW_FOR_LIVE, "ENC_TOO_SLOW_FOR_LIVE", },
	{ PNR_ENC_ENGINE_NOT_INITIALIZED, "ENC_ENGINE_NOT_INITIALIZED", },
	{ PNR_ENC_CODEC_NOT_FOUND, "ENC_CODEC_NOT_FOUND", },
	{ PNR_ENC_CODEC_NOT_INITIALIZED, "ENC_CODEC_NOT_INITIALIZED", },
	{ PNR_ENC_INVALID_INPUT_DIMENSIONS, "ENC_INVALID_INPUT_DIMENSIONS", },
	{ PNR_ENC_MESSAGE_IGNORED, "ENC_MESSAGE_IGNORED", },
	{ PNR_ENC_NO_SETTINGS, "ENC_NO_SETTINGS", },
	{ PNR_ENC_NO_OUTPUT_TYPES, "ENC_NO_OUTPUT_TYPES", },
	{ PNR_ENC_IMPROPER_STATE, "ENC_IMPROPER_STATE", },
	{ PNR_ENC_INVALID_SERVER, "ENC_INVALID_SERVER", },
	{ PNR_ENC_INVALID_TEMP_PATH, "ENC_INVALID_TEMP_PATH", },
	{ PNR_ENC_MERGE_FAIL, "ENC_MERGE_FAIL", },
	{ PNR_BIN_DATA_NOT_FOUND, "BIN_DATA_NOT_FOUND", },
	{ PNR_BIN_END_OF_DATA, "BIN_END_OF_DATA", },
	{ PNR_BIN_DATA_PURGED, "BIN_DATA_PURGED", },
	{ PNR_BIN_FULL, "BIN_FULL", },
	{ PNR_BIN_OFFSET_PAST_END, "BIN_OFFSET_PAST_END", },
	{ PNR_ENC_NO_ENCODED_DATA, "ENC_NO_ENCODED_DATA", },
	{ PNR_ENC_INVALID_DLL, "ENC_INVALID_DLL", },
	{ PNR_NOT_INDEXABLE, "NOT_INDEXABLE", },
	{ PNR_ENC_NO_BROWSER, "ENC_NO_BROWSER", },
	{ PNR_RMT_USAGE_ERROR, "RMT_USAGE_ERROR", },
	{ PNR_RMT_INVALID_ENDTIME, "RMT_INVALID_ENDTIME", },
	{ PNR_RMT_MISSING_INPUT_FILE, "RMT_MISSING_INPUT_FILE", },
	{ PNR_RMT_MISSING_OUTPUT_FILE, "RMT_MISSING_OUTPUT_FILE", },
	{ PNR_RMT_INPUT_EQUALS_OUTPUT_FILE, "RMT_INPUT_EQUALS_OUTPUT_FILE", },
	{ PNR_RMT_UNSUPPORTED_AUDIO_VERSION, "RMT_UNSUPPORTED_AUDIO_VERSION", },
	{ PNR_RMT_DIFFERENT_AUDIO, "RMT_DIFFERENT_AUDIO", },
	{ PNR_RMT_DIFFERENT_VIDEO, "RMT_DIFFERENT_VIDEO", },
	{ PNR_RMT_PASTE_MISSING_STREAM, "RMT_PASTE_MISSING_STREAM", },
	{ PNR_RMT_END_OF_STREAM, "RMT_END_OF_STREAM", },
	{ PNR_RMT_IMAGE_MAP_PARSE_ERROR, "RMT_IMAGE_MAP_PARSE_ERROR", },
	{ PNR_RMT_INVALID_IMAGEMAP_FILE, "RMT_INVALID_IMAGEMAP_FILE", },
	{ PNR_RMT_EVENT_PARSE_ERROR, "RMT_EVENT_PARSE_ERROR", },
	{ PNR_RMT_INVALID_EVENT_FILE, "RMT_INVALID_EVENT_FILE", },
	{ PNR_RMT_INVALID_OUTPUT_FILE, "RMT_INVALID_OUTPUT_FILE", },
	{ PNR_RMT_INVALID_DURATION, "RMT_INVALID_DURATION", },
	{ PNR_RMT_NO_DUMP_FILES, "RMT_NO_DUMP_FILES", },
	{ PNR_RMT_NO_EVENT_DUMP_FILE, "RMT_NO_EVENT_DUMP_FILE", },
	{ PNR_RMT_NO_IMAP_DUMP_FILE, "RMT_NO_IMAP_DUMP_FILE", },
	{ PNR_RMT_NO_DATA, "RMT_NO_DATA", },
	{ PNR_PROP_NOT_FOUND, "PROP_NOT_FOUND", },
	{ PNR_PROP_NOT_COMPOSITE, "PROP_NOT_COMPOSITE", },
	{ PNR_PROP_DUPLICATE, "PROP_DUPLICATE", },
	{ PNR_PROP_TYPE_MISMATCH, "PROP_TYPE_MISMATCH", },
	{ PNR_PROP_ACTIVE, "PROP_ACTIVE", },
	{ PNR_PROP_INACTIVE, "PROP_INACTIVE", },
	{ PNR_COULDNOTINITCORE, "COULDNOTINITCORE", },
	{ PNR_PERFECTPLAY_NOT_SUPPORTED, "PERFECTPLAY_NOT_SUPPORTED", },
	{ PNR_NO_LIVE_PERFECTPLAY, "NO_LIVE_PERFECTPLAY", },
	{ PNR_PERFECTPLAY_NOT_ALLOWED, "PERFECTPLAY_NOT_ALLOWED", },
	{ PNR_NO_CODECS, "NO_CODECS", },
	{ PNR_SLOW_MACHINE, "SLOW_MACHINE", },
	{ PNR_FORCE_PERFECTPLAY, "FORCE_PERFECTPLAY", },
	{ PNR_INVALID_HTTP_PROXY_HOST, "INVALID_HTTP_PROXY_HOST", },
	{ PNR_INVALID_METAFILE, "INVALID_METAFILE", },
	{ PNR_BROWSER_LAUNCH, "BROWSER_LAUNCH", },
#define	PNR_RESOURCE_NOT_CACHED		MAKE_PN_RESULT(1,SS_RSC,1)
	{ PNR_RESOURCE_NOT_FOUND, "RESOURCE_NOT_FOUND", },
	{ PNR_RESOURCE_CLOSE_FILE_FIRST, "RESOURCE_CLOSE_FILE_FIRST", },
	{ PNR_RESOURCE_NODATA, "RESOURCE_NODATA", },
	{ PNR_RESOURCE_BADFILE, "RESOURCE_BADFILE", },
	{ PNR_RESOURCE_PARTIALCOPY, "RESOURCE_PARTIALCOPY", },
	{ PNR_PPV_NO_USER, "PPV_NO_USER", },
	{ PNR_PPV_GUID_READ_ONLY, "PPV_GUID_READ_ONLY", },
	{ PNR_PPV_GUID_COLLISION, "PPV_GUID_COLLISION", },
	{ PNR_REGISTER_GUID_EXISTS, "REGISTER_GUID_EXISTS", },
	{ PNR_PPV_AUTHORIZATION_FAILED, "PPV_AUTHORIZATION_FAILED", },
	{ PNR_PPV_OLD_PLAYER, "PPV_OLD_PLAYER", },
	{ PNR_PPV_ACCOUNT_LOCKED, "PPV_ACCOUNT_LOCKED", },
	{ PNR_UPG_AUTH_FAILED, "UPG_AUTH_FAILED", },
	{ PNR_UPG_CERT_AUTH_FAILED, "UPG_CERT_AUTH_FAILED", },
	{ PNR_UPG_CERT_EXPIRED, "UPG_CERT_EXPIRED", },
	{ PNR_UPG_CERT_REVOKED, "UPG_CERT_REVOKED", },
	{ PNR_UPG_RUP_BAD, "UPG_RUP_BAD", },
	{ PNR_AUTOCFG_SUCCESS, "AUTOCFG_SUCCESS", },
	{ PNR_AUTOCFG_FAILED, "AUTOCFG_FAILED", },
	{ PNR_AUTOCFG_ABORT, "AUTOCFG_ABORT", },
	{ PNR_FAILED, "FAILED", },
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

/* ----------------------------------------------------- */

/* Declarations for objects of type RMBuildEngine */

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IRMABuildEngine *buildEngine;
} RMBEobject;

staticforward PyTypeObject RMBEtype;

static RMBEobject *
newRMBEobject()
{
	RMBEobject *self;
	
	self = PyObject_NEW(RMBEobject, &RMBEtype);
	if (self == NULL)
		return NULL;
	self->buildEngine = NULL;
	/* XXXX Add your own initializers here */
	return self;
}


/* ---------------------------------------------------------------- */

/* Declarations for objects of type RMInputPin */

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IRMAInputPin *inputPin;
} RMIPobject;

staticforward PyTypeObject RMIPtype;

static RMIPobject *
newRMIPobject()
{
	RMIPobject *self;
	
	self = PyObject_NEW(RMIPobject, &RMIPtype);
	if (self == NULL)
		return NULL;
	/* XXXX Add your own initializers here */
	self->inputPin = NULL;
	return self;
}


/* ---------------------------------------------------------------- */

/* Declarations for objects of type RMVideoInputPinFeedback */

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IRMAVideoInputPinFeedback *videoInputPinFeedback;
} RMVIPFobject;

staticforward PyTypeObject RMVIPFtype;

static RMVIPFobject *
newRMVIPFobject()
{
	RMVIPFobject *self;
	
	self = PyObject_NEW(RMVIPFobject, &RMVIPFtype);
	if (self == NULL)
		return NULL;
	/* XXXX Add your own initializers here */
	self->videoInputPinFeedback = NULL;
	return self;
}


/* ---------------------------------------------------------------- */

/* Declarations for objects of type RMTargetSettings */

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IRMATargetSettings *targetSettings;
} RMTSobject;

staticforward PyTypeObject RMTStype;

static RMTSobject *
newRMTSobject()
{
	RMTSobject *self;
	
	self = PyObject_NEW(RMTSobject, &RMTStype);
	if (self == NULL)
		return NULL;
	/* XXXX Add your own initializers here */
	self->targetSettings = NULL;
	return self;
}


/* ---------------------------------------------------------------- */

/* Declarations for objects of type RMClipProperties */

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IRMAClipProperties *clipProperties;
} RMCPobject;

staticforward PyTypeObject RMCPtype;

static RMCPobject *
newRMCPobject()
{
	RMCPobject *self;
	
	self = PyObject_NEW(RMCPobject, &RMCPtype);
	if (self == NULL)
		return NULL;
	/* XXXX Add your own initializers here */
	self->clipProperties = NULL;
	return self;
}


/* ---------------------------------------------------------------- */

/* Declarations for objects of type RMBroadcastServerProperties */

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IRMABroadcastServerProperties *broadcastServerProperties;
} RMBSPobject;

staticforward PyTypeObject RMBSPtype;

static RMBSPobject *
newRMBSPobject()
{
	RMBSPobject *self;
	
	self = PyObject_NEW(RMBSPobject, &RMBSPtype);
	if (self == NULL)
		return NULL;
	/* XXXX Add your own initializers here */
	self->broadcastServerProperties = NULL;
	return self;
}


/* ---------------------------------------------------------------- */

/* Declarations for objects of type RMPinProperties */

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IRMAPinProperties *pinProperties;
} RMPPobject;

staticforward PyTypeObject RMPPtype;

static RMPPobject *
newRMPPobject()
{
	RMPPobject *self;
	
	self = PyObject_NEW(RMPPobject, &RMPPtype);
	if (self == NULL)
		return NULL;
	/* XXXX Add your own initializers here */
	self->pinProperties = NULL;
	return self;
}


/* ---------------------------------------------------------------- */

/* Declarations for objects of type RMMediaSample */

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IRMAMediaSample *mediaSample;
} RMMSobject;

staticforward PyTypeObject RMMStype;

static RMMSobject *
newRMMSobject()
{
	RMMSobject *self;
	
	self = PyObject_NEW(RMMSobject, &RMMStype);
	if (self == NULL)
		return NULL;
	/* XXXX Add your own initializers here */
	self->mediaSample = NULL;
	return self;
}


/* ---------------------------------------------------------------- */

/* Declarations for objects of type RMTargetAudienceManager */

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IRMATargetAudienceManager *targetAudienceManager;
} RMTAMobject;

staticforward PyTypeObject RMTAMtype;

static RMTAMobject *
newRMTAMobject()
{
	RMTAMobject *self;
	
	self = PyObject_NEW(RMTAMobject, &RMTAMtype);
	if (self == NULL)
		return NULL;
	/* XXXX Add your own initializers here */
	self->targetAudienceManager = NULL;
	return self;
}


/* ---------------------------------------------------------------- */

/* Declarations for objects of type RMTargetAudienceInfo */

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IRMATargetAudienceInfo *targetAudienceInfo;
} RMTAIobject;

staticforward PyTypeObject RMTAItype;

static RMTAIobject *
newRMTAIobject()
{
	RMTAIobject *self;
	
	self = PyObject_NEW(RMTAIobject, &RMTAItype);
	if (self == NULL)
		return NULL;
	/* XXXX Add your own initializers here */
	self->targetAudienceInfo = NULL;
	return self;
}


/* ---------------------------------------------------------------- */

/* Declarations for objects of type RMCodecInfoManager */

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IRMACodecInfoManager *codecInfoManager;
} RMCIMobject;

staticforward PyTypeObject RMCIMtype;

static RMCIMobject *
newRMCIMobject()
{
	RMCIMobject *self;
	
	self = PyObject_NEW(RMCIMobject, &RMCIMtype);
	if (self == NULL)
		return NULL;
	/* XXXX Add your own initializers here */
	self->codecInfoManager = NULL;
	return self;
}


/* ---------------------------------------------------------------- */

/* Declarations for objects of type PNCodecCookie */

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	PNCODECCOOKIE codecCookie;
} RMCCobject;

staticforward PyTypeObject RMCCtype;

static RMCCobject *
newRMCCobject()
{
	RMCCobject *self;
	
	self = PyObject_NEW(RMCCobject, &RMCCtype);
	if (self == NULL)
		return NULL;
	/* XXXX Add your own initializers here */
	self->codecCookie.codecID = 0;
	self->codecCookie.flavorID = 0;
	return self;
}


/* ---------------------------------------------------------------- */

/* Declarations for objects of type RMCodecInfo */

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IRMACodecInfo *codecInfo;
} RMCIobject;

staticforward PyTypeObject RMCItype;

static RMCIobject *
newRMCIobject()
{
	RMCIobject *self;
	
	self = PyObject_NEW(RMCIobject, &RMCItype);
	if (self == NULL)
		return NULL;
	self->codecInfo = NULL;
	/* XXXX Add your own initializers here */
	return self;
}



#define EMPTYARG /**/
#define GETVALUE(ptr,funcname,type,cvfunc,cast,ref)    			\
	PN_RESULT res;							\
	type val;							\
	if (!PyArg_ParseTuple(args, ""))				\
		return NULL;						\
	res = (ptr)->funcname(ref val);					\
	if (!SUCCEEDED(res)) {						\
		seterror(#funcname, res);				\
		return NULL;						\
	}								\
	return cvfunc(cast val)
#define SETVALUE(ptr,funcname,cast,ctype,fmt)				\
	PN_RESULT res;							\
	ctype val;							\
	if (!PyArg_ParseTuple(args, fmt, &val))				\
		return NULL;						\
	res = (ptr)->funcname(cast val);				\
	if (!SUCCEEDED(res)) {						\
		seterror(#funcname, res);				\
		return NULL;						\
	}								\
	Py_INCREF(Py_None);						\
	return Py_None
#define CALLFUNC(ptr,funcname)						\
	PN_RESULT res;							\
	if (!PyArg_ParseTuple(args, ""))				\
		return NULL;						\
	res = (ptr)->funcname();					\
	if (!SUCCEEDED(res)) {						\
		seterror(#funcname, res);				\
		return NULL;						\
	}								\
	Py_INCREF(Py_None);						\
	return Py_None
#define GETIVALUE(ptr,funcname,type) GETVALUE(ptr,funcname,type,PyInt_FromLong,(long),&)
#define SETIVALUE(ptr,funcname,type) SETVALUE(ptr,funcname,(type),long,"l")
#define GETFVALUE(ptr,funcname) GETVALUE(ptr,funcname,float,PyFloat_FromDouble,(double),&)
#define SETFVALUE(ptr,funcname) SETVALUE(ptr,funcname,(float),float,"f")
#define GETSVALUE(ptr,funcname)						\
	PN_RESULT res;							\
	char val[APP_MAX_PATH+1];					\
	if (!PyArg_ParseTuple(args, ""))				\
		return NULL;						\
	res = (ptr)->funcname(val, APP_MAX_PATH);			\
	if (!SUCCEEDED(res)) {						\
		seterror(#funcname, res);				\
		return NULL;						\
	}								\
	return PyString_FromString(val)
#define SETSVALUE(ptr,funcname) SETVALUE(ptr,funcname,(char *),char *,"s")
#define ENUMERATE(ptr,funcname,newobj,query,ptype,field,ref)		\
	IRMAEnumeratorIUnknown* enumerator = NULL;			\
	IUnknown *tempUnk;						\
	UINT32 i;							\
	UINT32 n;							\
	PyObject *obj = NULL;						\
	ptype *v = NULL;						\
	PN_RESULT res;							\
	if (!PyArg_ParseTuple(args, ""))				\
		return NULL;						\
	res = (ptr)->funcname(ref enumerator);				\
	if (!SUCCEEDED(res)) {						\
		seterror(#funcname, res);				\
		return NULL;						\
	}								\
	res = enumerator->GetCount(&n);					\
	res = enumerator->First(&tempUnk);				\
	if (!SUCCEEDED(res)) {						\
		seterror("First", res);					\
		goto error;						\
	}								\
	obj = PyList_New((int) n);					\
	if (obj == NULL)						\
		goto error;						\
	for (i = 0; i < n; i++) {					\
		v = newobj();						\
		res = tempUnk->QueryInterface(query, (void **) &v->field); \
		PN_RELEASE(tempUnk);					\
		if (!SUCCEEDED(res)) {					\
			seterror("QueryInterface", res);		\
			goto error;					\
		}							\
		PyList_SetItem(obj, i, (PyObject *) v);			\
		Py_DECREF((PyObject *) v); v = NULL;			\
		res = enumerator->Next(&tempUnk);			\
		if (!SUCCEEDED(res)) {					\
			seterror("Next", res);				\
			goto error;					\
		}							\
	}								\
	PN_RELEASE(enumerator);						\
	return obj;							\
  error:								\
	Py_XDECREF(obj);						\
	Py_XDECREF((PyObject *) v);					\
	PN_RELEASE(enumerator);						\
	return NULL

/* ---------------------------------------------------------------- */

static char RMBE_GetPins__doc__[] = 
""
;

static PyObject *
RMBE_GetPins(RMBEobject *self, PyObject *args)
{
	ENUMERATE(self->buildEngine, GetPinEnumerator, newRMIPobject, IID_IRMAInputPin, RMIPobject, inputPin, &);
}


static char RMBE_GetClipProperties__doc__[] = 
""
;

static PyObject *
RMBE_GetClipProperties(RMBEobject *self, PyObject *args)
{
	RMCPobject *v;
	PN_RESULT res;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	v = newRMCPobject();
	res = self->buildEngine->GetClipProperties(&v->clipProperties);
	if (!SUCCEEDED(res)) {
		seterror("GetClipProperties", res);
		v->clipProperties = NULL; // just to be sure...
		Py_DECREF(v);
		return NULL;
	}
	return (PyObject *) v;
}


static char RMBE_SetClipProperties__doc__[] = 
""
;

static PyObject *
RMBE_SetClipProperties(RMBEobject *self, PyObject *args)
{
	PN_RESULT res;
	RMCPobject *val;

	if (!PyArg_ParseTuple(args, "O!", &RMCPtype, &val))
		return NULL;
	res = self->buildEngine->SetClipProperties(val->clipProperties);
	if (!SUCCEEDED(res)) {
		seterror("SetClipProperties", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMBE_GetTargetSettings__doc__[] = 
""
;

static PyObject *
RMBE_GetTargetSettings(RMBEobject *self, PyObject *args)
{
	RMTSobject *v;
	PN_RESULT res;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	v = newRMTSobject();
	res = self->buildEngine->GetTargetSettings(&v->targetSettings);
	if (!SUCCEEDED(res)) {
		seterror("GetTargetSettings", res);
		v->targetSettings = NULL; // just to be sure...
		Py_DECREF(v);
		return NULL;
	}
	return (PyObject *) v;
}


static char RMBE_SetTargetSettings__doc__[] = 
""
;

static PyObject *
RMBE_SetTargetSettings(RMBEobject *self, PyObject *args)
{
	PyObject *t;
	PN_RESULT res;

	if (!PyArg_ParseTuple(args, "O!", &RMTStype, &t))
		return NULL;
	res = self->buildEngine->SetTargetSettings(((RMTSobject *) t)->targetSettings);
	if (!SUCCEEDED(res)) {
		seterror("SetTargetSettings", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMBE_GetRealTimeEncoding__doc__[] = 
""
;

static PyObject *
RMBE_GetRealTimeEncoding(RMBEobject *self, PyObject *args)
{
	GETIVALUE(self->buildEngine, GetRealTimeEncoding, BOOL);
}


static char RMBE_SetRealTimeEncoding__doc__[] = 
""
;

static PyObject *
RMBE_SetRealTimeEncoding(RMBEobject *self, PyObject *args)
{
	SETIVALUE(self->buildEngine, SetRealTimeEncoding, BOOL);
}


static char RMBE_GetDoMultiRateEncoding__doc__[] = 
""
;

static PyObject *
RMBE_GetDoMultiRateEncoding(RMBEobject *self, PyObject *args)
{
	GETIVALUE(self->buildEngine, GetDoMultiRateEncoding, BOOL);
}


static char RMBE_SetDoMultiRateEncoding__doc__[] = 
""
;

static PyObject *
RMBE_SetDoMultiRateEncoding(RMBEobject *self, PyObject *args)
{
	SETIVALUE(self->buildEngine, SetDoMultiRateEncoding, BOOL);
}


static char RMBE_ResetAllOutputMimeTypes__doc__[] = 
""
;

static PyObject *
RMBE_ResetAllOutputMimeTypes(RMBEobject *self, PyObject *args)
{
	CALLFUNC(self->buildEngine, ResetAllOutputMimeTypes);
}


static char RMBE_PrepareToEncode__doc__[] = 
""
;

static PyObject *
RMBE_PrepareToEncode(RMBEobject *self, PyObject *args)
{
	PN_RESULT res;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	res = self->buildEngine->PrepareToEncode();
	switch (res) {
	case PNR_OK:
		Py_INCREF(Py_None);
		return Py_None;
	case PNR_ENC_BAD_CHANNELS:
		PyErr_SetString(ErrorObject, "PrepareToEncode: incorrect number of audio input channels specified");
		return NULL;
	case PNR_ENC_IMPROPER_STATE:
		PyErr_SetString(ErrorObject, "PrepareToEncode: prepare to encode cannor be called during encoding");
		return NULL;
	case PNR_ENC_INVALID_SERVER:
		PyErr_SetString(ErrorObject, "PrepareToEncode: specified server is invalid");
		return NULL;
	case PNR_ENC_INVALID_TEMP_PATH:
		PyErr_SetString(ErrorObject, "PrepareToEncode: current temp directory is invalid");
		return NULL;
	case PNR_ENC_NO_OUTPUT_TYPES:
		PyErr_SetString(ErrorObject, "PrepareToEncode: no output mime types specified");
		return NULL;
	case PNR_ENC_NO_OUTPUT_FILE:
		PyErr_SetString(ErrorObject, "PrepareToEncode: no output file or server specified");
		return NULL;
	case PNR_NOT_INITIALIZED:
		PyErr_SetString(ErrorObject, "PrepareToEncode: build engine not properly initialized with necessary objects");
		return NULL;
	default:
		seterror("PrepareToEncode", res);
		return NULL;
	}
}


static char RMBE_DoneEncoding__doc__[] = 
""
;

static PyObject *
RMBE_DoneEncoding(RMBEobject *self, PyObject *args)
{
	PN_RESULT res;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	res = self->buildEngine->DoneEncoding();
	switch (res) {
	case PNR_OK:
		Py_INCREF(Py_None);
		return Py_None;
	case PNR_ENC_MERGE_FAIL:
		PyErr_SetString(ErrorObject, "DoneEncoding: unable to create destination");
		return NULL;
	case PNR_ENC_NO_ENCODED_DATA:
		PyErr_SetString(ErrorObject, "DoneEncoding: no data was encoded");
		return NULL;
	default:
		seterror("DoneEncoding", res);
		return NULL;
	}
}


static char RMBE_CancelEncoding__doc__[] = 
""
;

static PyObject *
RMBE_CancelEncoding(RMBEobject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	self->buildEngine->CancelEncoding();
	Py_INCREF(Py_None);
	return Py_None;
}


static struct PyMethodDef RMBE_methods[] = {
	{"GetPins",	(PyCFunction)RMBE_GetPins,	METH_VARARGS,	RMBE_GetPins__doc__},
 {"GetClipProperties",	(PyCFunction)RMBE_GetClipProperties,	METH_VARARGS,	RMBE_GetClipProperties__doc__},
 {"SetClipProperties",	(PyCFunction)RMBE_SetClipProperties,	METH_VARARGS,	RMBE_SetClipProperties__doc__},
 {"GetTargetSettings",	(PyCFunction)RMBE_GetTargetSettings,	METH_VARARGS,	RMBE_GetTargetSettings__doc__},
 {"SetTargetSettings",	(PyCFunction)RMBE_SetTargetSettings,	METH_VARARGS,	RMBE_SetTargetSettings__doc__},
 {"GetRealTimeEncoding",	(PyCFunction)RMBE_GetRealTimeEncoding,	METH_VARARGS,	RMBE_GetRealTimeEncoding__doc__},
 {"SetRealTimeEncoding",	(PyCFunction)RMBE_SetRealTimeEncoding,	METH_VARARGS,	RMBE_SetRealTimeEncoding__doc__},
 {"GetDoMultiRateEncoding",	(PyCFunction)RMBE_GetDoMultiRateEncoding,	METH_VARARGS,	RMBE_GetDoMultiRateEncoding__doc__},
 {"SetDoMultiRateEncoding",	(PyCFunction)RMBE_SetDoMultiRateEncoding,	METH_VARARGS,	RMBE_SetDoMultiRateEncoding__doc__},
 {"ResetAllOutputMimeTypes",	(PyCFunction)RMBE_ResetAllOutputMimeTypes,	METH_VARARGS,	RMBE_ResetAllOutputMimeTypes__doc__},
 {"PrepareToEncode",	(PyCFunction)RMBE_PrepareToEncode,	METH_VARARGS,	RMBE_PrepareToEncode__doc__},
 {"DoneEncoding",	(PyCFunction)RMBE_DoneEncoding,	METH_VARARGS,	RMBE_DoneEncoding__doc__},
 {"CancelEncoding",	(PyCFunction)RMBE_CancelEncoding,	METH_VARARGS,	RMBE_CancelEncoding__doc__},
 
	{NULL,		NULL}		/* sentinel */
};

/* ---------- */


static void
RMBE_dealloc(RMBEobject *self)
{
	/* XXXX Add your own cleanup code here */
	if (self->buildEngine) {
		PN_RELEASE(self->buildEngine);
		self->buildEngine = NULL;
	}
	PyMem_DEL(self);
}

static PyObject *
RMBE_getattr(RMBEobject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(RMBE_methods, (PyObject *)self, name);
}

static char RMBEtype__doc__[] = 
""
;

static PyTypeObject RMBEtype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"RMBuildEngine",			/*tp_name*/
	sizeof(RMBEobject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)RMBE_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)RMBE_getattr,	/*tp_getattr*/
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
	RMBEtype__doc__ /* Documentation string */
};

/* End of code for RMBuildEngine objects */
/* -------------------------------------------------------- */


static char RMIP_GetOutputMimeType__doc__[] = 
""
;

static PyObject *
RMIP_GetOutputMimeType(RMIPobject *self, PyObject *args)
{
	GETSVALUE(self->inputPin, GetOutputMimeType);
}


static char RMIP_GetPinProperties__doc__[] = 
""
;

static PyObject *
RMIP_GetPinProperties(RMIPobject *self, PyObject *args)
{
	RMPPobject *v;
	PN_RESULT res;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	v = newRMPPobject();
	res = self->inputPin->GetPinProperties(&v->pinProperties);
	if (!SUCCEEDED(res)) {
		seterror("GetPinProperties", res);
		v->pinProperties = NULL; // just to be sure...
		Py_DECREF(v);
		return NULL;
	}
	return (PyObject *) v;
}


static char RMIP_SetPinProperties__doc__[] = 
""
;

static PyObject *
RMIP_SetPinProperties(RMIPobject *self, PyObject *args)
{
	RMPPobject *v;
	PN_RESULT res;

	if (!PyArg_ParseTuple(args, "O!", &RMPPtype, (PyObject *) &v))
		return NULL;
	res = self->inputPin->SetPinProperties(v->pinProperties);
	if (!SUCCEEDED(res)) {
		seterror("SetPinProperties", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMIP_Encode__doc__[] = 
""
;

static PyObject *
RMIP_Encode(RMIPobject *self, PyObject *args)
{
	PN_RESULT res;
	RMMSobject *val;

	if (!PyArg_ParseTuple(args, "O!", &RMMStype, &val))
		return NULL;
	res = self->inputPin->Encode(val->mediaSample);
	if (!SUCCEEDED(res)) {
		seterror("Encode", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMIP_GetPreferredAudioSourceProperties__doc__[] = 
""
;

static PyObject *
RMIP_GetPreferredAudioSourceProperties(RMIPobject *self, PyObject *args)
{
	PN_RESULT res;
	UINT32 sps, bps, nc;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	res = ((IRMAAudioInputPin *) self->inputPin)->GetPreferredAudioSourceProperties(&sps, &bps, &nc);
	if (!SUCCEEDED(res)) {
		seterror("GetPreferredAudioSourceProperties", res);
		return NULL;
	}
	return Py_BuildValue("(lll)", (long) sps, (long) bps, (long) nc);
}


static char RMIP_GetSuggestedInputSize__doc__[] = 
""
;

static PyObject *
RMIP_GetSuggestedInputSize(RMIPobject *self, PyObject *args)
{
	GETIVALUE((IRMAAudioInputPin *) self->inputPin, GetSuggestedInputSize, UINT32);
}


static char RMIP_GetClippingSize__doc__[] = 
""
;

static PyObject *
RMIP_GetClippingSize(RMIPobject *self, PyObject *args)
{
	PN_RESULT res;
	UINT32 left, top, width, height;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	res = ((IRMAVideoInputPin *) self->inputPin)->GetClippingSize(&left, &top, &width, &height);
	if (!SUCCEEDED(res)) {
		seterror("GetClippingSize", res);
		return NULL;
	}
	return Py_BuildValue("(llll)", (long) left, (long) top, (long) width, (long) height);
}


static char RMIP_GetPreferredInputFrameRate__doc__[] = 
""
;

static PyObject *
RMIP_GetPreferredInputFrameRate(RMIPobject *self, PyObject *args)
{
	GETFVALUE((IRMAVideoInputPin *)self->inputPin, GetPreferredInputFrameRate);
}


static struct PyMethodDef RMIP_methods[] = {
	{"GetOutputMimeType",	(PyCFunction)RMIP_GetOutputMimeType,	METH_VARARGS,	RMIP_GetOutputMimeType__doc__},
 {"GetPinProperties",	(PyCFunction)RMIP_GetPinProperties,	METH_VARARGS,	RMIP_GetPinProperties__doc__},
 {"SetPinProperties",	(PyCFunction)RMIP_SetPinProperties,	METH_VARARGS,	RMIP_SetPinProperties__doc__},
 {"Encode",	(PyCFunction)RMIP_Encode,	METH_VARARGS,	RMIP_Encode__doc__},
 {"GetPreferredAudioSourceProperties",	(PyCFunction)RMIP_GetPreferredAudioSourceProperties,	METH_VARARGS,	RMIP_GetPreferredAudioSourceProperties__doc__},
 {"GetSuggestedInputSize",	(PyCFunction)RMIP_GetSuggestedInputSize,	METH_VARARGS,	RMIP_GetSuggestedInputSize__doc__},
 {"GetClippingSize",	(PyCFunction)RMIP_GetClippingSize,	METH_VARARGS,	RMIP_GetClippingSize__doc__},
 {"GetPreferredInputFrameRate",	(PyCFunction)RMIP_GetPreferredInputFrameRate,	METH_VARARGS,	RMIP_GetPreferredInputFrameRate__doc__},
 
	{NULL,		NULL}		/* sentinel */
};

/* ---------- */


static void
RMIP_dealloc(RMIPobject *self)
{
	/* XXXX Add your own cleanup code here */
	if (self->inputPin) {
		PN_RELEASE(self->inputPin);
		self->inputPin = NULL;
	}
	PyMem_DEL(self);
}

static PyObject *
RMIP_getattr(RMIPobject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(RMIP_methods, (PyObject *)self, name);
}

static char RMIPtype__doc__[] = 
""
;

static PyTypeObject RMIPtype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"RMInputPin",			/*tp_name*/
	sizeof(RMIPobject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)RMIP_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)RMIP_getattr,	/*tp_getattr*/
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
	RMIPtype__doc__ /* Documentation string */
};

/* End of code for RMInputPin objects */
/* -------------------------------------------------------- */


static char RMVIPF_GetEncodeDecision__doc__[] =
""
;

static PyObject *
RMVIPF_GetEncodeDecision(RMVIPFobject *self, PyObject *args)
{
	PN_RESULT res;
	long timestamp;
	BOOL doEncode;

	if (!PyArg_ParseTuple(args, "l", &timestamp))
		return NULL;
	res = self->videoInputPinFeedback->GetEncodeDecision(timestamp, &doEncode);
	if (!SUCCEEDED(res)) {
		seterror("GetEncodeDecisionfailed", res);
		return NULL;
	}
	return PyInt_FromLong((long) doEncode);
}

static struct PyMethodDef RMVIPF_methods[] = {
	{"GetEncodeDecision",	(PyCFunction)RMVIPF_GetEncodeDecision,	METH_VARARGS,	RMVIPF_GetEncodeDecision__doc__},
 
	{NULL,		NULL}		/* sentinel */
};

/* ---------- */


static void
RMVIPF_dealloc(RMVIPFobject *self)
{
	/* XXXX Add your own cleanup code here */
	if (self->videoInputPinFeedback) {
		PN_RELEASE(self->videoInputPinFeedback);
		self->videoInputPinFeedback = NULL;
	}
	PyMem_DEL(self);
}

static PyObject *
RMVIPF_getattr(RMVIPFobject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(RMVIPF_methods, (PyObject *)self, name);
}

static char RMVIPFtype__doc__[] = 
""
;

static PyTypeObject RMVIPFtype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"RMVideoInputPinFeedback",			/*tp_name*/
	sizeof(RMVIPFobject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)RMVIPF_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)RMVIPF_getattr,	/*tp_getattr*/
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
	RMVIPFtype__doc__ /* Documentation string */
};

/* End of code for RMVideoInputPinFeedback objects */
/* -------------------------------------------------------- */


static char RMTS_GetType__doc__[] = 
""
;

static PyObject *
RMTS_GetType(RMTSobject *self, PyObject *args)
{
	GETIVALUE(self->targetSettings, GetType, UINT32);
}


static char RMTS_AddTargetAudience__doc__[] = 
""
;

static PyObject *
RMTS_AddTargetAudience(RMTSobject *self, PyObject *args)
{
	SETIVALUE((IRMABasicTargetSettings *) self->targetSettings, AddTargetAudience, UINT32);
}


static char RMTS_RemoveTargetAudience__doc__[] = 
""
;

static PyObject *
RMTS_RemoveTargetAudience(RMTSobject *self, PyObject *args)
{
	SETIVALUE((IRMABasicTargetSettings *) self->targetSettings, RemoveTargetAudience, UINT32);
}


static char RMTS_RemoveAllTargetAudiences__doc__[] = 
""
;

static PyObject *
RMTS_RemoveAllTargetAudiences(RMTSobject *self, PyObject *args)
{
	CALLFUNC((IRMABasicTargetSettings *) self->targetSettings, RemoveAllTargetAudiences);
}


static char RMTS_GetTargetAudienceCount__doc__[] = 
""
;

static PyObject *
RMTS_GetTargetAudienceCount(RMTSobject *self, PyObject *args)
{
	PN_RESULT res;
	UINT32 count;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	res = ((IRMABasicTargetSettings *) self->targetSettings)->GetTargetAudienceCount(&count);
	if (!SUCCEEDED(res)) {
		seterror("GetTargetAudienceCount", res);
		return NULL;
	}
	return PyInt_FromLong((long) count);
}


static char RMTS_GetNthTargetAudience__doc__[] = 
""
;

static PyObject *
RMTS_GetNthTargetAudience(RMTSobject *self, PyObject *args)
{
	long index;
	UINT32 count;
	PN_RESULT res;

	if (!PyArg_ParseTuple(args, "l", &index))
		return NULL;
	res = ((IRMABasicTargetSettings *) self->targetSettings)->GetNthTargetAudience((UINT32) index, &count);
	if (!SUCCEEDED(res)) {
		seterror("GetNthTargetAudience", res);
		return NULL;
	}
	return PyInt_FromLong((long) count);
}


static char RMTS_GetAudioContent__doc__[] = 
""
;

static PyObject *
RMTS_GetAudioContent(RMTSobject *self, PyObject *args)
{
	PN_RESULT res;
	UINT32 content;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	res = ((IRMABasicTargetSettings *) self->targetSettings)->GetAudioContent(&content);
	if (!SUCCEEDED(res)) {
		seterror("GetAudioContent", res);
		return NULL;
	}
	return PyInt_FromLong((long) content);
}


static char RMTS_SetAudioContent__doc__[] = 
""
;

static PyObject *
RMTS_SetAudioContent(RMTSobject *self, PyObject *args)
{
	SETIVALUE((IRMABasicTargetSettings *) self->targetSettings, SetAudioContent, UINT32);
}


static char RMTS_GetVideoQuality__doc__[] = 
""
;

static PyObject *
RMTS_GetVideoQuality(RMTSobject *self, PyObject *args)
{
	PN_RESULT res;
	UINT32 quality;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	res = ((IRMABasicTargetSettings *) self->targetSettings)->GetVideoQuality(&quality);
	if (!SUCCEEDED(res)) {
		seterror("GetVideoQuality", res);
		return NULL;
	}
	return PyInt_FromLong((long) quality);
}


static char RMTS_SetVideoQuality__doc__[] = 
""
;

static PyObject *
RMTS_SetVideoQuality(RMTSobject *self, PyObject *args)
{
	SETIVALUE((IRMABasicTargetSettings *) self->targetSettings, SetVideoQuality, UINT32);
}


static char RMTS_GetPlayerCompatibility__doc__[] = 
""
;

static PyObject *
RMTS_GetPlayerCompatibility(RMTSobject *self, PyObject *args)
{
	PN_RESULT res;
	UINT32 version;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	res = ((IRMABasicTargetSettings *) self->targetSettings)->GetPlayerCompatibility(&version);
	if (!SUCCEEDED(res)) {
		seterror("GetPlayerCompatibility", res);
		return NULL;
	}
	return PyInt_FromLong((long) version);
}


static char RMTS_SetPlayerCompatibility__doc__[] = 
""
;

static PyObject *
RMTS_SetPlayerCompatibility(RMTSobject *self, PyObject *args)
{
	SETIVALUE((IRMABasicTargetSettings *) self->targetSettings, SetPlayerCompatibility, UINT32);
}


static char RMTS_GetEmphasizeAudio__doc__[] = 
""
;

static PyObject *
RMTS_GetEmphasizeAudio(RMTSobject *self, PyObject *args)
{
	GETIVALUE((IRMABasicTargetSettings *) self->targetSettings, GetEmphasizeAudio, BOOL);
}


static char RMTS_SetEmphasizeAudio__doc__[] = 
""
;

static PyObject *
RMTS_SetEmphasizeAudio(RMTSobject *self, PyObject *args)
{
	SETIVALUE((IRMABasicTargetSettings *) self->targetSettings, SetEmphasizeAudio, BOOL);
}


static char RMTS_GetDoAudioOnlyMultimedia__doc__[] = 
""
;

static PyObject *
RMTS_GetDoAudioOnlyMultimedia(RMTSobject *self, PyObject *args)
{
	GETIVALUE((IRMABasicTargetSettings *) self->targetSettings, GetDoAudioOnlyMultimedia, BOOL);
}


static char RMTS_SetDoAudioOnlyMultimedia__doc__[] = 
""
;

static PyObject *
RMTS_SetDoAudioOnlyMultimedia(RMTSobject *self, PyObject *args)
{
	SETIVALUE((IRMABasicTargetSettings *) self->targetSettings, SetDoAudioOnlyMultimedia, BOOL);
}


static struct PyMethodDef RMTS_methods[] = {
	{"GetType",	(PyCFunction)RMTS_GetType,	METH_VARARGS,	RMTS_GetType__doc__},
 {"AddTargetAudience",	(PyCFunction)RMTS_AddTargetAudience,	METH_VARARGS,	RMTS_AddTargetAudience__doc__},
 {"RemoveTargetAudience",	(PyCFunction)RMTS_RemoveTargetAudience,	METH_VARARGS,	RMTS_RemoveTargetAudience__doc__},
 {"RemoveAllTargetAudiences",	(PyCFunction)RMTS_RemoveAllTargetAudiences,	METH_VARARGS,	RMTS_RemoveAllTargetAudiences__doc__},
 {"GetTargetAudienceCount",	(PyCFunction)RMTS_GetTargetAudienceCount,	METH_VARARGS,	RMTS_GetTargetAudienceCount__doc__},
 {"GetNthTargetAudience",	(PyCFunction)RMTS_GetNthTargetAudience,	METH_VARARGS,	RMTS_GetNthTargetAudience__doc__},
 {"GetAudioContent",	(PyCFunction)RMTS_GetAudioContent,	METH_VARARGS,	RMTS_GetAudioContent__doc__},
 {"SetAudioContent",	(PyCFunction)RMTS_SetAudioContent,	METH_VARARGS,	RMTS_SetAudioContent__doc__},
 {"GetVideoQuality",	(PyCFunction)RMTS_GetVideoQuality,	METH_VARARGS,	RMTS_GetVideoQuality__doc__},
 {"SetVideoQuality",	(PyCFunction)RMTS_SetVideoQuality,	METH_VARARGS,	RMTS_SetVideoQuality__doc__},
 {"GetPlayerCompatibility",	(PyCFunction)RMTS_GetPlayerCompatibility,	METH_VARARGS,	RMTS_GetPlayerCompatibility__doc__},
 {"SetPlayerCompatibility",	(PyCFunction)RMTS_SetPlayerCompatibility,	METH_VARARGS,	RMTS_SetPlayerCompatibility__doc__},
 {"GetEmphasizeAudio",	(PyCFunction)RMTS_GetEmphasizeAudio,	METH_VARARGS,	RMTS_GetEmphasizeAudio__doc__},
 {"SetEmphasizeAudio",	(PyCFunction)RMTS_SetEmphasizeAudio,	METH_VARARGS,	RMTS_SetEmphasizeAudio__doc__},
 {"GetDoAudioOnlyMultimedia",	(PyCFunction)RMTS_GetDoAudioOnlyMultimedia,	METH_VARARGS,	RMTS_GetDoAudioOnlyMultimedia__doc__},
 {"SetDoAudioOnlyMultimedia",	(PyCFunction)RMTS_SetDoAudioOnlyMultimedia,	METH_VARARGS,	RMTS_SetDoAudioOnlyMultimedia__doc__},
 
	{NULL,		NULL}		/* sentinel */
};

/* ---------- */


static void
RMTS_dealloc(RMTSobject *self)
{
	/* XXXX Add your own cleanup code here */
	if (self->targetSettings) {
		PN_RELEASE(self->targetSettings);
		self->targetSettings = NULL;
	}
	PyMem_DEL(self);
}

static PyObject *
RMTS_getattr(RMTSobject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(RMTS_methods, (PyObject *)self, name);
}

static char RMTStype__doc__[] = 
""
;

static PyTypeObject RMTStype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"RMTargetSettings",			/*tp_name*/
	sizeof(RMTSobject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)RMTS_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)RMTS_getattr,	/*tp_getattr*/
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
	RMTStype__doc__ /* Documentation string */
};

/* End of code for RMTargetSettings objects */
/* -------------------------------------------------------- */


static char RMCP_GetDoOutputFile__doc__[] = 
""
;

static PyObject *
RMCP_GetDoOutputFile(RMCPobject *self, PyObject *args)
{
	GETIVALUE(self->clipProperties, GetDoOutputFile, BOOL);
}


static char RMCP_SetDoOutputFile__doc__[] = 
""
;

static PyObject *
RMCP_SetDoOutputFile(RMCPobject *self, PyObject *args)
{
	SETIVALUE(self->clipProperties, SetDoOutputFile, BOOL);
}


static char RMCP_GetDoOutputServer__doc__[] = 
""
;

static PyObject *
RMCP_GetDoOutputServer(RMCPobject *self, PyObject *args)
{
	GETIVALUE(self->clipProperties, GetDoOutputServer, BOOL);
}


static char RMCP_SetDoOutputServer__doc__[] = 
""
;

static PyObject *
RMCP_SetDoOutputServer(RMCPobject *self, PyObject *args)
{
	SETIVALUE(self->clipProperties, SetDoOutputServer, BOOL);
}


static char RMCP_GetOutputFilename__doc__[] = 
""
;

static PyObject *
RMCP_GetOutputFilename(RMCPobject *self, PyObject *args)
{
	GETSVALUE(self->clipProperties, GetOutputFilename);
}


static char RMCP_SetOutputFilename__doc__[] = 
""
;

static PyObject *
RMCP_SetOutputFilename(RMCPobject *self, PyObject *args)
{
	PN_RESULT res;
	char *filename;

	if (!PyArg_ParseTuple(args, "s", &filename))
		return NULL;
	res = self->clipProperties->SetOutputFilename(filename);
	if (!SUCCEEDED(res)) {
		seterror("SetOutputFilename", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMCP_GetOutputServerInfo__doc__[] = 
""
;

static PyObject *
RMCP_GetOutputServerInfo(RMCPobject *self, PyObject *args)
{
	PN_RESULT res;
	char server[APP_MAX_PATH+1], streamname[APP_MAX_PATH+1], username[APP_MAX_PATH+1], passwd[APP_MAX_PATH+1];
	UINT32 port;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	res = self->clipProperties->GetOutputServerInfo(server, streamname, &port, username, passwd, APP_MAX_PATH);
	if (!SUCCEEDED(res)) {
		seterror("GetOutputServerInfo", res);
		return NULL;
	}
	return Py_BuildValue("(ssiss)", server, streamname, port, username, passwd);
}


static char RMCP_SetOutputServerInfo__doc__[] = 
""
;

static PyObject *
RMCP_SetOutputServerInfo(RMCPobject *self, PyObject *args)
{
	char *server, *streamname, *username, *passwd;
	long port;
	PN_RESULT res;

	if (!PyArg_ParseTuple(args, "sslss", &server, &streamname, &port, &username, &passwd))
		return NULL;
	res = self->clipProperties->SetOutputServerInfo(server, streamname, (UINT32) port, username, passwd);
	if (!SUCCEEDED(res)) {
		seterror("SetOutputServerInfo", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMCP_GetTitle__doc__[] = 
""
;

static PyObject *
RMCP_GetTitle(RMCPobject *self, PyObject *args)
{
	GETSVALUE(self->clipProperties, GetTitle);
}


static char RMCP_SetTitle__doc__[] = 
""
;

static PyObject *
RMCP_SetTitle(RMCPobject *self, PyObject *args)
{
	SETSVALUE(self->clipProperties, SetTitle);
}


static char RMCP_GetAuthor__doc__[] = 
""
;

static PyObject *
RMCP_GetAuthor(RMCPobject *self, PyObject *args)
{
	GETSVALUE(self->clipProperties, GetAuthor);
}


static char RMCP_SetAuthor__doc__[] = 
""
;

static PyObject *
RMCP_SetAuthor(RMCPobject *self, PyObject *args)
{
	SETSVALUE(self->clipProperties, SetAuthor);
}


static char RMCP_GetCopyright__doc__[] = 
""
;

static PyObject *
RMCP_GetCopyright(RMCPobject *self, PyObject *args)
{
	GETSVALUE(self->clipProperties, GetCopyright);
}


static char RMCP_SetCopyright__doc__[] = 
""
;

static PyObject *
RMCP_SetCopyright(RMCPobject *self, PyObject *args)
{
	SETSVALUE(self->clipProperties, SetCopyright);
}


static char RMCP_GetComment__doc__[] = 
""
;

static PyObject *
RMCP_GetComment(RMCPobject *self, PyObject *args)
{
	GETSVALUE(self->clipProperties, GetComment);
}


static char RMCP_SetComment__doc__[] = 
""
;

static PyObject *
RMCP_SetComment(RMCPobject *self, PyObject *args)
{
	SETSVALUE(self->clipProperties, SetComment);
}


static char RMCP_GetSelectiveRecord__doc__[] = 
""
;

static PyObject *
RMCP_GetSelectiveRecord(RMCPobject *self, PyObject *args)
{
	GETIVALUE(self->clipProperties, GetSelectiveRecord, BOOL);
}


static char RMCP_SetSelectiveRecord__doc__[] = 
""
;

static PyObject *
RMCP_SetSelectiveRecord(RMCPobject *self, PyObject *args)
{
	SETIVALUE(self->clipProperties, SetSelectiveRecord, BOOL);
}


static char RMCP_GetMobilePlay__doc__[] = 
""
;

static PyObject *
RMCP_GetMobilePlay(RMCPobject *self, PyObject *args)
{
	GETIVALUE(self->clipProperties, GetMobilePlay, BOOL);
}


static char RMCP_SetMobilePlay__doc__[] = 
""
;

static PyObject *
RMCP_SetMobilePlay(RMCPobject *self, PyObject *args)
{
	SETIVALUE(self->clipProperties, SetMobilePlay, BOOL);
}


static char RMCP_GetPerfectPlay__doc__[] = 
""
;

static PyObject *
RMCP_GetPerfectPlay(RMCPobject *self, PyObject *args)
{
	GETIVALUE(self->clipProperties, GetPerfectPlay, BOOL);
}


static char RMCP_SetPerfectPlay__doc__[] = 
""
;

static PyObject *
RMCP_SetPerfectPlay(RMCPobject *self, PyObject *args)
{
	SETIVALUE(self->clipProperties, SetPerfectPlay, BOOL);
}


static struct PyMethodDef RMCP_methods[] = {
	{"GetDoOutputFile",	(PyCFunction)RMCP_GetDoOutputFile,	METH_VARARGS,	RMCP_GetDoOutputFile__doc__},
 {"SetDoOutputFile",	(PyCFunction)RMCP_SetDoOutputFile,	METH_VARARGS,	RMCP_SetDoOutputFile__doc__},
 {"GetDoOutputServer",	(PyCFunction)RMCP_GetDoOutputServer,	METH_VARARGS,	RMCP_GetDoOutputServer__doc__},
 {"SetDoOutputServer",	(PyCFunction)RMCP_SetDoOutputServer,	METH_VARARGS,	RMCP_SetDoOutputServer__doc__},
 {"GetOutputFilename",	(PyCFunction)RMCP_GetOutputFilename,	METH_VARARGS,	RMCP_GetOutputFilename__doc__},
 {"SetOutputFilename",	(PyCFunction)RMCP_SetOutputFilename,	METH_VARARGS,	RMCP_SetOutputFilename__doc__},
 {"GetOutputServerInfo",	(PyCFunction)RMCP_GetOutputServerInfo,	METH_VARARGS,	RMCP_GetOutputServerInfo__doc__},
 {"SetOutputServerInfo",	(PyCFunction)RMCP_SetOutputServerInfo,	METH_VARARGS,	RMCP_SetOutputServerInfo__doc__},
 {"GetTitle",	(PyCFunction)RMCP_GetTitle,	METH_VARARGS,	RMCP_GetTitle__doc__},
 {"SetTitle",	(PyCFunction)RMCP_SetTitle,	METH_VARARGS,	RMCP_SetTitle__doc__},
 {"GetAuthor",	(PyCFunction)RMCP_GetAuthor,	METH_VARARGS,	RMCP_GetAuthor__doc__},
 {"SetAuthor",	(PyCFunction)RMCP_SetAuthor,	METH_VARARGS,	RMCP_SetAuthor__doc__},
 {"GetCopyright",	(PyCFunction)RMCP_GetCopyright,	METH_VARARGS,	RMCP_GetCopyright__doc__},
 {"SetCopyright",	(PyCFunction)RMCP_SetCopyright,	METH_VARARGS,	RMCP_SetCopyright__doc__},
 {"GetComment",	(PyCFunction)RMCP_GetComment,	METH_VARARGS,	RMCP_GetComment__doc__},
 {"SetComment",	(PyCFunction)RMCP_SetComment,	METH_VARARGS,	RMCP_SetComment__doc__},
 {"GetSelectiveRecord",	(PyCFunction)RMCP_GetSelectiveRecord,	METH_VARARGS,	RMCP_GetSelectiveRecord__doc__},
 {"SetSelectiveRecord",	(PyCFunction)RMCP_SetSelectiveRecord,	METH_VARARGS,	RMCP_SetSelectiveRecord__doc__},
 {"GetMobilePlay",	(PyCFunction)RMCP_GetMobilePlay,	METH_VARARGS,	RMCP_GetMobilePlay__doc__},
 {"SetMobilePlay",	(PyCFunction)RMCP_SetMobilePlay,	METH_VARARGS,	RMCP_SetMobilePlay__doc__},
 {"GetPerfectPlay",	(PyCFunction)RMCP_GetPerfectPlay,	METH_VARARGS,	RMCP_GetPerfectPlay__doc__},
 {"SetPerfectPlay",	(PyCFunction)RMCP_SetPerfectPlay,	METH_VARARGS,	RMCP_SetPerfectPlay__doc__},
 
	{NULL,		NULL}		/* sentinel */
};

/* ---------- */


static void
RMCP_dealloc(RMCPobject *self)
{
	/* XXXX Add your own cleanup code here */
	if (self->clipProperties) {
		PN_RELEASE(self->clipProperties);
		self->clipProperties = NULL;
	}
	PyMem_DEL(self);
}

static PyObject *
RMCP_getattr(RMCPobject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(RMCP_methods, (PyObject *)self, name);
}

static char RMCPtype__doc__[] = 
""
;

static PyTypeObject RMCPtype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"RMClipProperties",			/*tp_name*/
	sizeof(RMCPobject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)RMCP_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)RMCP_getattr,	/*tp_getattr*/
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
	RMCPtype__doc__ /* Documentation string */
};

/* End of code for RMClipProperties objects */
/* -------------------------------------------------------- */


static char RMBSP_GetOutputServerInfo__doc__[] = 
""
;

static PyObject *
RMBSP_GetOutputServerInfo(RMBSPobject *self, PyObject *args)
{
	PN_RESULT res;
	char server[APP_MAX_PATH+1], streamname[APP_MAX_PATH+1], username[APP_MAX_PATH+1], passwd[APP_MAX_PATH+1];
	UINT32 port;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	res = self->broadcastServerProperties->GetOutputServerInfo(server, streamname, &port, username, passwd, APP_MAX_PATH);
	if (!SUCCEEDED(res)) {
		seterror("GetOutputServerInfo", res);
		return NULL;
	}
	return Py_BuildValue("(ssiss)", server, streamname, port, username, passwd);
}


static char RMBSP_SetOutputServerInfo__doc__[] = 
""
;

static PyObject *
RMBSP_SetOutputServerInfo(RMBSPobject *self, PyObject *args)
{
	char *server, *streamname, *username, *passwd;
	long port;
	PN_RESULT res;

	if (!PyArg_ParseTuple(args, "sslss", &server, &streamname, &port, &username, &passwd))
		return NULL;
	res = self->broadcastServerProperties->SetOutputServerInfo(server, streamname, (UINT32) port, username, passwd);
	if (!SUCCEEDED(res)) {
		seterror("SetOutputServerInfo", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMBSP_GetTransportProtocol__doc__[] = 
""
;

static PyObject *
RMBSP_GetTransportProtocol(RMBSPobject *self, PyObject *args)
{
	GETSVALUE(self->broadcastServerProperties, GetTransportProtocol);
}


static char RMBSP_SetTransportProtocol__doc__[] = 
""
;

static PyObject *
RMBSP_SetTransportProtocol(RMBSPobject *self, PyObject *args)
{
	SETSVALUE(self->broadcastServerProperties, SetTransportProtocol);
}


static struct PyMethodDef RMBSP_methods[] = {
	{"GetOutputServerInfo",	(PyCFunction)RMBSP_GetOutputServerInfo,	METH_VARARGS,	RMBSP_GetOutputServerInfo__doc__},
 {"SetOutputServerInfo",	(PyCFunction)RMBSP_SetOutputServerInfo,	METH_VARARGS,	RMBSP_SetOutputServerInfo__doc__},
 {"GetTransportProtocol",	(PyCFunction)RMBSP_GetTransportProtocol,	METH_VARARGS,	RMBSP_GetTransportProtocol__doc__},
 {"SetTransportProtocol",	(PyCFunction)RMBSP_SetTransportProtocol,	METH_VARARGS,	RMBSP_SetTransportProtocol__doc__},
 
	{NULL,		NULL}		/* sentinel */
};

/* ---------- */


static void
RMBSP_dealloc(RMBSPobject *self)
{
	/* XXXX Add your own cleanup code here */
	if (self->broadcastServerProperties) {
		PN_RELEASE(self->broadcastServerProperties);
		self->broadcastServerProperties = NULL;
	}
	PyMem_DEL(self);
}

static PyObject *
RMBSP_getattr(RMBSPobject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(RMBSP_methods, (PyObject *)self, name);
}

static char RMBSPtype__doc__[] = 
""
;

static PyTypeObject RMBSPtype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"RMBroadcastServerProperties",			/*tp_name*/
	sizeof(RMBSPobject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)RMBSP_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)RMBSP_getattr,	/*tp_getattr*/
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
	RMBSPtype__doc__ /* Documentation string */
};

/* End of code for RMBroadcastServerProperties objects */
/* -------------------------------------------------------- */


static char RMPP_GetOutputMimeType__doc__[] = 
""
;

static PyObject *
RMPP_GetOutputMimeType(RMPPobject *self, PyObject *args)
{
	GETSVALUE(self->pinProperties, GetOutputMimeType);
}


static char RMPP_GetSampleRate__doc__[] = 
""
;

static PyObject *
RMPP_GetSampleRate(RMPPobject *self, PyObject *args)
{
	GETIVALUE((IRMAAudioPinProperties *)self->pinProperties, GetSampleRate, UINT32);
}


static char RMPP_SetSampleRate__doc__[] = 
""
;

static PyObject *
RMPP_SetSampleRate(RMPPobject *self, PyObject *args)
{
	SETIVALUE((IRMAAudioPinProperties *)self->pinProperties, SetSampleRate, UINT32);
}


static char RMPP_GetSampleSize__doc__[] = 
""
;

static PyObject *
RMPP_GetSampleSize(RMPPobject *self, PyObject *args)
{
	GETIVALUE((IRMAAudioPinProperties *)self->pinProperties, GetSampleSize, UINT32);
}


static char RMPP_SetSampleSize__doc__[] = 
""
;

static PyObject *
RMPP_SetSampleSize(RMPPobject *self, PyObject *args)
{
	SETIVALUE((IRMAAudioPinProperties *)self->pinProperties, SetSampleSize, UINT32);
}


static char RMPP_GetNumChannels__doc__[] = 
""
;

static PyObject *
RMPP_GetNumChannels(RMPPobject *self, PyObject *args)
{
	GETIVALUE((IRMAAudioPinProperties *)self->pinProperties, GetNumChannels, UINT32);
}


static char RMPP_SetNumChannels__doc__[] = 
""
;

static PyObject *
RMPP_SetNumChannels(RMPPobject *self, PyObject *args)
{
	SETIVALUE((IRMAAudioPinProperties *)self->pinProperties, SetNumChannels, UINT32);
}


static char RMPP_GetVideoSize__doc__[] = 
""
;

static PyObject *
RMPP_GetVideoSize(RMPPobject *self, PyObject *args)
{
	PN_RESULT res;
	UINT32 width, height;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	res = ((IRMAVideoPinProperties *)self->pinProperties)->GetVideoSize(&width, &height);
	if (!SUCCEEDED(res)) {
		seterror("GetVideoSize", res);
		return NULL;
	}
	return Py_BuildValue("(ll)", (long) width, (long) height);
}


static char RMPP_SetVideoSize__doc__[] = 
""
;

static PyObject *
RMPP_SetVideoSize(RMPPobject *self, PyObject *args)
{
	PN_RESULT res;
	long width, height;

	if (!PyArg_ParseTuple(args, "ll", &width, &height))
		return NULL;
	res = ((IRMAVideoPinProperties *) self->pinProperties)->SetVideoSize((UINT32) width, (UINT32) height);
	if (!SUCCEEDED(res)) {
		seterror("SetVideoSize", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMPP_GetVideoFormat__doc__[] = 
""
;

static PyObject *
RMPP_GetVideoFormat(RMPPobject *self, PyObject *args)
{
	GETIVALUE((IRMAVideoPinProperties *)self->pinProperties, GetVideoFormat, UINT32);
}


static char RMPP_SetVideoFormat__doc__[] = 
""
;

static PyObject *
RMPP_SetVideoFormat(RMPPobject *self, PyObject *args)
{
	SETIVALUE((IRMAVideoPinProperties *)self->pinProperties, SetVideoFormat, UINT32);
}


static char RMPP_GetCroppingEnabled__doc__[] = 
""
;

static PyObject *
RMPP_GetCroppingEnabled(RMPPobject *self, PyObject *args)
{
	GETIVALUE((IRMAVideoPinProperties *)self->pinProperties, GetCroppingEnabled, BOOL);
}


static char RMPP_SetCroppingEnabled__doc__[] = 
""
;

static PyObject *
RMPP_SetCroppingEnabled(RMPPobject *self, PyObject *args)
{
	SETIVALUE((IRMAVideoPinProperties *)self->pinProperties, SetCroppingEnabled, BOOL);
}


static char RMPP_GetCroppingSize__doc__[] = 
""
;

static PyObject *
RMPP_GetCroppingSize(RMPPobject *self, PyObject *args)
{
	PN_RESULT res;
	UINT32 left, top, width, height;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	res = ((IRMAVideoPinProperties *) self->pinProperties)->GetCroppingSize(&left, &top, &width, &height);
	if (!SUCCEEDED(res)) {
		seterror("GetCroppingSize", res);
		return NULL;
	}
	return Py_BuildValue("(llll)", (long) left, (long) top, (long) width, (long) height);
}


static char RMPP_SetCroppingSize__doc__[] = 
""
;

static PyObject *
RMPP_SetCroppingSize(RMPPobject *self, PyObject *args)
{
	PN_RESULT res;
	long left, top, width, height;

	if (!PyArg_ParseTuple(args, "llll", &left, &top, &width, &height))
		return NULL;
	res = ((IRMAVideoPinProperties *)self->pinProperties)->SetCroppingSize((UINT32) left, (UINT32) top, (UINT32) width, (UINT32) height);
	if (!SUCCEEDED(res)) {
		seterror("SetCroppingSize", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMPP_GetFrameRate__doc__[] = 
""
;

static PyObject *
RMPP_GetFrameRate(RMPPobject *self, PyObject *args)
{
	GETFVALUE((IRMAVideoPinProperties *)self->pinProperties, GetFrameRate);
}


static char RMPP_SetFrameRate__doc__[] = 
""
;

static PyObject *
RMPP_SetFrameRate(RMPPobject *self, PyObject *args)
{
	SETFVALUE((IRMAVideoPinProperties *)self->pinProperties, SetFrameRate);
}


static struct PyMethodDef RMPP_methods[] = {
	{"GetOutputMimeType",	(PyCFunction)RMPP_GetOutputMimeType,	METH_VARARGS,	RMPP_GetOutputMimeType__doc__},
 {"GetSampleRate",	(PyCFunction)RMPP_GetSampleRate,	METH_VARARGS,	RMPP_GetSampleRate__doc__},
 {"SetSampleRate",	(PyCFunction)RMPP_SetSampleRate,	METH_VARARGS,	RMPP_SetSampleRate__doc__},
 {"GetSampleSize",	(PyCFunction)RMPP_GetSampleSize,	METH_VARARGS,	RMPP_GetSampleSize__doc__},
 {"SetSampleSize",	(PyCFunction)RMPP_SetSampleSize,	METH_VARARGS,	RMPP_SetSampleSize__doc__},
 {"GetNumChannels",	(PyCFunction)RMPP_GetNumChannels,	METH_VARARGS,	RMPP_GetNumChannels__doc__},
 {"SetNumChannels",	(PyCFunction)RMPP_SetNumChannels,	METH_VARARGS,	RMPP_SetNumChannels__doc__},
 {"GetVideoSize",	(PyCFunction)RMPP_GetVideoSize,	METH_VARARGS,	RMPP_GetVideoSize__doc__},
 {"SetVideoSize",	(PyCFunction)RMPP_SetVideoSize,	METH_VARARGS,	RMPP_SetVideoSize__doc__},
 {"GetVideoFormat",	(PyCFunction)RMPP_GetVideoFormat,	METH_VARARGS,	RMPP_GetVideoFormat__doc__},
 {"SetVideoFormat",	(PyCFunction)RMPP_SetVideoFormat,	METH_VARARGS,	RMPP_SetVideoFormat__doc__},
 {"GetCroppingEnabled",	(PyCFunction)RMPP_GetCroppingEnabled,	METH_VARARGS,	RMPP_GetCroppingEnabled__doc__},
 {"SetCroppingEnabled",	(PyCFunction)RMPP_SetCroppingEnabled,	METH_VARARGS,	RMPP_SetCroppingEnabled__doc__},
 {"GetCroppingSize",	(PyCFunction)RMPP_GetCroppingSize,	METH_VARARGS,	RMPP_GetCroppingSize__doc__},
 {"SetCroppingSize",	(PyCFunction)RMPP_SetCroppingSize,	METH_VARARGS,	RMPP_SetCroppingSize__doc__},
 {"GetFrameRate",	(PyCFunction)RMPP_GetFrameRate,	METH_VARARGS,	RMPP_GetFrameRate__doc__},
 {"SetFrameRate",	(PyCFunction)RMPP_SetFrameRate,	METH_VARARGS,	RMPP_SetFrameRate__doc__},
 
	{NULL,		NULL}		/* sentinel */
};

/* ---------- */


static void
RMPP_dealloc(RMPPobject *self)
{
	/* XXXX Add your own cleanup code here */
	if (self->pinProperties) {
		PN_RELEASE(self->pinProperties);
		self->pinProperties = NULL;
	}
	PyMem_DEL(self);
}

static PyObject *
RMPP_getattr(RMPPobject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(RMPP_methods, (PyObject *)self, name);
}

static char RMPPtype__doc__[] = 
""
;

static PyTypeObject RMPPtype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"RMPinProperties",			/*tp_name*/
	sizeof(RMPPobject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)RMPP_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)RMPP_getattr,	/*tp_getattr*/
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
	RMPPtype__doc__ /* Documentation string */
};

/* End of code for RMPinProperties objects */
/* -------------------------------------------------------- */


static char RMMS_SetBuffer__doc__[] = 
""
;

static PyObject *
RMMS_SetBuffer(RMMSobject *self, PyObject *args)
{
	PN_RESULT res;
	void *buffer;
	int buffersize;
	long timestamp;
	int flags;

	if (!PyArg_ParseTuple(args, "s#li", &buffer, &buffersize, &timestamp, &flags))
		return NULL;
	res = self->mediaSample->SetBuffer(buffer, (UINT32) buffersize, (UINT32) timestamp, (UINT16) flags);
	if (!SUCCEEDED(res)) {
		seterror("SetBuffer", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMMS_GetBuffer__doc__[] = 
""
;

static PyObject *
RMMS_GetBuffer(RMMSobject *self, PyObject *args)
{
	PN_RESULT res;
	void *buffer;
	UINT32 buffersize;
	UINT32 timestamp;
	UINT16 flags;
	PyObject *v1, *v2;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	res = self->mediaSample->GetBuffer(&buffer, &buffersize, &timestamp, &flags);
	if (!SUCCEEDED(res)) {
		seterror("GetBuffer", res);
		return NULL;
	}
	v1 = PyString_FromStringAndSize((char *) buffer, (int) buffersize);
	if (v1 == NULL)
		return NULL;
	v2 = Py_BuildValue("(Oli)", v1, (long) timestamp, (int) flags);
	Py_DECREF(v1);
	return v2;
}


static char RMMS_SetTime__doc__[] = 
""
;

static PyObject *
RMMS_SetTime(RMMSobject *self, PyObject *args)
{
	PN_RESULT res;
	long start, stop;

	if (!PyArg_ParseTuple(args, "ll", &start, &stop))
		return NULL;
	res = ((IRMAEventMediaSample *) self->mediaSample)->SetTime((UINT32) start, (UINT32) stop);
	if (!SUCCEEDED(res)) {
		seterror("SetTime", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMMS_SetAction__doc__[] = 
""
;

static PyObject *
RMMS_SetAction(RMMSobject *self, PyObject *args)
{
	PN_RESULT res;
	int type;
	char *str;

	if (!PyArg_ParseTuple(args, "is", &type, &str))
		return NULL;
	res = ((IRMAEventMediaSample *) self->mediaSample)->SetAction((UINT16) type, str);
	if (!SUCCEEDED(res)) {
		seterror("SetAction", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMMS_SetMapTime__doc__[] = 
""
;

static PyObject *
RMMS_SetMapTime(RMMSobject *self, PyObject *args)
{
	PN_RESULT res;
	long start, stop;

	if (!PyArg_ParseTuple(args, "ll", &start, &stop))
		return NULL;
	res = ((IRMAImageMapMediaSample *) self->mediaSample)->SetMapTime((UINT32) start, (UINT32) stop);
	if (!SUCCEEDED(res)) {
		seterror("SetMapTime", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMMS_SetMapSize__doc__[] = 
""
;

static PyObject *
RMMS_SetMapSize(RMMSobject *self, PyObject *args)
{
	PN_RESULT res;
	int left, top, right, bottom;

	if (!PyArg_ParseTuple(args, "iiii", &left, &top, &right, &bottom))
		return NULL;
	res = ((IRMAImageMapMediaSample *) self->mediaSample)->SetMapSize((UINT16) left, (UINT16) top, (UINT16) right, (UINT16) bottom);
	if (!SUCCEEDED(res)) {
		seterror("SetMapSize", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMMS_ResetMap__doc__[] = 
""
;

static PyObject *
RMMS_ResetMap(RMMSobject *self, PyObject *args)
{
	CALLFUNC((IRMAImageMapMediaSample *) self->mediaSample, ResetMap);
}


static char RMMS_GetShapeHandle__doc__[] = 
""
;

static PyObject *
RMMS_GetShapeHandle(RMMSobject *self, PyObject *args)
{
	UINT32 handle;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	handle = ((IRMAImageMapMediaSample *) self->mediaSample)->GetShapeHandle();
	return PyInt_FromLong((long) handle);
}


static char RMMS_ReleaseShapeHandle__doc__[] = 
""
;

static PyObject *
RMMS_ReleaseShapeHandle(RMMSobject *self, PyObject *args)
{
	SETIVALUE((IRMAImageMapMediaSample *) self->mediaSample, ReleaseShapeHandle, UINT32);
}


static char RMMS_ResetShapeHandle__doc__[] = 
""
;

static PyObject *
RMMS_ResetShapeHandle(RMMSobject *self, PyObject *args)
{
	SETIVALUE((IRMAImageMapMediaSample *) self->mediaSample, ResetShapeHandle, UINT32);
}


static char RMMS_SetShapeType__doc__[] = 
""
;

static PyObject *
RMMS_SetShapeType(RMMSobject *self, PyObject *args)
{
	PN_RESULT res;
	long handle;
	int type;

	if (!PyArg_ParseTuple(args, "li", &handle, &type))
		return NULL;
	res = ((IRMAImageMapMediaSample *) self->mediaSample)->SetShapeType((UINT32) handle, (UINT16) type);
	if (!SUCCEEDED(res)) {
		seterror("SetShapeType", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMMS_SetShapeCoordinates__doc__[] = 
""
;

static PyObject *
RMMS_SetShapeCoordinates(RMMSobject *self, PyObject *args)
{
	PN_RESULT res;
	long handle;
	int len, i;
	PyObject *list, *item;
	UINT16 *array;

	if (!PyArg_ParseTuple(args, "lO!", &handle, &PyList_Type, &list))
		return NULL;
	len = PyList_Size(list);
	array = PyMem_NEW(UINT16, len);
	if (array == NULL)
		return PyErr_NoMemory();
	for (i = 0; i < len; i++) {
		item = PyList_GetItem(list, i);
		if (!PyInt_Check(item)) {
			PyMem_DEL(array);
			PyErr_BadArgument();
			return NULL;
		}
		array[i] = (UINT16) PyInt_AsLong(item);
	}
	res = ((IRMAImageMapMediaSample *) self->mediaSample)->SetShapeCoordinates((UINT32) handle, (UINT16) len, array);
	PyMem_DEL(array);	// XXX are we allowed to free this?
	if (!SUCCEEDED(res)) {
		seterror("SetShapeCoordinates", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMMS_AddShapeCoordinate__doc__[] = 
""
;

static PyObject *
RMMS_AddShapeCoordinate(RMMSobject *self, PyObject *args)
{
	PN_RESULT res;
	long handle;
	int coord;

	if (!PyArg_ParseTuple(args, "li", &handle, &coord))
		return NULL;
	res = ((IRMAImageMapMediaSample *) self->mediaSample)->AddShapeCoordinate((UINT32) handle, (UINT16) coord);
	if (!SUCCEEDED(res)) {
		seterror("AddShapeCoordinate", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMMS_SetShapeActionPlayFile__doc__[] = 
""
;

static PyObject *
RMMS_SetShapeActionPlayFile(RMMSobject *self, PyObject *args)
{
	PN_RESULT res;
	long handle;
	char *file;

	if (!PyArg_ParseTuple(args, "ls", &handle, &file))
		return NULL;
	res = ((IRMAImageMapMediaSample *) self->mediaSample)->SetShapeActionPlayFile((UINT32) handle, file);
	if (!SUCCEEDED(res)) {
		seterror("SetShapeActionPlayFile", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMMS_SetShapeActionBrowse__doc__[] = 
""
;

static PyObject *
RMMS_SetShapeActionBrowse(RMMSobject *self, PyObject *args)
{
	PN_RESULT res;
	long handle;
	char *url;

	if (!PyArg_ParseTuple(args, "ls", &handle, &url))
		return NULL;
	res = ((IRMAImageMapMediaSample *) self->mediaSample)->SetShapeActionBrowse((UINT32) handle, url);
	if (!SUCCEEDED(res)) {
		seterror("SetShapeActionBrowse", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMMS_SetShapeActionSeek__doc__[] = 
""
;

static PyObject *
RMMS_SetShapeActionSeek(RMMSobject *self, PyObject *args)
{
	PN_RESULT res;
	long handle, time;

	if (!PyArg_ParseTuple(args, "ll", &handle, &time))
		return NULL;
	res = ((IRMAImageMapMediaSample *) self->mediaSample)->SetShapeActionSeek((UINT32) handle, (UINT32) time);
	if (!SUCCEEDED(res)) {
		seterror("SetShapeActionSeek", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMMS_SetShapeAltText__doc__[] = 
""
;

static PyObject *
RMMS_SetShapeAltText(RMMSobject *self, PyObject *args)
{
	PN_RESULT res;
	long handle;
	char *text;

	if (!PyArg_ParseTuple(args, "ls", &handle, &text))
		return NULL;
	res = ((IRMAImageMapMediaSample *) self->mediaSample)->SetShapeAltText((UINT32) handle, text);
	if (!SUCCEEDED(res)) {
		seterror("SetShapeAltText", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMMS_SetShapeDuration__doc__[] = 
""
;

static PyObject *
RMMS_SetShapeDuration(RMMSobject *self, PyObject *args)
{
	PN_RESULT res;
	long handle, start, stop;

	if (!PyArg_ParseTuple(args, "lll", &handle, &start, &stop))
		return NULL;
	res = ((IRMAImageMapMediaSample *) self->mediaSample)->SetShapeDuration((UINT32) handle, (UINT32) start, (UINT32) stop);
	if (!SUCCEEDED(res)) {
		seterror("SetShapeDuration", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMMS_AddShape__doc__[] = 
""
;

static PyObject *
RMMS_AddShape(RMMSobject *self, PyObject *args)
{
	SETIVALUE((IRMAImageMapMediaSample *) self->mediaSample, AddShape, UINT32);
}


static struct PyMethodDef RMMS_methods[] = {
	{"SetBuffer",	(PyCFunction)RMMS_SetBuffer,	METH_VARARGS,	RMMS_SetBuffer__doc__},
 {"GetBuffer",	(PyCFunction)RMMS_GetBuffer,	METH_VARARGS,	RMMS_GetBuffer__doc__},
 {"SetTime",	(PyCFunction)RMMS_SetTime,	METH_VARARGS,	RMMS_SetTime__doc__},
 {"SetAction",	(PyCFunction)RMMS_SetAction,	METH_VARARGS,	RMMS_SetAction__doc__},
 {"SetMapTime",	(PyCFunction)RMMS_SetMapTime,	METH_VARARGS,	RMMS_SetMapTime__doc__},
 {"SetMapSize",	(PyCFunction)RMMS_SetMapSize,	METH_VARARGS,	RMMS_SetMapSize__doc__},
 {"ResetMap",	(PyCFunction)RMMS_ResetMap,	METH_VARARGS,	RMMS_ResetMap__doc__},
 {"GetShapeHandle",	(PyCFunction)RMMS_GetShapeHandle,	METH_VARARGS,	RMMS_GetShapeHandle__doc__},
 {"ReleaseShapeHandle",	(PyCFunction)RMMS_ReleaseShapeHandle,	METH_VARARGS,	RMMS_ReleaseShapeHandle__doc__},
 {"ResetShapeHandle",	(PyCFunction)RMMS_ResetShapeHandle,	METH_VARARGS,	RMMS_ResetShapeHandle__doc__},
 {"SetShapeType",	(PyCFunction)RMMS_SetShapeType,	METH_VARARGS,	RMMS_SetShapeType__doc__},
 {"SetShapeCoordinates",	(PyCFunction)RMMS_SetShapeCoordinates,	METH_VARARGS,	RMMS_SetShapeCoordinates__doc__},
 {"AddShapeCoordinate",	(PyCFunction)RMMS_AddShapeCoordinate,	METH_VARARGS,	RMMS_AddShapeCoordinate__doc__},
 {"SetShapeActionPlayFile",	(PyCFunction)RMMS_SetShapeActionPlayFile,	METH_VARARGS,	RMMS_SetShapeActionPlayFile__doc__},
 {"SetShapeActionBrowse",	(PyCFunction)RMMS_SetShapeActionBrowse,	METH_VARARGS,	RMMS_SetShapeActionBrowse__doc__},
 {"SetShapeActionSeek",	(PyCFunction)RMMS_SetShapeActionSeek,	METH_VARARGS,	RMMS_SetShapeActionSeek__doc__},
 {"SetShapeAltText",	(PyCFunction)RMMS_SetShapeAltText,	METH_VARARGS,	RMMS_SetShapeAltText__doc__},
 {"SetShapeDuration",	(PyCFunction)RMMS_SetShapeDuration,	METH_VARARGS,	RMMS_SetShapeDuration__doc__},
 {"AddShape",	(PyCFunction)RMMS_AddShape,	METH_VARARGS,	RMMS_AddShape__doc__},
 
	{NULL,		NULL}		/* sentinel */
};

/* ---------- */


static void
RMMS_dealloc(RMMSobject *self)
{
	/* XXXX Add your own cleanup code here */
	if (self->mediaSample) {
		PN_RELEASE(self->mediaSample);
		self->mediaSample = NULL;
	}
	PyMem_DEL(self);
}

static PyObject *
RMMS_getattr(RMMSobject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(RMMS_methods, (PyObject *)self, name);
}

static char RMMStype__doc__[] = 
""
;

static PyTypeObject RMMStype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"RMMediaSample",			/*tp_name*/
	sizeof(RMMSobject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)RMMS_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)RMMS_getattr,	/*tp_getattr*/
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
	RMMStype__doc__ /* Documentation string */
};

/* End of code for RMMediaSample objects */
/* -------------------------------------------------------- */


static char RMTAM_GetTargetAudienceInfo__doc__[] = 
""
;

static PyObject *
RMTAM_GetTargetAudienceInfo(RMTAMobject *self, PyObject *args)
{
	PN_RESULT res;
	int  target;
	RMTAIobject *v;

	if (!PyArg_ParseTuple(args, "i", &target))
		return NULL;
	v = newRMTAIobject();
	res = self->targetAudienceManager->GetTargetAudienceInfo((UINT16) target, v->targetAudienceInfo);
	if (!SUCCEEDED(res)) {
		seterror("GetTargetAudienceInfo", res);
		return NULL;
	}
	return (PyObject *) v;
}


static char RMTAM_DisplayTargetAudienceSettings__doc__[] = 
""
;

static PyObject *
RMTAM_DisplayTargetAudienceSettings(RMTAMobject *self, PyObject *args)
{
#if 0
	PN_RESULT res;
	long descr, parent;
	RMTSobject *settings;
	char *path;

	if (!PyArg_ParseTuple(args, "llO!s", &descr, &parent, &RMTStype, &settings, &path))
		return NULL;
	res = self->targetAudienceManager->DisplayTargetAudienceSettings((UINT32) descr, (UINT32) parent, (IRMABasicTargetSettings *) settings->targetSettings, path);
	if (!SUCCEEDED(res)) {
		seterror("DisplayTargetAudienceSettings", res);
		return NULL;
	}
#endif
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMTAM_RestoreDefaults__doc__[] = 
""
;

static PyObject *
RMTAM_RestoreDefaults(RMTAMobject *self, PyObject *args)
{
	SETIVALUE(self->targetAudienceManager, RestoreDefaults, UINT32);
}


static struct PyMethodDef RMTAM_methods[] = {
	{"GetTargetAudienceInfo",	(PyCFunction)RMTAM_GetTargetAudienceInfo,	METH_VARARGS,	RMTAM_GetTargetAudienceInfo__doc__},
 {"DisplayTargetAudienceSettings",	(PyCFunction)RMTAM_DisplayTargetAudienceSettings,	METH_VARARGS,	RMTAM_DisplayTargetAudienceSettings__doc__},
 {"RestoreDefaults",	(PyCFunction)RMTAM_RestoreDefaults,	METH_VARARGS,	RMTAM_RestoreDefaults__doc__},
 
	{NULL,		NULL}		/* sentinel */
};

/* ---------- */


static void
RMTAM_dealloc(RMTAMobject *self)
{
	/* XXXX Add your own cleanup code here */
	if (self->targetAudienceManager) {
		PN_RELEASE(self->targetAudienceManager);
		self->targetAudienceManager = NULL;
	}
	PyMem_DEL(self);
}

static PyObject *
RMTAM_getattr(RMTAMobject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(RMTAM_methods, (PyObject *)self, name);
}

static char RMTAMtype__doc__[] = 
""
;

static PyTypeObject RMTAMtype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"RMTargetAudienceManager",			/*tp_name*/
	sizeof(RMTAMobject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)RMTAM_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)RMTAM_getattr,	/*tp_getattr*/
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
	RMTAMtype__doc__ /* Documentation string */
};

/* End of code for RMTargetAudienceManager objects */
/* -------------------------------------------------------- */


static char RMTAI_GetTargetAudienceID__doc__[] = 
""
;

static PyObject *
RMTAI_GetTargetAudienceID(RMTAIobject *self, PyObject *args)
{
	GETVALUE(self->targetAudienceInfo, GetTargetAudienceID, UINT32, PyInt_FromLong, (long), EMPTYARG);
}


static char RMTAI_GetTargetAudienceName__doc__[] = 
""
;

static PyObject *
RMTAI_GetTargetAudienceName(RMTAIobject *self, PyObject *args)
{
	GETSVALUE(self->targetAudienceInfo, GetTargetAudienceName);
}


static char RMTAI_GetTargetBitrate__doc__[] = 
""
;

static PyObject *
RMTAI_GetTargetBitrate(RMTAIobject *self, PyObject *args)
{
	GETVALUE(self->targetAudienceInfo, GetTargetBitrate, float, PyFloat_FromDouble, (double), EMPTYARG);
}


static char RMTAI_SetTargetBitrate__doc__[] = 
""
;

static PyObject *
RMTAI_SetTargetBitrate(RMTAIobject *self, PyObject *args)
{
	SETFVALUE(self->targetAudienceInfo, SetTargetBitrate);
}


static char RMTAI_GetAudioCodec__doc__[] = 
""
;

static PyObject *
RMTAI_GetAudioCodec(RMTAIobject *self, PyObject *args)
{
	PN_RESULT res;
	long descr, content;
	RMCCobject *v;

	if (!PyArg_ParseTuple(args, "ll", &descr, &content))
		return NULL;
	v = newRMCCobject();
	res = self->targetAudienceInfo->GetAudioCodec((UINT32) descr, (UINT32) content, v->codecCookie);
	if (!SUCCEEDED(res)) {
		seterror("GetAudioCodec", res);
		return NULL;
	}
	return (PyObject *) v;
}


static char RMTAI_SetAudioCodec__doc__[] = 
""
;

static PyObject *
RMTAI_SetAudioCodec(RMTAIobject *self, PyObject *args)
{
	PN_RESULT res;
	long descr, content;
	RMCCobject *v;

	if (!PyArg_ParseTuple(args, "llO!", &descr, &content, &RMCCtype, &v))
		return NULL;
	res = self->targetAudienceInfo->SetAudioCodec((UINT32) descr, (UINT32) content, v->codecCookie);
	if (!SUCCEEDED(res)) {
		seterror("SetAudioCodec", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMTAI_GetVideoCodec__doc__[] = 
""
;

static PyObject *
RMTAI_GetVideoCodec(RMTAIobject *self, PyObject *args)
{
	PN_RESULT res;
	RMCCobject *v;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	v = newRMCCobject();
	res = self->targetAudienceInfo->GetVideoCodec(v->codecCookie);
	if (!SUCCEEDED(res)) {
		seterror("GetVideoCodec", res);
		return NULL;
	}
	return (PyObject *) v;
}


static char RMTAI_SetVideoCodec__doc__[] = 
""
;

static PyObject *
RMTAI_SetVideoCodec(RMTAIobject *self, PyObject *args)
{
	PN_RESULT res;
	RMCCobject *v;

	if (!PyArg_ParseTuple(args, "O!", &RMCCtype, &v))
		return NULL;
	res = self->targetAudienceInfo->SetVideoCodec(v->codecCookie);
	if (!SUCCEEDED(res)) {
		seterror("SetVideoCodec", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char RMTAI_GetMaxFrameRate__doc__[] = 
""
;

static PyObject *
RMTAI_GetMaxFrameRate(RMTAIobject *self, PyObject *args)
{
	GETVALUE(self->targetAudienceInfo, GetMaxFrameRate, float, PyFloat_FromDouble, (double), EMPTYARG);
}


static char RMTAI_SetMaxFrameRate__doc__[] = 
""
;

static PyObject *
RMTAI_SetMaxFrameRate(RMTAIobject *self, PyObject *args)
{
	SETFVALUE(self->targetAudienceInfo, SetMaxFrameRate);
}


static struct PyMethodDef RMTAI_methods[] = {
	{"GetTargetAudienceID",	(PyCFunction)RMTAI_GetTargetAudienceID,	METH_VARARGS,	RMTAI_GetTargetAudienceID__doc__},
 {"GetTargetAudienceName",	(PyCFunction)RMTAI_GetTargetAudienceName,	METH_VARARGS,	RMTAI_GetTargetAudienceName__doc__},
 {"GetTargetBitrate",	(PyCFunction)RMTAI_GetTargetBitrate,	METH_VARARGS,	RMTAI_GetTargetBitrate__doc__},
 {"SetTargetBitrate",	(PyCFunction)RMTAI_SetTargetBitrate,	METH_VARARGS,	RMTAI_SetTargetBitrate__doc__},
 {"GetAudioCodec",	(PyCFunction)RMTAI_GetAudioCodec,	METH_VARARGS,	RMTAI_GetAudioCodec__doc__},
 {"SetAudioCodec",	(PyCFunction)RMTAI_SetAudioCodec,	METH_VARARGS,	RMTAI_SetAudioCodec__doc__},
 {"GetVideoCodec",	(PyCFunction)RMTAI_GetVideoCodec,	METH_VARARGS,	RMTAI_GetVideoCodec__doc__},
 {"SetVideoCodec",	(PyCFunction)RMTAI_SetVideoCodec,	METH_VARARGS,	RMTAI_SetVideoCodec__doc__},
 {"GetMaxFrameRate",	(PyCFunction)RMTAI_GetMaxFrameRate,	METH_VARARGS,	RMTAI_GetMaxFrameRate__doc__},
 {"SetMaxFrameRate",	(PyCFunction)RMTAI_SetMaxFrameRate,	METH_VARARGS,	RMTAI_SetMaxFrameRate__doc__},
 
	{NULL,		NULL}		/* sentinel */
};

/* ---------- */


static void
RMTAI_dealloc(RMTAIobject *self)
{
	/* XXXX Add your own cleanup code here */
	if (self->targetAudienceInfo) {
		PN_RELEASE(self->targetAudienceInfo);
		self->targetAudienceInfo = NULL;
	}
	PyMem_DEL(self);
}

static PyObject *
RMTAI_getattr(RMTAIobject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(RMTAI_methods, (PyObject *)self, name);
}

static char RMTAItype__doc__[] = 
""
;

static PyTypeObject RMTAItype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"RMTargetAudienceInfo",			/*tp_name*/
	sizeof(RMTAIobject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)RMTAI_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)RMTAI_getattr,	/*tp_getattr*/
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
	RMTAItype__doc__ /* Documentation string */
};

/* End of code for RMTargetAudienceInfo objects */
/* -------------------------------------------------------- */


static char RMCIM_GetAudioCodecs__doc__[] = 
""
;

static PyObject *
RMCIM_GetAudioCodecs(RMCIMobject *self, PyObject *args)
{
#if 0
	ENUMERATE(self->codecInfoManager, GetAudioCodecEnum, newRMCIobject, IID_IRMAAudioCodecInfo, RMCIobject, codecInfo, EMPTYARG);
#else
	Py_INCREF(Py_None);
	return Py_None;
#endif
}


static char RMCIM_GetVideoCodecs__doc__[] = 
""
;

static PyObject *
RMCIM_GetVideoCodecs(RMCIMobject *self, PyObject *args)
{
#if 0
	ENUMERATE(self->codecInfoManager, GetVideoCodecEnum, newRMCIobject, IID_IRMAVideoCodecInfo, RMCIobject, codecInfo, EMPTYARG);
#else
	Py_INCREF(Py_None);
	return Py_None;
#endif
}


static char RMCIM_GetCodecInfo__doc__[] = 
""
;

static PyObject *
RMCIM_GetCodecInfo(RMCIMobject *self, PyObject *args)
{
	PN_RESULT res;
	RMCCobject *cookie;
	RMCIobject *v;

	if (!PyArg_ParseTuple(args, "O!", &RMCCtype, &cookie))
		return NULL;
	v = newRMCIobject();
	res = self->codecInfoManager->GetCodecInfo(cookie->codecCookie, v->codecInfo);
	if (!SUCCEEDED(res)) {
		seterror("GetCodecInfo", res);
		return NULL;
	}
	return (PyObject *) v;
}


static struct PyMethodDef RMCIM_methods[] = {
	{"GetAudioCodecs",	(PyCFunction)RMCIM_GetAudioCodecs,	METH_VARARGS,	RMCIM_GetAudioCodecs__doc__},
 {"GetVideoCodecs",	(PyCFunction)RMCIM_GetVideoCodecs,	METH_VARARGS,	RMCIM_GetVideoCodecs__doc__},
 {"GetCodecInfo",	(PyCFunction)RMCIM_GetCodecInfo,	METH_VARARGS,	RMCIM_GetCodecInfo__doc__},
 
	{NULL,		NULL}		/* sentinel */
};

/* ---------- */


static void
RMCIM_dealloc(RMCIMobject *self)
{
	/* XXXX Add your own cleanup code here */
	if (self->codecInfoManager) {
		PN_RELEASE(self->codecInfoManager);
		self->codecInfoManager = NULL;
	}
	PyMem_DEL(self);
}

static PyObject *
RMCIM_getattr(RMCIMobject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(RMCIM_methods, (PyObject *)self, name);
}

static char RMCIMtype__doc__[] = 
""
;

static PyTypeObject RMCIMtype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"RMCodecInfoManager",			/*tp_name*/
	sizeof(RMCIMobject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)RMCIM_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)RMCIM_getattr,	/*tp_getattr*/
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
	RMCIMtype__doc__ /* Documentation string */
};

/* End of code for RMCodecInfoManager objects */
/* -------------------------------------------------------- */


static struct PyMethodDef RMCC_methods[] = {
	{NULL,		NULL}		/* sentinel */
};

/* ---------- */


static void
RMCC_dealloc(RMCCobject *self)
{
	/* XXXX Add your own cleanup code here */
	PyMem_DEL(self);
}

static PyObject *
RMCC_getattr(RMCCobject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	if (strcmp(name, "codecID") == 0)
		return PyInt_FromLong((long) self->codecCookie.codecID);
	if (strcmp(name, "flavorID") == 0)
		return PyInt_FromLong((long) self->codecCookie.flavorID);
	return Py_FindMethod(RMCC_methods, (PyObject *)self, name);
}

static char RMCCtype__doc__[] = 
""
;

static PyTypeObject RMCCtype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"RMCodecCookie",			/*tp_name*/
	sizeof(RMCCobject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)RMCC_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)RMCC_getattr,	/*tp_getattr*/
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
	RMCCtype__doc__ /* Documentation string */
};

/* End of code for RMCodecCookie objects */
/* -------------------------------------------------------- */


static char RMCI_GetCodecCookie__doc__[] = 
""
;

static PyObject *
RMCI_GetCodecCookie(RMCIobject *self, PyObject *args)
{
	PN_RESULT res;
	RMCCobject *v;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	v = newRMCCobject();
	res = self->codecInfo->GetCodecCookie(v->codecCookie);
	if (!SUCCEEDED(res)) {
		seterror("GetCodecCookie", res);
		return NULL;
	}
	return (PyObject *) v;
}


static char RMCI_GetCodecName__doc__[] = 
""
;

static PyObject *
RMCI_GetCodecName(RMCIobject *self, PyObject *args)
{
	GETSVALUE(self->codecInfo, GetCodecName);
}


static char RMCI_GetOldestCompatiblePlayer__doc__[] = 
""
;

static PyObject *
RMCI_GetOldestCompatiblePlayer(RMCIobject *self, PyObject *args)
{
	GETVALUE(self->codecInfo, GetOldestCompatiblePlayer, UINT32, PyInt_FromLong, (long), EMPTYARG);
}


static char RMCI_GetCodecForVersion__doc__[] = 
""
;

static PyObject *
RMCI_GetCodecForVersion(RMCIobject *self, PyObject *args)
{
	PN_RESULT res;
	long version;
	RMCCobject *v;

	if (!PyArg_ParseTuple(args, "l", &version))
		return NULL;
	v = newRMCCobject();
	res = self->codecInfo->GetCodecForVersion(version, v->codecCookie);
	if (!SUCCEEDED(res)) {
		seterror("GetCodecForVersion", res);
		return NULL;
	}
	return (PyObject *) v;
}


static char RMCI_GetDescription__doc__[] = 
""
;

static PyObject *
RMCI_GetDescription(RMCIobject *self, PyObject *args)
{
	GETSVALUE((IRMACodecInfo2 *) self->codecInfo, GetDescription);
}


static char RMCI_GetBitrate__doc__[] = 
""
;

static PyObject *
RMCI_GetBitrate(RMCIobject *self, PyObject *args)
{
	GETVALUE((IRMAAudioCodecInfo *) self->codecInfo, GetBitrate, UINT32, PyInt_FromLong, (long), EMPTYARG);
}


static char RMCI_GetSampleRate__doc__[] = 
""
;

static PyObject *
RMCI_GetSampleRate(RMCIobject *self, PyObject *args)
{
	GETVALUE((IRMAAudioCodecInfo *) self->codecInfo, GetSampleRate, UINT32, PyInt_FromLong, (long), EMPTYARG);
}


static char RMCI_GetSampleSize__doc__[] = 
""
;

static PyObject *
RMCI_GetSampleSize(RMCIobject *self, PyObject *args)
{
	GETVALUE((IRMAAudioCodecInfo *) self->codecInfo, GetSampleSize, UINT32, PyInt_FromLong, (long), EMPTYARG);
}


static char RMCI_GetNumChannels__doc__[] = 
""
;

static PyObject *
RMCI_GetNumChannels(RMCIobject *self, PyObject *args)
{
	GETVALUE((IRMAAudioCodecInfo *) self->codecInfo, GetNumChannels, UINT32, PyInt_FromLong, (long), EMPTYARG);
}


static char RMCI_GetFrequencyResponse__doc__[] = 
""
;

static PyObject *
RMCI_GetFrequencyResponse(RMCIobject *self, PyObject *args)
{
	GETVALUE((IRMAAudioCodecInfo *) self->codecInfo, GetFrequencyResponse, UINT32, PyInt_FromLong, (long), EMPTYARG);
}


static char RMCI_GetCodecModulus__doc__[] = 
""
;

static PyObject *
RMCI_GetCodecModulus(RMCIobject *self, PyObject *args)
{
	PN_RESULT res;
	UINT32 width, height;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	res = ((IRMAVideoCodecInfo *) self->codecInfo)->GetCodecModulus(width, height);
	if (!SUCCEEDED(res)) {
		seterror("GetCodecModulus", res);
		return NULL;
	}
	return Py_BuildValue("(ll)", (long) width, (long) height);
}


static struct PyMethodDef RMCI_methods[] = {
	{"GetCodecCookie",	(PyCFunction)RMCI_GetCodecCookie,	METH_VARARGS,	RMCI_GetCodecCookie__doc__},
 {"GetCodecName",	(PyCFunction)RMCI_GetCodecName,	METH_VARARGS,	RMCI_GetCodecName__doc__},
 {"GetOldestCompatiblePlayer",	(PyCFunction)RMCI_GetOldestCompatiblePlayer,	METH_VARARGS,	RMCI_GetOldestCompatiblePlayer__doc__},
 {"GetCodecForVersion",	(PyCFunction)RMCI_GetCodecForVersion,	METH_VARARGS,	RMCI_GetCodecForVersion__doc__},
 {"GetDescription",	(PyCFunction)RMCI_GetDescription,	METH_VARARGS,	RMCI_GetDescription__doc__},
 {"GetBitrate",	(PyCFunction)RMCI_GetBitrate,	METH_VARARGS,	RMCI_GetBitrate__doc__},
 {"GetSampleRate",	(PyCFunction)RMCI_GetSampleRate,	METH_VARARGS,	RMCI_GetSampleRate__doc__},
 {"GetSampleSize",	(PyCFunction)RMCI_GetSampleSize,	METH_VARARGS,	RMCI_GetSampleSize__doc__},
 {"GetNumChannels",	(PyCFunction)RMCI_GetNumChannels,	METH_VARARGS,	RMCI_GetNumChannels__doc__},
 {"GetFrequencyResponse",	(PyCFunction)RMCI_GetFrequencyResponse,	METH_VARARGS,	RMCI_GetFrequencyResponse__doc__},
 {"GetCodecModulus",	(PyCFunction)RMCI_GetCodecModulus,	METH_VARARGS,	RMCI_GetCodecModulus__doc__},
 
	{NULL,		NULL}		/* sentinel */
};

/* ---------- */


static void
RMCI_dealloc(RMCIobject *self)
{
	/* XXXX Add your own cleanup code here */
	if (self->codecInfo) {
		PN_RELEASE(self->codecInfo);
		self->codecInfo = NULL;
	}
	PyMem_DEL(self);
}

static PyObject *
RMCI_getattr(RMCIobject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(RMCI_methods, (PyObject *)self, name);
}

static char RMCItype__doc__[] = 
""
;

static PyTypeObject RMCItype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"RMCodecInfo",			/*tp_name*/
	sizeof(RMCIobject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)RMCI_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)RMCI_getattr,	/*tp_getattr*/
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
	RMCItype__doc__ /* Documentation string */
};

/* End of code for RMCodecInfo objects */
/* -------------------------------------------------------- */


static char RP_CreateRMBuildEngine__doc__[] =
""
;

static PyObject *
RP_CreateRMBuildEngine(PyObject *self, PyObject *args)
{
	PN_RESULT res;
	RMBEobject *obj;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;

	obj = newRMBEobject();
	if (obj == NULL)
		return NULL;
	res = RMACreateRMBuildEngine(&obj->buildEngine);
	if (!SUCCEEDED(res)) {
		Py_DECREF(obj);
		seterror("RMACreateRMBuildEngine", res);
		return NULL;
	}
	return (PyObject *) obj;
}

/* List of methods defined in the module */

static struct PyMethodDef RP_methods[] = {
	{"CreateRMBuildEngine",	(PyCFunction)RP_CreateRMBuildEngine,	METH_VARARGS,	RP_CreateRMBuildEngine__doc__},
 
	{NULL,	 (PyCFunction)NULL, 0, NULL}		/* sentinel */
};


STDAPI SetDLLAccessPath(const char *pPathDescriptor);

static void
SetDllCategoryPaths()
{
	char szAppDir[APP_MAX_PATH+1] = "";

	// Get the app dir -- this is platform specific
#if 0
#if defined(_WIN32)
	GetModuleFileName(NULL, szAppDir, APP_MAX_PATH);
	char* pLastChar = strrchr(szAppDir, '\\');
	if (pLastChar != NULL)
		*(pLastChar+1) = '\0';
#elif defined(_MACINTOSH)
	CMacStuff::GetApplicationDirectory(szAppDir);
#endif
#else
	strcpy(szAppDir, "d:\\ufs\\mm\\cmif\bin\\win32\\");
#endif

	// Set the DLL Access paths
	// Win32 DEBUG builds and all Mac builds set everything to the app dir
	// All other builds look in subdirs underneath the app dir
	UINT32 ulNumChars = 0;   
	char szDllPath[6*APP_MAX_PATH] = "";      

	ulNumChars += sprintf(szDllPath+ulNumChars,"DT_Plugins=%s",szAppDir)+1;
	ulNumChars += sprintf(szDllPath+ulNumChars,"DT_Codecs=%s",szAppDir)+1;
	ulNumChars += sprintf(szDllPath+ulNumChars,"DT_EncSDK=%s",szAppDir)+1;
	ulNumChars += sprintf(szDllPath+ulNumChars,"DT_Common=%s",szAppDir)+1;
	ulNumChars += sprintf(szDllPath+ulNumChars,"DT_Update=%s",szAppDir)+1;

	// Set the path used to load RealProducer Core G2 SDK DLL's
#ifdef RN_DLL_ACCESS
	GetDLLAccessPath()->SetAccessPaths(szDllPath);  
#else
	SetDLLAccessPath(szDllPath); 
#endif
}

/* Initialization function for the module (*must* be called initproducer) */

static char producer_module_documentation[] = 
""
;

#ifdef _WINDOWS
#ifdef PY_EXPORTS
#define DLL_API __declspec(dllexport)
#else
#define DLL_API __declspec(dllimport)
#endif
#else
#define DLL_API
#endif
#define PY_API extern "C" DLL_API

PY_API void
initproducer()
{
	PyObject *m, *d, *x;

	SetDllCategoryPaths();

	/* Create the module and add the functions */
	m = Py_InitModule4("producer", RP_methods,
		producer_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	/* Add some symbolic constants to the module */
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("producer.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	/* XXXX Add constants here */
	x = PyString_FromString(MIME_REALAUDIO);
	if (x == NULL || PyDict_SetItemString(d, "MIME_REALAUDIO", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyString_FromString(MIME_REALVIDEO);
	if (x == NULL || PyDict_SetItemString(d, "MIME_REALVIDEO", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyString_FromString(MIME_REALEVENT);
	if (x == NULL || PyDict_SetItemString(d, "MIME_REALEVENT", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyString_FromString(MIME_REALIMAGEMAP);
	if (x == NULL || PyDict_SetItemString(d, "MIME_REALIMAGEMAP", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyString_FromString(MIME_REALPIX);
	if (x == NULL || PyDict_SetItemString(d, "MIME_REALPIX", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_TARGET_28_MODEM);
	if (x == NULL || PyDict_SetItemString(d, "ENC_TARGET_28_MODEM", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_TARGET_56_MODEM);
	if (x == NULL || PyDict_SetItemString(d, "ENC_TARGET_56_MODEM", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_TARGET_SINGLE_ISDN);
	if (x == NULL || PyDict_SetItemString(d, "ENC_TARGET_SINGLE_ISDN", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_TARGET_DUAL_ISDN);
	if (x == NULL || PyDict_SetItemString(d, "ENC_TARGET_DUAL_ISDN", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_TARGET_LAN_LOW);
	if (x == NULL || PyDict_SetItemString(d, "ENC_TARGET_LAN_LOW", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_TARGET_LAN_HIGH);
	if (x == NULL || PyDict_SetItemString(d, "ENC_TARGET_LAN_HIGH", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_NUM_TARGET_AUDIENCES);
	if (x == NULL || PyDict_SetItemString(d, "ENC_NUM_TARGET_AUDIENCES", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_AUDIO_CONTENT_VOICE);
	if (x == NULL || PyDict_SetItemString(d, "ENC_AUDIO_CONTENT_VOICE", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_AUDIO_CONTENT_VOICE_BACKGROUND);
	if (x == NULL || PyDict_SetItemString(d, "ENC_AUDIO_CONTENT_VOICE_BACKGROUND", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_AUDIO_CONTENT_MUSIC);
	if (x == NULL || PyDict_SetItemString(d, "ENC_AUDIO_CONTENT_MUSIC", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_AUDIO_CONTENT_MUSIC_STEREO);
	if (x == NULL || PyDict_SetItemString(d, "ENC_AUDIO_CONTENT_MUSIC_STEREO", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_NUM_AUDIO_CONTENTS);
	if (x == NULL || PyDict_SetItemString(d, "ENC_NUM_AUDIO_CONTENTS", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_VIDEO_QUALITY_NORMAL);
	if (x == NULL || PyDict_SetItemString(d, "ENC_VIDEO_QUALITY_NORMAL", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_VIDEO_QUALITY_SMOOTH_MOTION);
	if (x == NULL || PyDict_SetItemString(d, "ENC_VIDEO_QUALITY_SMOOTH_MOTION", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_VIDEO_QUALITY_SHARP_IMAGE);
	if (x == NULL || PyDict_SetItemString(d, "ENC_VIDEO_QUALITY_SHARP_IMAGE", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_VIDEO_QUALITY_SLIDESHOW);
	if (x == NULL || PyDict_SetItemString(d, "ENC_VIDEO_QUALITY_SLIDESHOW", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_NUM_VIDEO_QUALITYS);
	if (x == NULL || PyDict_SetItemString(d, "ENC_NUM_VIDEO_QUALITYS", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_VIDEO_FORMAT_RGB24);
	if (x == NULL || PyDict_SetItemString(d, "ENC_VIDEO_FORMAT_RGB24", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_VIDEO_FORMAT_RGB32);
	if (x == NULL || PyDict_SetItemString(d, "ENC_VIDEO_FORMAT_RGB32", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_VIDEO_FORMAT_RGB32_NONINVERTED);
	if (x == NULL || PyDict_SetItemString(d, "ENC_VIDEO_FORMAT_RGB32_NONINVERTED", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_VIDEO_FORMAT_BGR32);
	if (x == NULL || PyDict_SetItemString(d, "ENC_VIDEO_FORMAT_BGR32", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_VIDEO_FORMAT_BGR32_NONINVERTED);
	if (x == NULL || PyDict_SetItemString(d, "ENC_VIDEO_FORMAT_BGR32_NONINVERTED", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_VIDEO_FORMAT_I420);
	if (x == NULL || PyDict_SetItemString(d, "ENC_VIDEO_FORMAT_I420", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_VIDEO_FORMAT_YV12);
	if (x == NULL || PyDict_SetItemString(d, "ENC_VIDEO_FORMAT_YV12", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_VIDEO_FORMAT_YVU9);
	if (x == NULL || PyDict_SetItemString(d, "ENC_VIDEO_FORMAT_YVU9", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_VIDEO_FORMAT_YUY2);
	if (x == NULL || PyDict_SetItemString(d, "ENC_VIDEO_FORMAT_YUY2", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_VIDEO_FORMAT_YUY2_INVERTED);
	if (x == NULL || PyDict_SetItemString(d, "ENC_VIDEO_FORMAT_YUY2_INVERTED", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_VIDEO_FORMAT_UYVY);
	if (x == NULL || PyDict_SetItemString(d, "ENC_VIDEO_FORMAT_UYVY", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_NUM_VIDEO_FORMATS);
	if (x == NULL || PyDict_SetItemString(d, "ENC_NUM_VIDEO_FORMATS", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_VIDEO_NOISE_FILTER_OFF);
	if (x == NULL || PyDict_SetItemString(d, "ENC_VIDEO_NOISE_FILTER_OFF", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_VIDEO_NOISE_FILTER_LOW);
	if (x == NULL || PyDict_SetItemString(d, "ENC_VIDEO_NOISE_FILTER_LOW", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_VIDEO_NOISE_FILTER_HIGH);
	if (x == NULL || PyDict_SetItemString(d, "ENC_VIDEO_NOISE_FILTER_HIGH", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_NUM_NOISE_FILTER_SETTINGS);
	if (x == NULL || PyDict_SetItemString(d, "ENC_NUM_NOISE_FILTER_SETTINGS", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_TARGET_AUDIENCES_AUDIO);
	if (x == NULL || PyDict_SetItemString(d, "ENC_TARGET_AUDIENCES_AUDIO", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_TARGET_AUDIENCES_VIDEO);
	if (x == NULL || PyDict_SetItemString(d, "ENC_TARGET_AUDIENCES_VIDEO", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_TARGET_AUDIENCES_MULTIMEDIA);
	if (x == NULL || PyDict_SetItemString(d, "ENC_TARGET_AUDIENCES_MULTIMEDIA", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_NUM_TARGET_AUDIENCES_OPTIONS);
	if (x == NULL || PyDict_SetItemString(d, "ENC_NUM_TARGET_AUDIENCES_OPTIONS", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_TARGET_SETTINGS_BASIC);
	if (x == NULL || PyDict_SetItemString(d, "ENC_TARGET_SETTINGS_BASIC", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) ENC_NUM_TARGET_SETTINGS_TYPES);
	if (x == NULL || PyDict_SetItemString(d, "ENC_NUM_TARGET_SETTINGS_TYPES", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) IRMAEventMediaSample_URL);
	if (x == NULL || PyDict_SetItemString(d, "IRMAEventMediaSample_URL", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) IRMAEventMediaSample_Title);
	if (x == NULL || PyDict_SetItemString(d, "IRMAEventMediaSample_Title", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) IRMAEventMediaSample_Author);
	if (x == NULL || PyDict_SetItemString(d, "IRMAEventMediaSample_Author", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) IRMAEventMediaSample_Copyright);
	if (x == NULL || PyDict_SetItemString(d, "IRMAEventMediaSample_Copyright", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) IRMAImageMapMediaSample_SHAPE_NONE);
	if (x == NULL || PyDict_SetItemString(d, "IRMAImageMapMediaSample_SHAPE_NONE", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) IRMAImageMapMediaSample_SHAPE_RECTANGLE);
	if (x == NULL || PyDict_SetItemString(d, "IRMAImageMapMediaSample_SHAPE_RECTANGLE", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) IRMAImageMapMediaSample_SHAPE_CIRCLE);
	if (x == NULL || PyDict_SetItemString(d, "IRMAImageMapMediaSample_SHAPE_CIRCLE", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) IRMAImageMapMediaSample_SHAPE_POLYGON);
	if (x == NULL || PyDict_SetItemString(d, "IRMAImageMapMediaSample_SHAPE_POLYGON", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) IRMAImageMapMediaSample_ACTION_NONE);
	if (x == NULL || PyDict_SetItemString(d, "IRMAImageMapMediaSample_ACTION_NONE", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) IRMAImageMapMediaSample_ACTION_BROWSER_URL);
	if (x == NULL || PyDict_SetItemString(d, "IRMAImageMapMediaSample_ACTION_BROWSER_URL", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) IRMAImageMapMediaSample_ACTION_PLAYER_URL);
	if (x == NULL || PyDict_SetItemString(d, "IRMAImageMapMediaSample_ACTION_PLAYER_URL", x) < 0)
		goto error;
	Py_DECREF(x);
	x = PyLong_FromLong((long) IRMAImageMapMediaSample_ACTION_PLAYER_SEEK);
	if (x == NULL || PyDict_SetItemString(d, "IRMAImageMapMediaSample_ACTION_PLAYER_SEEK", x) < 0)
		goto error;
	Py_DECREF(x);
	
	/* Check for errors */
	if (PyErr_Occurred()) {
	  error:
		Py_FatalError("can't initialize module producer");
	}
}
