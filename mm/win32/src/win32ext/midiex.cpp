#include "stdafx.h"

#include "mcidll.h"
#include "win32win.h"

#include "moddef.h"
DECLARE_PYMODULECLASS(Midiex);
IMPLEMENT_PYMODULECLASS(Midiex,GetMidiex,"Midiex Module Wrapper Object");


#define MAX_CHAN  10
static MCI_MIDI_STRUCT  *ChanTable[MAX_CHAN];
static BOOL   Busy[MAX_CHAN];


static BOOL first=TRUE;

static void init()
{
	for (UINT k=0; k<MAX_CHAN; k++)
		ChanTable[k] = NULL;

	for (UINT j=0; j<MAX_CHAN; j++)
		Busy[j] = FALSE;

	first = FALSE;

}

static PyObject*  py_midi_prepare(PyObject *self,PyObject *args)
{
	if (first) init();

	PyObject *Ob = Py_None;
	char *FileName;
	if(!PyArg_ParseTuple(args, "Os", &Ob, &FileName))
		RETURN_ERR("py_midi_prepare");

	CWnd *pWnd = GetWndPtr(Ob);
	if(!pWnd) return NULL;

	for (int k=0; k<MAX_CHAN; k++)
	{
		if (ChanTable[k] == NULL)
		{
			ChanTable[k] = (MCI_MIDI_STRUCT*) malloc(sizeof(MCI_MIDI_STRUCT));
			break;
		}
		if (k == MAX_CHAN-1)
			RETURN_ERR("Unable to activate another channel");

	}


	ChanTable[k]->hWndParent = pWnd->m_hWnd;
	strcpy(ChanTable[k]->szFileName, FileName);
	ChanTable[k]->fNotify=TRUE;
	
	/*
 	GUI_BGN_SAVE;
	BOOL bRet = MidiOpen(ChanTable[k]);
	GUI_END_SAVE;

		
	if (! bRet)
	{
		free(ChanTable[k]);
		ChanTable[k] = NULL;
		Busy[k] = FALSE;
		return NULL;
	}*/

		
	
	return Py_BuildValue("i", k);
}

static PyObject* py_midi_play(PyObject *self, PyObject *args)
{
	int k;
	long d;
	if(!PyArg_ParseTuple(args, "il", &k, &d))
		RETURN_ERR("py_midi_play");


	if(ChanTable[k] == NULL)
		RETURN_ERR("py_midi_play::invalid index");

 	GUI_BGN_SAVE;
	// stop any other channel that is currently playing
	for (int j=0; j<MAX_CHAN; j++)
	{
		int temp = k - j;
		if ((temp != 0)) 
		{
			if (Busy[j] == TRUE) 
			{
				Busy[j]= FALSE;
				MidiStop(ChanTable[j]);
				SendMessage(ChanTable[j]->hWndParent, MM_MCINOTIFY,1,0);
			}
		}
	}

	BOOL bRet = MidiOpen(ChanTable[k]);
	ChanTable[k]->lMIDIduration = d;
	if (!bRet)
		{
		free(ChanTable[k]);
		ChanTable[k] = NULL;
		Busy[k] = FALSE;
		}
	else
		{
		bRet=MidiPlay(ChanTable[k]);
		Busy[k] = TRUE;
		}
 	GUI_END_SAVE;

	return Py_BuildValue("i", bRet);
}

static PyObject* py_midi_playstop(PyObject *self, PyObject *args)
{
	int k;
	if(!PyArg_ParseTuple(args, "i", &k))
		RETURN_ERR("py_midi_playstop");
	if(ChanTable[k] == NULL)
		RETURN_ERR("py_midi_playstop::invalid index");

 	GUI_BGN_SAVE;
	BOOL bRet = MidiStop(ChanTable[k]);				
 	GUI_END_SAVE;

	return Py_BuildValue("i", bRet);
}



static PyObject* py_midi_finished(PyObject *self, PyObject *args)
{
	int k;
	if(!PyArg_ParseTuple(args, "i", &k))
		RETURN_ERR("py_midi_finished");
	if(ChanTable[k] == NULL)
		RETURN_ERR("py_midi_finished::invalid index");

 	GUI_BGN_SAVE;
	BOOL bRet = MidiClose(ChanTable[k]);	
 	GUI_END_SAVE;
	Busy[k] = FALSE;
	free(ChanTable[k]);
	ChanTable[k] = NULL;

	return Py_BuildValue("i", bRet);
}

static PyObject* py_midi_seekstart(PyObject *self, PyObject *args)
{
	int k;
	if(!PyArg_ParseTuple(args, "i", &k))
			RETURN_ERR("py_midi_seekstart");
	if(ChanTable[k] == NULL)
		RETURN_ERR("py_midi_seekstart::invalid index");

	ChanTable[k]->iSeekThere = 0;
 	GUI_BGN_SAVE;
	BOOL bRet = MidiSeek(ChanTable[k]);		
 	GUI_END_SAVE;
	return Py_BuildValue("i", bRet);
}

static PyObject* py_midi_seek(PyObject *self, PyObject *args)
{
	int k,d;
	if(!PyArg_ParseTuple(args, "ii", &k, &d))
		RETURN_ERR("py_midi_seek");
	if(ChanTable[k] == NULL)
		RETURN_ERR("py_midi_seek::invalid index");

	ChanTable[k]->iSeekThere = d;
 	GUI_BGN_SAVE;
	BOOL bRet = MidiSeek(ChanTable[k]);	
 	GUI_END_SAVE;
	
	return Py_BuildValue("i", bRet);
}

BEGIN_PYMETHODDEF(Midiex)
	{ "prepare", py_midi_prepare, 1},
	{ "play",py_midi_play, 1},
	{ "finished", py_midi_finished, 1},
	{ "stop", py_midi_playstop, 1},
	{ "seekstart", py_midi_seekstart, 1},
	{ "seek", py_midi_seek, 1},
END_PYMETHODDEF()


DEFINE_PYMODULETYPE("PyMidiex",Midiex);

