#include "stdafx.h"

#include "mcidll.h"
#include "win32win.h"


#include "moddef.h"
DECLARE_PYMODULECLASS(Mpegex);
IMPLEMENT_PYMODULECLASS(Mpegex,GetMpegex,"Mpegex Module Wrapper pPyObjject");

///////////////////////////////////
#define MAX_CHAN  10
static MCI_AVI_STRUCT  *ChanTable[MAX_CHAN];
static BOOL first=TRUE;

static void init()
{
	for (UINT k=0; k<MAX_CHAN; k++)
		ChanTable[k] = NULL;
	first = FALSE;
}

static PyObject*  py_mpeg_arm(PyObject *self, PyObject *args)
{
	if (first) init();
    
	PyObject *pPyObj;
	char *FileName;
	BOOL bStretch,center;
	float scale;
	long clipbegin, clipend;

	if(!PyArg_ParseTuple(args, "Osifill", &pPyObj, &FileName, &bStretch, &scale, &center, &clipbegin, &clipend))
		RETURN_ERR("py_mpeg_prepare");


	CWnd *pWnd = GetWndPtr(pPyObj);
	if(!pWnd) return NULL;

	for (UINT k=0; k<MAX_CHAN; k++)
	{
		if (ChanTable[k] == NULL)
		{
			ChanTable[k] = (MCI_AVI_STRUCT*) malloc(sizeof(MCI_AVI_STRUCT));
			break;
		}
		if (k == MAX_CHAN-1)
			RETURN_ERR("Unable to activate another channel");

	}


	ChanTable[k]->hWndParent = pWnd->m_hWnd;
	strcpy(ChanTable[k]->szFileName, FileName);
	ChanTable[k]->fReverse=FALSE;
    ChanTable[k]->fNotify=TRUE;
	ChanTable[k]->fStretch = bStretch;
	ChanTable[k]->format = 1;
	ChanTable[k]->scale = scale;
	ChanTable[k]->center = center;
	ChanTable[k]->lAVIduration = 0;

	GUI_BGN_SAVE;
	BOOL bRet = AviOpen(ChanTable[k]);
	GUI_END_SAVE;

	if(!bRet)
		{
		free(ChanTable[k]);
		ChanTable[k] = NULL;
		RETURN_ERR("AviOpen failed");
		}

	ChanTable[k]->playstart = AviClip(ChanTable[k], clipbegin);
	ChanTable[k]->playend = AviClip(ChanTable[k], clipend);

	return Py_BuildValue("i", k);
	}

static PyObject* py_mpeg_play(PyObject *self, PyObject *args)
{
	int k;
	long d;
	if(!PyArg_ParseTuple(args, "il", &k, &d))
		RETURN_ERR("py_mpeg_play");
	if(ChanTable[k] == NULL)
		RETURN_ERR("py_mpeg_play::invalid index");

	ChanTable[k]->lAVIduration = d;
	GUI_BGN_SAVE;
	BOOL bRet = AviPlay(ChanTable[k]);
	GUI_END_SAVE;
	ChanTable[k]->lAVIduration = 0;

	return Py_BuildValue("i", bRet);
}


static PyObject* py_mpeg_playstop(PyObject *self, PyObject *args)
{
	int k;
	if(!PyArg_ParseTuple(args, "i", &k))
		RETURN_ERR("py_mpeg_playstop");
	if(ChanTable[k] == NULL)
		RETURN_ERR("py_mpeg_playstop::invalid index");

	GUI_BGN_SAVE;
	BOOL bRet = AviStop(ChanTable[k]);
	GUI_END_SAVE;
				
	return Py_BuildValue("i", bRet);
}



static PyObject* py_mpeg_finished(PyObject *self, PyObject *args)
{
	int k;
	if(!PyArg_ParseTuple(args, "i", &k))
		RETURN_ERR("mpeg_finished");

	if(ChanTable[k] == NULL)
		RETURN_ERR("py_mpeg_finished::invalid index");

	GUI_BGN_SAVE;
	BOOL bRet = AviClose(ChanTable[k]);
	GUI_END_SAVE;

	free(ChanTable[k]);
	ChanTable[k] = NULL;
	return Py_BuildValue("i", bRet);
}



static PyObject* py_mpeg_GetFrame(PyObject *self, PyObject *args)
{
	int k;
	if(!PyArg_ParseTuple(args, "i", &k))
		RETURN_ERR("py_mpeg_GetFrame");

	if (ChanTable[k] == NULL)
		RETURN_ERR("py_mpeg_GetFrame::invalid index");

	GUI_BGN_SAVE;
	BOOL bRet = AviFrame(ChanTable[k]);	
	GUI_END_SAVE;
	
	return Py_BuildValue("i", bRet);
}


static PyObject* py_mpeg_position(PyObject *self, PyObject *args)
{
	int k;
	if(!PyArg_ParseTuple(args, "i", &k))
		RETURN_ERR("py_mpeg_position");

	if (ChanTable[k] == NULL)
		RETURN_ERR("py_mpeg_position::invalid index");

	// It seems that there is no need to stop and restatr the movie
	// Just place the window
	//BOOL b1 = AviStop(ChanTable[k]);
	positionMovie(ChanTable[k]);
	//BOOL b2 = AviPlay(ChanTable[k]);
	//bRet = b1*b2;
	return Py_BuildValue("l", 1);
}

static PyObject* py_mpeg_duration(PyObject *self, PyObject *args)
{
	int k;
	if(!PyArg_ParseTuple(args, "i", &k))
		RETURN_ERR("py_mpeg_duration");

	if (ChanTable[k] == NULL)
		RETURN_ERR("py_mpeg_duration::invalid index");

	GUI_BGN_SAVE;
	long length = (long) AviDuration(ChanTable[k]);
	GUI_END_SAVE;

	long lRet;	
	if(ChanTable[k]->playend != 0)
		lRet = ChanTable[k]->playend-ChanTable[k]->playstart;
	else if(ChanTable[k]->playstart != 0)
		lRet = length - ChanTable[k]->playstart;
	else lRet = length;

	if(lRet < 0)
		lRet = length;
			
	return Py_BuildValue("l", lRet);
}



static PyObject* py_mpeg_seekstart(PyObject *self, PyObject *args)
{
	int k;
	if(!PyArg_ParseTuple(args, "i", &k))
		RETURN_ERR("py_mpeg_seekstart");
	if (ChanTable[k] == NULL)
		RETURN_ERR("py_mpeg_seekstart::invalid index");

	ChanTable[k]->iSeekThere = ChanTable[k]->playstart;
	GUI_BGN_SAVE;
	BOOL bRet = AviSeek(ChanTable[k]);	
	GUI_END_SAVE;
	
	return Py_BuildValue("i", bRet);
}

static PyObject* py_mpeg_seek(PyObject *self, PyObject *args)
{
	int k, d;
	if(!PyArg_ParseTuple(args, "ii", &k, &d))
		RETURN_ERR("py_mpeg_seek");
	if (ChanTable[k] == NULL)
		RETURN_ERR("py_mpeg_seek::invalid index");

	ChanTable[k]->iSeekThere = d;
	GUI_BGN_SAVE;
	BOOL bRet = AviSeek(ChanTable[k]);
	GUI_END_SAVE;				
	return Py_BuildValue("i", bRet);
}


static PyObject* py_mpeg_Update(PyObject *self, PyObject *args)
{
	int k;
	if(!PyArg_ParseTuple(args, "i", &k))
		RETURN_ERR("py_mpeg_Update");

	if (ChanTable[k] == NULL)
		RETURN_ERR("py_mpeg_Update::invalid index");

	GUI_BGN_SAVE;
	BOOL bRet = (int) AviUpdate(ChanTable[k]);
	GUI_END_SAVE;

	return Py_BuildValue("i", bRet);
}


static PyObject*  py_mpeg_SizeOfImage(PyObject *self, PyObject *args)
{
	PyObject *pPyObj;
	char *FileName;
	if(!PyArg_ParseTuple(args, "Os", &pPyObj, &FileName))
		RETURN_ERR("py_mpeg_SizeOfImage");

	CWnd *pWnd = GetWndPtr(pPyObj);
	if(pWnd==NULL) return NULL;


	MCI_AVI_STRUCT* temp = (MCI_AVI_STRUCT*) malloc(sizeof(MCI_AVI_STRUCT));
	
	temp->hWndParent = pWnd->m_hWnd;
	strcpy(temp->szFileName, FileName);
	temp->fReverse=FALSE;
    temp->fNotify=TRUE;
	temp->fStretch = 0;
	temp->format = 1;
	temp->scale = 0;
	temp->center = 0;
 
	RECT rc={0,0,100,100};
	GUI_BGN_SAVE;
	BOOL bRet = AviOpen(temp);
	if(bRet)
		{
		AviSize(temp, &rc);
		AviClose(temp);
		}
	GUI_END_SAVE;
	free(temp);	

	if (!bRet)
		RETURN_ERR("AviOpen failed");

	return Py_BuildValue("ll", rc.right, rc.bottom);
}



BEGIN_PYMETHODDEF(Mpegex)
	{ "arm", py_mpeg_arm, 1},
	{ "play",py_mpeg_play, 1},
	{ "finished", py_mpeg_finished, 1},
	{ "stop", py_mpeg_playstop, 1},
	{ "position", py_mpeg_position, 1},
	{ "GetFrame", py_mpeg_GetFrame, 1},
	{ "GetDuration",py_mpeg_duration,1},
	{ "seek", py_mpeg_seek, 1},
	{ "seekstart", py_mpeg_seekstart, 1},
	{ "Update", py_mpeg_Update, 1},
	{ "SizeOfImage", py_mpeg_SizeOfImage, 1},
END_PYMETHODDEF();


DEFINE_PYMODULETYPE("PyMpegex",Mpegex);
