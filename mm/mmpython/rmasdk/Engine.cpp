#include "Std.h"
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

class EngineObject : public RMAObject {
public:
	MAKE_PY_CTOR(EngineObject)
	static TypeObject type;
	static PyObject *CreateInstance(PyObject *self, PyObject *args);
	static TypeObject* GetBaseType(){return &RMAObject::type;}

	// PyMethods
	static PyObject *CreatePlayer(PyObject *self, PyObject *args);
	static PyObject *EventOccurred(PyObject *self, PyObject *args);

	static IRMAClientEngine *pEngine;
	static EngineObject *inst;

	static FPRMCREATEENGINE fpCreateEngine;
	static FPRMCLOSEENGINE fpCloseEngine;
	static HINSTANCE hDll;

protected:
	EngineObject();
	~EngineObject();
#if !defined(_ABIO32) || _ABIO32 == 0
	virtual string repr();
#else
	virtual char *repr();
#endif
};

IRMAClientEngine *EngineObject::pEngine = NULL;
EngineObject *EngineObject::inst = NULL;
FPRMCREATEENGINE EngineObject::fpCreateEngine = NULL;
FPRMCLOSEENGINE EngineObject::fpCloseEngine = NULL;
HINSTANCE EngineObject::hDll = NULL;

void
CloseEngine()
{   
	if (EngineObject::pEngine) {
		EngineObject::fpCloseEngine(EngineObject::pEngine);
		EngineObject::pEngine = NULL;
	}
	if (EngineObject::hDll) {
		FreeLibrary(EngineObject::hDll);
		EngineObject::hDll = NULL;
	}

	// set static var to NULL again
	EngineObject::inst = NULL;
}

inline bool
cleanup()
{
	CloseEngine();
	return false;
}

static bool
CreateEngine()
{
	if (EngineObject::pEngine)
		return true;
	// initialize the globals
	EngineObject::fpCreateEngine = NULL;
	EngineObject::fpCloseEngine = NULL;

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
	}

	strcat(szDllName, "pnen3260.dll");

#elif defined(_WIN16) 
	strcpy(szDllName, "pnen1660.dll");
#else
#error Unknown platform
#endif
    
	if ((EngineObject::hDll = LoadLibrary(szDllName)) == NULL) {
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
	EngineObject::fpCreateEngine = (FPRMCREATEENGINE) GetProcAddress(EngineObject::hDll, "CreateEngine");
	EngineObject::fpCloseEngine  = (FPRMCLOSEENGINE)  GetProcAddress(EngineObject::hDll, "CloseEngine");
 
	if (EngineObject::fpCreateEngine == NULL ||
	    EngineObject::fpCloseEngine == NULL) {
		return cleanup();
	}

	// create client engine 
	if (PNR_OK != EngineObject::fpCreateEngine((IRMAClientEngine**) & EngineObject::pEngine)) {
		return cleanup();
	}
	return true;
}

EngineObject::EngineObject()
{
}

EngineObject::~EngineObject()
{
	CloseEngine();
}

PyObject *
EngineObject::CreateInstance(PyObject *self, PyObject *args)
{
	CHECK_NO_ARGS(args);
	if (EngineObject::inst) {
		Py_INCREF(EngineObject::inst);
		return EngineObject::inst;
	}
	EngineObject::inst= (EngineObject*) RMAObject::make(EngineObject::type);
	if (!CreateEngine()) {
		PyErr_SetString(PyExc_IOError, "CreateEngine failed");
		Py_DECREF(EngineObject::inst);
		EngineObject::inst = NULL;
		return NULL;
	}
	return EngineObject::inst;
}

PyObject *
EngineObject_CreateInstance(PyObject *self, PyObject *args)
{
	return EngineObject::CreateInstance(self, args);
}

#if !defined(_ABIO32) || _ABIO32 == 0
string
#else
char *
#endif
EngineObject::repr()
{
	char buf[256];
#if !defined(_ABIO32) || _ABIO32 == 0
	sprintf (buf, " instance 0x%X", this);
	return RMAObject::repr() + buf;
#else
	char *rep = RMAObject::repr();
	sprintf (buf, "%s instance 0x%X", rep, this);
	free(rep);
	return strdup(buf);
#endif
}

PyObject *
EngineObject::CreatePlayer(PyObject *self, PyObject *args)
{
	extern PyObject *PlayerObject_CreateInstance(PyObject *self, PyObject *args);
	return PlayerObject_CreateInstance(self,args);
}
	
PyObject *
EngineObject::EventOccurred(PyObject *self, PyObject *args)
{
	PNxEvent pn_event;
	PN_RESULT res;
	
	/* Event = PyArg_ParseTuple(blabla) */
#ifdef _MACINTOSH
	EventRecord ev;
	if (!PyArg_ParseTuple(args, "O&", PyMac_GetEventRecord, &ev))
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

static struct PyMethodDef PyRMEngine_methods[] = {
	{"CreatePlayer",EngineObject::CreatePlayer,1},
	{"EventOccurred", EngineObject::EventOccurred,1},
	{NULL, 	NULL},
};

TypeObject EngineObject::type("PyRMEngine",
			      GetBaseType(),
			      sizeof(EngineObject),
			      PyRMEngine_methods,
			      GET_PY_CTOR(EngineObject));

IRMAClientEngine *
GetEngine(PyObject *engine)
{
	return ((EngineObject *) engine)->pEngine;
}
