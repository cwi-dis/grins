
#include "mpegex.h"



#define MAX_CHAN  10


MCI_AVI_STRUCT  *ChanTable[MAX_CHAN];


static PyObject *MpegExError;

BOOL first;

PyIMPORT CWnd *GetWndPtr(PyObject *);


#ifdef __cplusplus
extern "C" {
#endif


void init()
{
	TRACE("Initializing...\n");
	for (UINT k=0; k<MAX_CHAN; k++)
		ChanTable[k] = NULL;

	first = FALSE;

}

static PyObject*  py_mpeg_arm(PyObject *self,PyObject *args)
{
	TRACE("Entering mpeg_arm\n");
	if (first)
		init();

	UINT k;
	CWnd *Wnd; 
	BOOL bStretch, bRet;
	PyObject *Ob = Py_None;
	char *FileName;
	

	if(!PyArg_ParseTuple(args, "Osi", &Ob, &FileName, &bStretch))
	{
		Py_INCREF(Py_None);
		AfxMessageBox("Error", MB_OK);
		return Py_None;return NULL;
	
	}

	Wnd = GetWndPtr(Ob);
	TRACE("Retrieved: Handle %X filename %s", Wnd->m_hWnd, FileName);

	for (k=0; k<MAX_CHAN; k++)
	{
		if (ChanTable[k] == NULL)
		{
			ChanTable[k] = (MCI_AVI_STRUCT*) malloc(sizeof(MCI_AVI_STRUCT));
			TRACE("New struct allocated, index %d\n", k);
			break;
		}
		if (k == MAX_CHAN-1)
			AfxMessageBox("Unable to activate another channel", MB_OK);

	}


	ChanTable[k]->hWndParent = Wnd->m_hWnd;
	strcpy(ChanTable[k]->szFileName, FileName);
	TRACE("Filename in struct is: %s\n", ChanTable[k]->szFileName);
	ChanTable[k]->fReverse=FALSE;
    ChanTable[k]->fNotify=TRUE;
	ChanTable[k]->fStretch = bStretch;
 
	bRet = AviOpen(ChanTable[k]);

	if (! bRet)
	{
		free(ChanTable[k]);
		ChanTable[k] = NULL;
	}

	//strcpy(mciAviInfo.szFileName, PyString_AsString(PyFile_Name(file)));
	//strcpy(FileName, PyString_AsString(PyFile_Name(file)));
	
	/*TRACE("Quick test:\n");

	for (UINT j=0; j<MAX_CHAN; j++)
	{
		if (ChanTable[j] != NULL)
			TRACE("Index-Handle-File: %d %X %s\n", j, ChanTable[j]->hWndParent, ChanTable[j]->szFileName);
	}*/	

	if (!bRet)
	return Py_BuildValue("i", -1);
	
	return Py_BuildValue("i", k);
}

static PyObject* py_mpeg_play(PyObject *self, PyObject *args)
{
	TRACE("Entering mpeg_play\n");

	BOOL bRet;
	int k;
	PyObject *Ob = Py_None;
		
	if(!PyArg_ParseTuple(args, "i", &k))
	{
		Py_INCREF(Py_None);
		AfxMessageBox("Error", MB_OK);
		return Py_None;return NULL;
	
	}

	if (ChanTable[k] != NULL)
	bRet = AviPlay(ChanTable[k]);
	TRACE("Playing struct with index %d\n", k);
	
	return Py_BuildValue("i", bRet);
}

static PyObject* py_mpeg_playstop(PyObject *self, PyObject *args)
{
	TRACE("Entering mpeg_playstop\n");

	BOOL bRet;
	int k;
	PyObject *Ob = Py_None;
	
	if(!PyArg_ParseTuple(args, "i", &k))
	{
		Py_INCREF(Py_None);
		AfxMessageBox("Error", MB_OK);
		return Py_None;return NULL;
	
	}

	if (ChanTable[k] != NULL)
	bRet = AviStop(ChanTable[k]);				
	TRACE("Stopping struct indexed %d\n", k);

	return Py_BuildValue("i", bRet);
}



static PyObject* py_mpeg_finished(PyObject *self, PyObject *args)
{
	TRACE("Entering mpeg_finished\n");

	BOOL bRet;
	int k;
	PyObject *Ob = Py_None;

	
	if(!PyArg_ParseTuple(args, "i", &k))
	{
		Py_INCREF(Py_None);
		AfxMessageBox("Error", MB_OK);
		return Py_None;return NULL;
	
	}

	if (ChanTable[k] != NULL)
	bRet = AviClose(ChanTable[k]);
				
	TRACE("About to free struct indexed %d\n", k);
	free(ChanTable[k]);
	ChanTable[k] = NULL;

	
	return Py_BuildValue("i", bRet);
}


static PyObject* py_mpeg_position(PyObject *self, PyObject *args)
{
	TRACE("Entering mpeg_position\n");

	BOOL bRet;
	int k;
	PyObject *Ob = Py_None;

	
	if(!PyArg_ParseTuple(args, "i", &k))
	{
		Py_INCREF(Py_None);
		AfxMessageBox("Error", MB_OK);
		return Py_None;return NULL;
	
	}

	if (ChanTable[k] != NULL)
	{
		BOOL b1 = AviStop(ChanTable[k]);
		positionMovie(ChanTable[k]);
		BOOL b2 = AviPlay(ChanTable[k]);
		bRet = b1*b2;
	}

	return Py_BuildValue("i", bRet);
}

static PyMethodDef MpegExMethods[] = 
{
	{ "arm", (PyCFunction)py_mpeg_arm, 1},
	{ "play",(PyCFunction)py_mpeg_play, 1},
	{ "finished", (PyCFunction)py_mpeg_finished, 1},
	{ "stop", (PyCFunction)py_mpeg_playstop, 1},
	{ "position", (PyCFunction)py_mpeg_position, 1},
	{ NULL, NULL }
};


PyEXPORT 
void initmpegex()
{
	PyObject *m, *d;
	first = TRUE;
	m = Py_InitModule("mpegex", MpegExMethods);
	d = PyModule_GetDict(m);
	MpegExError = PyString_FromString("mpegex.error");
	PyDict_SetItemString(d, "error", MpegExError);
}

#ifdef __cplusplus
}
#endif


