#include "std.h"
#include "PyCppApi.h"
#include "StdRma.h"

#include "Engine.h"

#include "os.h"

#include "StdApp.h"

#ifdef _MACINTOSH
#include <Events.h>
#include <Folders.h>
#include "macglue.h"
#endif

class EngineObject : public Object
	{
	public:
	MAKE_PY_CTOR(EngineObject)
	static TypeObject type;
	static PyObject *CreateInstance(PyObject *self, PyObject *args);
	static TypeObject* GetBaseType(){return &Object::type;}

	// PyMethods
	static PyObject *CreatePlayer(PyObject *self, PyObject *args);
	static PyObject *EventOccurred(PyObject *self, PyObject *args);


	static IRMAClientEngine* pEngine;
	static EngineObject* inst;

	protected:
	EngineObject();
	~EngineObject();
	virtual string repr();
	};

PyObject *EngineObject_CreateInstance(PyObject *self, PyObject *args)
	{return EngineObject::CreateInstance(self,args);}
void EngineObject_AddRef()
	{if(EngineObject::inst)Py_INCREF(EngineObject::inst);}
void EngineObject_Release()
	{if(EngineObject::inst)Py_DECREF(EngineObject::inst);}


IRMAClientEngine* EngineObject::pEngine=NULL;
EngineObject* EngineObject::inst=NULL;


EngineObject::EngineObject()
	{
	}

EngineObject::~EngineObject()
	{
	CloseEngine();
	}

PyObject *EngineObject::CreateInstance(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	if(EngineObject::inst)
		{
		Py_INCREF(EngineObject::inst);
		return EngineObject::inst;
		}
	EngineObject::inst=(EngineObject*)Object::make(EngineObject::type);
	return EngineObject::inst;
	}

string EngineObject::repr()
	{
	char buf[256];
	sprintf (buf," instance 0x%X",this);
	return Object::repr() + buf;
	}

/////////////////////////////////////////////
// PyMethods
PyObject* EngineObject::CreatePlayer(PyObject *self, PyObject *args)
	{
	extern PyObject *PlayerObject_CreateInstance(PyObject *self, PyObject *args);
	return PlayerObject_CreateInstance(self,args);
	}
	
PyObject* EngineObject::EventOccurred(PyObject *self, PyObject *args)
	{
	PNxEvent pn_event;
	PN_RESULT res;
#ifdef _MACINTOSH
	EventRecord ev;
#endif
	
	/* Event = PyArg_ParseTuple(blabla) */
#ifdef _MACINTOSH
	if( !PyArg_ParseTuple(args, "O&", PyMac_GetEventRecord, &ev) )
		return NULL;
	pn_event.event = ev.what;
	pn_event.param1 = &ev;
#else
	/* What _may_ work on unix is passing a zeroed struct. See the main program of
	** the minimal playback engine for details.
	** On Windows this magically seems to be unneeded at all.
	*/
	PyErr_SetString(PyExc_SystemError, 
		"rma PNxEvent mapping not implemented on this platform yet");
	return NULL;
#endif
	res = pEngine->EventOccurred(&pn_event);
	return Py_BuildValue("i", res);
	}

static struct PyMethodDef PyRMEngine_methods[] =
	{
	{"CreatePlayer",EngineObject::CreatePlayer,1},
	{"EventOccurred", EngineObject::EventOccurred,1},
	{NULL, 	NULL}
	};

TypeObject EngineObject::type("PyRMEngine", 
						  GetBaseType(), 
						  sizeof(EngineObject), 
						  PyRMEngine_methods, 
						  GET_PY_CTOR(EngineObject));



/////////////////////////////////////////////////////////////
static FPRMCREATEENGINE m_fpCreateEngine;
static FPRMCLOSEENGINE m_fpCloseEngine;
static HINSTANCE hDll;
static PN_RESULT theErr = PNR_OK;

inline bool cleanup(){CloseEngine();return false;}

static bool CreateEngine()
	{
	if( EngineObject::pEngine) return true;
    // initialize the globals
    m_fpCreateEngine = NULL;
    m_fpCloseEngine	= NULL;
    
    // prepare/load the RMACore module
    char   szDllName[_MAX_PATH];
    
#if defined(_UNIX)
    strcpy(szDllName, "rmacore.dll");

#elif defined(_MACINTOSH)
    // ASSUME rmacore is in System Folder:Extensions:Real:Common
    // SHOULD obtain value from preference file
    OSErr	macErr;

    // set szDllName to empty string
    szDllName[0] = '\0'; 

    // find the Extensions folder
    short	vRefNum;
    long	dirID;
#if 0
    /* Older G2 beta's had the engine in the extensions folder */
    macErr = FindFolder (kOnSystemDisk, kExtensionFolderType, kDontCreateFolder, &vRefNum, &dirID);
#else
    macErr = FindFolder (kOnSystemDisk, kApplicationSupportFolderType, kDontCreateFolder, &vRefNum, &dirID);
#endif

    // find the path of the Extensions folder
    DirInfo	block;
    Str63	directoryName;
    char	tmpName[_MAX_PATH];

    block.ioDrParID = dirID;
    block.ioNamePtr = directoryName;
    do
		{
		block.ioVRefNum = vRefNum;
		block.ioFDirIndex = -1;
		block.ioDrDirID = block.ioDrParID;

		macErr = PBGetCatInfoSync ((CInfoPBPtr)&block);
		if (macErr == noErr)
			{
			strcpy (tmpName, szDllName);
			szDllName[0] = '\0';
			strncat (szDllName, (char*)&directoryName[1], directoryName[0]);
			if (strlen(tmpName))
				{
				strcat (szDllName, ":");
				strcat (szDllName, tmpName);
				}
			}
		}
    while ((macErr == noErr) && (block.ioDrDirID != 2)); // 2 means root directory of a volume
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
		"Software\\RealNetworks\\Preferences\\DT_Common", &hKey)) 
    { 
	// get the path to pnen 
	hRes = RegQueryValue(hKey, "", szDllName, (long *)&bufSize); 
	RegCloseKey(hKey); 
    }

    strcat(szDllName, "pnen3260.dll");

#elif defined(_WIN16) 
    strcpy(szDllName, "pnen1660.dll");
#else
#error Unknown platform
#endif
    
    if (!(hDll = LoadLibrary(szDllName))) 
    {
	theErr = PNR_FAILED;
#if defined(_UNIX)
 	fprintf(stdout, "Failed to load the 'rmacore.so.6.0' shared library\n");
	fprintf(stdout, dlerror());
#else
 	fprintf(stdout, "Failed to load the '%s' library.\n", szDllName);
#endif
	return cleanup();
    }

    fprintf(stdout, "Loaded rmacore\n");

    // retrieve the proc addresses from the module
    m_fpCreateEngine = (FPRMCREATEENGINE) GetProcAddress(hDll, "CreateEngine");
    m_fpCloseEngine  = (FPRMCLOSEENGINE)  GetProcAddress(hDll, "CloseEngine");
 
    if (m_fpCreateEngine == NULL ||
 		m_fpCloseEngine == NULL)
		{
		theErr = PNR_FAILED;
		return cleanup();
		}

    // create client engine 
    if (PNR_OK != m_fpCreateEngine((IRMAClientEngine**) & EngineObject::pEngine))
		{
		theErr = PNR_FAILED;
		return cleanup();
		}
	return true;
	}

IRMAClientEngine* GetEngine()
	{
	if(! EngineObject::pEngine)CreateEngine();
	return  EngineObject::pEngine;
	}

void CloseEngine()
	{   
    if ( EngineObject::pEngine)
		{
		m_fpCloseEngine( EngineObject::pEngine);
		 EngineObject::pEngine = NULL;
		}
    if (hDll)
		{
		FreeLibrary(hDll);
		hDll = NULL;
		}

	// set static var to NULL again
	 EngineObject::inst=NULL;
	}


