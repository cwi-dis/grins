
/*************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include "Python.h"

#include <windows.h>

#include "wininet.h"

#pragma comment (lib,"wininet.lib")


static PyObject *ErrorObject;

static void seterror(const char *msg){PyErr_SetString(ErrorObject, msg);}
static void seterror(const char *funcname, const char *msg)
	{
	PyErr_Format(ErrorObject, "%s failed, %s", funcname, msg);
	PyErr_SetString(ErrorObject, msg);
	}
static void seterror(const char *funcname, DWORD err)
{
	char* pszmsg;
	FormatMessage( 
		 FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
		 NULL,
		 err,
		 MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
		 (LPTSTR) &pszmsg,
		 0,
		 NULL 
		);
	PyErr_Format(ErrorObject, "%s failed, error = %x, %s", funcname, err, pszmsg);
	LocalFree(pszmsg);
}

////////////////////////////////////////
///////////////////////////////////////////
// Objects declarations

//
typedef struct {
	PyObject_HEAD
	HINTERNET h;
} InternetSessionObject;

staticforward PyTypeObject InternetSessionType;

static InternetSessionObject *
newInternetSessionObject()
{
	InternetSessionObject *self = PyObject_NEW(InternetSessionObject, &InternetSessionType);
	if (self == NULL) return NULL;
	self->h = NULL;
	return self;
}


///////////////////////////////////////////
///////////////////////////////////////////
// Objects exported

////////////////////////////////////////////
// InternetSession object 

static char InternetSession_Ping__doc__[] =
""
;
static PyObject *
InternetSession_Ping(InternetSessionObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	Py_INCREF(Py_None);
	return Py_None;
}


static struct PyMethodDef InternetSession_methods[] = {
	{"Ping", (PyCFunction)InternetSession_Ping, METH_VARARGS, InternetSession_Ping__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
InternetSession_dealloc(InternetSessionObject *self)
{
	if(self->h) InternetCloseHandle(self->h);
	self->h = NULL;
	PyMem_DEL(self);
}

static PyObject *
InternetSession_getattr(InternetSessionObject *self, char *name)
{
	return Py_FindMethod(InternetSession_methods, (PyObject *)self, name);
}

static char InternetSessionType__doc__[] =
""
;

static PyTypeObject InternetSessionType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"InternetSession",			/*tp_name*/
	sizeof(InternetSessionObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)InternetSession_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)InternetSession_getattr,	/*tp_getattr*/
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
	InternetSessionType__doc__ /* Documentation string */
};

// End of code for InternetSession object 
////////////////////////////////////////////



///////////////////////////////////////////
///////////////////////////////////////////
// MODULE

static char InternetGetConnectedState__doc__[] =
"Retrieves the connected state of the local system."
;
static PyObject*
InternetGetConnectedState(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	DWORD dwFlags = 0;
	BOOL res = InternetGetConnectedState(&dwFlags, 0);
	return Py_BuildValue("ii", res, dwFlags);
}

static char InternetCheckConnection__doc__[] =
"Allows an application to check if a connection to the Internet can be established."
;
static PyObject*
InternetCheckConnection(PyObject *self, PyObject *args)
{
	char *pszURL = NULL;
	DWORD dwFlags = 0; // 0 or 1 == FLAG_ICC_FORCE_CONNECTION;
	if (!PyArg_ParseTuple(args,"|si", &pszURL, &dwFlags))
		return NULL;
	DWORD dwReserved = 0;
	BOOL res = InternetCheckConnection(pszURL, dwFlags, dwReserved);
	return Py_BuildValue("i", res);
}


static char InternetAttemptConnect__doc__[] =
"Attempts to make a connection to the Internet."
;
static PyObject*
InternetAttemptConnect(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) return NULL;
	DWORD dwReserved = 0;
	DWORD res;
	Py_BEGIN_ALLOW_THREADS
	res = InternetAttemptConnect(dwReserved);
	Py_END_ALLOW_THREADS
	if(res!=ERROR_SUCCESS){
		seterror("InternetAttemptConnect", res);
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char InternetGoOnline__doc__[] =
"Prompts the user for permission to initiate connection to a URL."
;
static PyObject*
InternetGoOnline(PyObject *self, PyObject *args)
{
	char *pszURL;
	HWND hwnd;
	if (!PyArg_ParseTuple(args,"si", &pszURL, &hwnd))
		return NULL;
	DWORD dwReserved = 0;
	BOOL res;
	Py_BEGIN_ALLOW_THREADS
	res = InternetGoOnline(pszURL, hwnd, dwReserved);
	Py_END_ALLOW_THREADS
	return Py_BuildValue("i", res);
}

static char CreateInternetSession__doc__[] =
""
;
static PyObject*
CreateInternetSession(PyObject *self, PyObject *args)
{
    char *pszAgent = NULL;
    DWORD dwAccessType = PRE_CONFIG_INTERNET_ACCESS;
    char *pszProxyName = NULL;
    char *pszProxyBypass = NULL;
    DWORD dwFlags = 0;
	if (!PyArg_ParseTuple(args, "|sissi", &pszAgent, &dwAccessType, &pszProxyName, &pszProxyBypass, &dwFlags))
		return NULL;

	InternetSessionObject *obj = newInternetSessionObject();
	if (obj == NULL) return NULL;
	
	obj->h = InternetOpen(pszAgent,dwAccessType,pszProxyName,pszProxyBypass,dwFlags);
	if(obj->h==NULL){
		seterror("CreateInternetSession::InternetOpen", GetLastError());
		return NULL;
		}
	return (PyObject*)obj;
}

static struct PyMethodDef wininet_methods[] = {
	{"GetConnectedState", (PyCFunction)InternetGetConnectedState, METH_VARARGS, InternetGetConnectedState__doc__},
	//{"CheckConnection", (PyCFunction)InternetCheckConnection, METH_VARARGS, InternetCheckConnection__doc__},
	{"AttemptConnect", (PyCFunction)InternetAttemptConnect, METH_VARARGS, InternetAttemptConnect__doc__},
	{"GoOnline", (PyCFunction)InternetGoOnline, METH_VARARGS, InternetGoOnline__doc__},
	{"CreateInternetSession", (PyCFunction)CreateInternetSession, METH_VARARGS, CreateInternetSession__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

/////////////////////////////////////

struct constentry {char* s;int n;};

static struct constentry _open_type[] ={
	{"INTERNET_OPEN_TYPE_PRECONFIG", INTERNET_OPEN_TYPE_PRECONFIG},
	{"INTERNET_OPEN_TYPE_DIRECT", INTERNET_OPEN_TYPE_DIRECT},
	{"INTERNET_OPEN_TYPE_PROXY", INTERNET_OPEN_TYPE_PROXY},
	{"INTERNET_OPEN_TYPE_PRECONFIG_WITH_NO_AUTOPROXY", INTERNET_OPEN_TYPE_PRECONFIG_WITH_NO_AUTOPROXY},

	{"PRE_CONFIG_INTERNET_ACCESS", PRE_CONFIG_INTERNET_ACCESS},
	{"LOCAL_INTERNET_ACCESS", LOCAL_INTERNET_ACCESS},
	{"CERN_PROXY_INTERNET_ACCESS", CERN_PROXY_INTERNET_ACCESS},

	{NULL,0}
	};

// Flags for InternetGetConnectedState
static struct constentry _connection[] ={
	{"INTERNET_CONNECTION_MODEM", INTERNET_CONNECTION_MODEM},
	{"INTERNET_CONNECTION_LAN", INTERNET_CONNECTION_LAN},
	{"INTERNET_CONNECTION_PROXY", INTERNET_CONNECTION_PROXY},
	{"INTERNET_CONNECTION_MODEM_BUSY", INTERNET_CONNECTION_MODEM_BUSY},
	{NULL,0}
	};

static struct constentry _flags[] ={
	{"INTERNET_FLAG_RELOAD", INTERNET_FLAG_RELOAD},					
	{"INTERNET_FLAG_RAW_DATA", INTERNET_FLAG_RAW_DATA},					
	{"INTERNET_FLAG_EXISTING_CONNECT", INTERNET_FLAG_EXISTING_CONNECT},			
	{"INTERNET_FLAG_ASYNC", INTERNET_FLAG_ASYNC},						
	{"INTERNET_FLAG_PASSIVE", INTERNET_FLAG_PASSIVE},					
	{"INTERNET_FLAG_NO_CACHE_WRITE", INTERNET_FLAG_NO_CACHE_WRITE},			
	{"INTERNET_FLAG_DONT_CACHE", INTERNET_FLAG_DONT_CACHE},				
	{"INTERNET_FLAG_MAKE_PERSISTENT", INTERNET_FLAG_MAKE_PERSISTENT},			
	{"INTERNET_FLAG_FROM_CACHE", INTERNET_FLAG_FROM_CACHE},				
	{"INTERNET_FLAG_OFFLINE", INTERNET_FLAG_OFFLINE},					
	{"INTERNET_FLAG_SECURE", INTERNET_FLAG_SECURE},					
	{"INTERNET_FLAG_KEEP_CONNECTION", INTERNET_FLAG_KEEP_CONNECTION},			
	{"INTERNET_FLAG_NO_AUTO_REDIRECT", INTERNET_FLAG_NO_AUTO_REDIRECT},			
	{"INTERNET_FLAG_READ_PREFETCH", INTERNET_FLAG_READ_PREFETCH},				
	{"INTERNET_FLAG_NO_COOKIES", INTERNET_FLAG_NO_COOKIES},				
	{"INTERNET_FLAG_NO_AUTH", INTERNET_FLAG_NO_AUTH},					
	{"INTERNET_FLAG_CACHE_IF_NET_FAIL", INTERNET_FLAG_CACHE_IF_NET_FAIL},			
	{"INTERNET_FLAG_IGNORE_REDIRECT_TO_HTTP", INTERNET_FLAG_IGNORE_REDIRECT_TO_HTTP},   
	{"INTERNET_FLAG_IGNORE_REDIRECT_TO_HTTPS ", INTERNET_FLAG_IGNORE_REDIRECT_TO_HTTPS}, 
	{"INTERNET_FLAG_IGNORE_CERT_DATE_INVALID", INTERNET_FLAG_IGNORE_CERT_DATE_INVALID},  
	{"INTERNET_FLAG_IGNORE_CERT_CN_INVALID", INTERNET_FLAG_IGNORE_CERT_CN_INVALID},    
	{"INTERNET_FLAG_RESYNCHRONIZE", INTERNET_FLAG_RESYNCHRONIZE},				
	{"INTERNET_FLAG_HYPERLINK", INTERNET_FLAG_HYPERLINK},					 
	{"INTERNET_FLAG_NO_UI", INTERNET_FLAG_NO_UI},						
	{"INTERNET_FLAG_PRAGMA_NOCACHE", INTERNET_FLAG_PRAGMA_NOCACHE},			
	{"INTERNET_FLAG_CACHE_ASYNC", INTERNET_FLAG_CACHE_ASYNC},				
	{"INTERNET_FLAG_FORMS_SUBMIT", INTERNET_FLAG_FORMS_SUBMIT},				
	{"INTERNET_FLAG_NEED_FILE", INTERNET_FLAG_NEED_FILE},					
	{"INTERNET_FLAG_MUST_CACHE_REQUEST", INTERNET_FLAG_MUST_CACHE_REQUEST},		
	{"INTERNET_FLAG_TRANSFER_ASCII", INTERNET_FLAG_TRANSFER_ASCII},			
	{"INTERNET_FLAG_TRANSFER_BINARY", INTERNET_FLAG_TRANSFER_BINARY},			
	{NULL,0}
	};


// add symbolic constants of enum
static int 
SetItemEnum(PyObject *d,constentry e[])
	{
	PyObject *x;
	for(int i=0;e[i].s;i++)
		{
		x = PyInt_FromLong((long) e[i].n);
		if (x == NULL || PyDict_SetItemString(d, e[i].s, x) < 0)
			return -1;
		Py_DECREF(x);
		}
	return 0;
	}

#define FATAL_ERROR_IF(exp) if(exp){Py_FatalError("can't initialize module wininet");return;}	

static char wininet_module_documentation[] =
"Windows WinInet module"
;

extern "C" __declspec(dllexport)
void initwininet()
{
	PyObject *m, *d;
	bool bPyErrOccurred = false;
	
	// Create the module and add the functions
	m = Py_InitModule4("wininet", wininet_methods,
		wininet_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	// add 'error'
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("wininet.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	// add symbolic constants
	FATAL_ERROR_IF(SetItemEnum(d,_open_type)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_connection)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_flags)<0)

	// Check for errors
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module wininet");
}
