
#include "midiex.h"



#define MAX_CHAN  10


MCI_MIDI_STRUCT  *ChanTable[MAX_CHAN];
BOOL   Busy[MAX_CHAN];


static PyObject *midiExError;

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

	for (UINT j=0; j<MAX_CHAN; j++)
		Busy[j] = FALSE;

	first = FALSE;

}

static PyObject*  py_midi_prepare(PyObject *self,PyObject *args)
{
	TRACE("Entering midi_arm\n");
	if (first)
		init();

	UINT k;
	CWnd *Wnd; 
	BOOL  bRet;
	PyObject *Ob = Py_None;
	char *FileName;
	

	if(!PyArg_ParseTuple(args, "Os", &Ob, &FileName))
	{
		Py_INCREF(Py_None);
		//AfxMessageBox("Error", MB_OK);
		return Py_None;return NULL;
	
	}

	Wnd = GetWndPtr(Ob);
	TRACE("Retrieved: Handle %X filename %s", Wnd->m_hWnd, FileName);

	for (k=0; k<MAX_CHAN; k++)
	{
		if (ChanTable[k] == NULL)
		{
			ChanTable[k] = (MCI_MIDI_STRUCT*) malloc(sizeof(MCI_MIDI_STRUCT));
			TRACE("New struct allocated, index %d\n", k);
			break;
		}
		if (k == MAX_CHAN-1)
			AfxMessageBox("Unable to activate another channel", MB_OK);

	}


	ChanTable[k]->hWndParent = Wnd->m_hWnd;
	strcpy(ChanTable[k]->szFileName, FileName);
	TRACE("Filename in struct is: %s\n", ChanTable[k]->szFileName);
	ChanTable[k]->fNotify=TRUE;
	
 
	bRet = MidiOpen(ChanTable[k]);

		
	if (! bRet)
	{
		free(ChanTable[k]);
		ChanTable[k] = NULL;
		Busy[k] = FALSE;
	}

		
	if (!bRet)
	return Py_BuildValue("i", -1);
	
	return Py_BuildValue("i", k);
}

static PyObject* py_midi_play(PyObject *self, PyObject *args)
{
	TRACE("Entering midi_play\n");

	BOOL bRet;
	int k;
	PyObject *Ob = Py_None;
		
	if(!PyArg_ParseTuple(args, "i", &k))
	{
		Py_INCREF(Py_None);
		//AfxMessageBox("Error", MB_OK);
		return Py_None;return NULL;
	
	}
	

	// stop any other channel that is currently playing
	for (int j=0; j<MAX_CHAN; j++)
	{
		int temp = k - j;
		TRACE("Temp is %d\n", temp);

		if ((temp != 0)) 
		{
			if (Busy[j] == TRUE) 
			{
				Busy[j]= FALSE;
				MidiStop(ChanTable[j]);
				//MidiClose(ChanTable[j]);
				//free(ChanTable[j]);
				//TRACE("Index %d no longer exists \n", j);
				//ChanTable[j] = NULL;
				break;					//only one is busy, once found we 're ok
			}
		}
	}

	if (ChanTable[k] != NULL)
	{
		bRet = MidiPlay(ChanTable[k]);
		Busy[k] = TRUE;
	}

	
	
	TRACE("Playing struct with index %d\n", k);
	
	return Py_BuildValue("i", bRet);
}

static PyObject* py_midi_playstop(PyObject *self, PyObject *args)
{
	TRACE("Entering midi_playstop\n");

	BOOL bRet;
	int k;
	PyObject *Ob = Py_None;
	
	if(!PyArg_ParseTuple(args, "i", &k))
	{
		Py_INCREF(Py_None);
		//AfxMessageBox("Error", MB_OK);
		return Py_None;return NULL;
	
	}

	if (ChanTable[k] != NULL)
	bRet = MidiStop(ChanTable[k]);				
	TRACE("Stopping struct indexed %d\n", k);

	return Py_BuildValue("i", bRet);
}



static PyObject* py_midi_finished(PyObject *self, PyObject *args)
{
	TRACE("Entering midi_finished\n");

	BOOL bRet;
	int k;
	PyObject *Ob = Py_None;

	
	if(!PyArg_ParseTuple(args, "i", &k))
	{
		Py_INCREF(Py_None);
		//AfxMessageBox("Error", MB_OK);
		return Py_None;return NULL;
	
	}

	if (ChanTable[k] != NULL)
	{
		bRet = MidiClose(ChanTable[k]);
		Busy[k] = FALSE;
	}
	

				
	TRACE("About to free struct indexed %d\n", k);
	free(ChanTable[k]);
	ChanTable[k] = NULL;

	
	return Py_BuildValue("i", bRet);
}


static PyMethodDef midiExMethods[] = 
{
	{ "prepare", (PyCFunction)py_midi_prepare, 1},
	{ "play",(PyCFunction)py_midi_play, 1},
	{ "finished", (PyCFunction)py_midi_finished, 1},
	{ "stop", (PyCFunction)py_midi_playstop, 1},
	{ NULL, NULL }
};


PyEXPORT 
void initmidiex()
{
	PyObject *m, *d;
	first = TRUE;
	m = Py_InitModule("midiex", midiExMethods);
	d = PyModule_GetDict(m);
	midiExError = PyString_FromString("midiex.error");
	PyDict_SetItemString(d, "error", midiExError);
}

#ifdef __cplusplus
}
#endif


