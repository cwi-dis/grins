
#include "mpegex.h"



#define MAX_CHAN  10


MCI_AVI_STRUCT  *ChanTable[MAX_CHAN];


static PyObject *MpegExError;

BOOL first;

PyIMPORT CWnd *GetWndPtr(PyObject *);


#ifdef __cplusplus
extern "C" {
#endif

void MpegExErrorFunc(char *str);

void init()
{
	TRACE("Initializing...\n");
	for (UINT k=0; k<MAX_CHAN; k++)
		ChanTable[k] = NULL;

	first = FALSE;

}

static PyObject*  py_mpeg_arm(PyObject *self, PyObject *args)
{
	TRACE("Entering mpeg_arm\n");
	if (first)
		init();

	UINT k;
	CWnd *Wnd; 
	BOOL bStretch, bRet, center;
	PyObject *Ob = Py_None;
	char *FileName;
	float scale;
	

	if(!PyArg_ParseTuple(args, "Osifi", &Ob, &FileName, &bStretch, &scale, &center))
	{
		Py_INCREF(Py_None);
		//AfxMessageBox("Error", MB_OK);
		MpegExErrorFunc("py_mpeg_prepare(parent, filename, Stretch, scale, center)");
		return Py_None;
	
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
	ChanTable[k]->format = 1;
	ChanTable[k]->scale = scale;
	ChanTable[k]->center = center;
 
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
	long d;
	PyObject *Ob = Py_None;
		
	if(!PyArg_ParseTuple(args, "il", &k, &d))
	{
		Py_INCREF(Py_None);
		//AfxMessageBox("Error", MB_OK);
		MpegExErrorFunc("py_mpeg_play(file identifier, duration)");
		return Py_None;
	}

	if (ChanTable[k] != NULL)
	{
		ChanTable[k]->lAVIduration = d;
		bRet = AviPlay(ChanTable[k]);
	}
	
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
		//AfxMessageBox("Error", MB_OK);
		MpegExErrorFunc("py_mpeg_playstop(file identifier)");
		return Py_None;
	
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
		//AfxMessageBox("Error", MB_OK);
		MpegExErrorFunc("py_mpeg_finished(file identifier)");
		return Py_None;	
	}

	if (ChanTable[k] != NULL)
	bRet = AviClose(ChanTable[k]);
				
	TRACE("About to free struct indexed %d\n", k);
	free(ChanTable[k]);
	ChanTable[k] = NULL;

	
	return Py_BuildValue("i", bRet);
}



static PyObject* py_mpeg_GetFrame(PyObject *self, PyObject *args)
{
	TRACE("Entering mpeg_playstop\n");

	int k;
	long bRet = -1;
	PyObject *Ob = Py_None;
	
	if(!PyArg_ParseTuple(args, "i", &k))
	{
		Py_INCREF(Py_None);
		//AfxMessageBox("Error", MB_OK);
		MpegExErrorFunc("py_mpeg_GetFrame(file identifier)");
		return Py_None;
	
	}

	if (ChanTable[k] != NULL)
		bRet = AviFrame(ChanTable[k]);				
	

	return Py_BuildValue("l", bRet);
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
		//AfxMessageBox("Error", MB_OK);
		MpegExErrorFunc("py_mpeg_position(file identifier)");
		return Py_None;
	
	}

	if (ChanTable[k] != NULL)
	{
		// It seems that there is no need to stop and restatr the movie
		// Just place the window
		//BOOL b1 = AviStop(ChanTable[k]);
		positionMovie(ChanTable[k]);
		//BOOL b2 = AviPlay(ChanTable[k]);
		//bRet = b1*b2;
		bRet=1;
	}

	return Py_BuildValue("i", bRet);
}

static PyObject* py_mpeg_duration(PyObject *self, PyObject *args)
{
	TRACE("Entering mpeg_duration\n");

	int bRet;
	int k;
	PyObject *Ob = Py_None;

	
	if(!PyArg_ParseTuple(args, "i", &k))
	{
		Py_INCREF(Py_None);
		//AfxMessageBox("Function Usage : Mpeg Duration(Index)", MB_OK);
		MpegExErrorFunc("py_mpeg_duration(file identifier)");
		return Py_None;
	
	}

	bRet = (int) AviDuration(ChanTable[k]);
	 
	
	return Py_BuildValue("i", bRet);
}

static PyObject* py_mpeg_seekstart(PyObject *self, PyObject *args)
{
	TRACE("Entering mpeg_seekstart\n");

	BOOL bRet;
	int k;
	PyObject *Ob = Py_None;
	
	if(!PyArg_ParseTuple(args, "i", &k))
	{
		Py_INCREF(Py_None);
		MpegExErrorFunc("py_mpeg_seekstart(file identifier)");
		//AfxMessageBox("Error", MB_OK);
		return Py_None;
	}

	if (ChanTable[k] != NULL){
		ChanTable[k]->iSeekThere = 0;
		bRet = AviSeek(ChanTable[k]);				
	}

	TRACE("Rewind struct indexed %d\n", k);

	return Py_BuildValue("i", bRet);
}

static PyObject* py_mpeg_seek(PyObject *self, PyObject *args)
{
	TRACE("Entering mpeg_seek\n");

	BOOL bRet;
	int k, d;
	PyObject *Ob = Py_None;
	
	if(!PyArg_ParseTuple(args, "ii", &k, &d))
	{
		Py_INCREF(Py_None);
		MpegExErrorFunc("py_mpeg_seek(file identifier, position)");
		//AfxMessageBox("Error", MB_OK);
		return Py_None;
	}

	if (ChanTable[k] != NULL)
	{
		ChanTable[k]->iSeekThere = d;
		bRet = AviSeek(ChanTable[k]);				
	}

	TRACE("Rewind struct indexed %d\n", k);

	return Py_BuildValue("i", bRet);
}


static PyObject* py_mpeg_Update(PyObject *self, PyObject *args)
{
	int bRet;
	int k;
	PyObject *Ob = Py_None;

	
	if(!PyArg_ParseTuple(args, "i", &k))
	{
		Py_INCREF(Py_None);
		//AfxMessageBox("Function Usage : Mpeg Duration(Index)", MB_OK);
		MpegExErrorFunc("Update(file identifier)");
		return Py_None;
	
	}

	bRet = (int) AviUpdate(ChanTable[k]);
	 
	
	return Py_BuildValue("i", bRet);
}


static PyObject*  py_mpeg_SizeOfImage(PyObject *self, PyObject *args)
{
	CWnd *Wnd; 
	PyObject *Ob = Py_None;
	char *FileName;
	int bRet = 0;
	MCI_AVI_STRUCT* temp = NULL;
	RECT rc;
	
	if(!PyArg_ParseTuple(args, "Os", &Ob, &FileName))
	{
		Py_INCREF(Py_None);
		MpegExErrorFunc("SizeOfImage(parent, filename)");
		return Py_None;
	
	}

	Wnd = GetWndPtr(Ob);
	
	temp = (MCI_AVI_STRUCT*) malloc(sizeof(MCI_AVI_STRUCT));
	
	temp->hWndParent = Wnd->m_hWnd;
	strcpy(temp->szFileName, FileName);
	temp->fReverse=FALSE;
    temp->fNotify=TRUE;
	temp->fStretch = 0;
	temp->format = 1;
	temp->scale = 0;
	temp->center = 0;
 
	bRet = AviOpen(temp);

	if (! bRet)
	{
		free(temp);
		temp = NULL;
		return Py_BuildValue("ll", 0, 0);
	}

	AviSize(temp, &rc);
	AviClose(temp);

	free(temp);
	temp = NULL;
	
	return Py_BuildValue("ll", rc.right, rc.bottom);
}



static PyMethodDef MpegExMethods[] = 
{
	{ "arm", (PyCFunction)py_mpeg_arm, 1},
	{ "play",(PyCFunction)py_mpeg_play, 1},
	{ "finished", (PyCFunction)py_mpeg_finished, 1},
	{ "stop", (PyCFunction)py_mpeg_playstop, 1},
	{ "position", (PyCFunction)py_mpeg_position, 1},
	{ "GetFrame", (PyCFunction)py_mpeg_GetFrame, 1},
	{ "GetDuration",(PyCFunction)py_mpeg_duration,1},
	{ "seek", (PyCFunction)py_mpeg_seek, 1},
	{ "seekstart", (PyCFunction)py_mpeg_seekstart, 1},
	{ "Update", (PyCFunction)py_mpeg_Update, 1},
	{ "SizeOfImage", (PyCFunction)py_mpeg_SizeOfImage, 1},
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

void MpegExErrorFunc(char *str)
{
	PyErr_SetString (MpegExError, str);
	PyErr_Print();
}

#ifdef __cplusplus
}
#endif


