// -*- Mode: C++; tab-width: 4 -*-
// $Id$
//
#define VC_EXTRALEAN
#define STRICT

#pragma comment (lib,"winmm.lib")
#pragma comment (lib,"dsound.lib")

#include <afxwin.h>
#include <afxmt.h>	
#include <afxext.h> 
#include <mmsystem.h>
#include "audiostream.h"

//Win32 Header Files
#include <process.h>

//Python Header Files
#include "Python.h"

//PythonWin Header Files
#include "win32ui.h"
#include "win32assoc.h"
#include "win32cmd.h"
#include "win32win.h"

#include "moddef.h"
DECLARE_PYMODULECLASS(Soundex);
IMPLEMENT_PYMODULECLASS(Soundex,GetSoundex,"Soundex Module Wrapper Object");


static AudioStreamServices *mainsound;
static HWND hWnd=NULL;

struct samples{
	HWND hwnd;
	AudioStream* sample;
	BOOL reserved;
};

#define MAX_SOUND_NUMBER	20
static samples sounds[MAX_SOUND_NUMBER];
static BOOL firsttime=TRUE;


int createsound(HWND hwnd,LPSTR filename)
	{
	if(firsttime)
		{
		firsttime = FALSE;
		mainsound = new AudioStreamServices;
		if (mainsound)
			mainsound->Initialize (hwnd);
		hWnd=hwnd;
		for(int i=0;i<MAX_SOUND_NUMBER;i++) 
			{
			sounds[i].sample = new AudioStream;
			sounds[i].hwnd = NULL;
			sounds[i].reserved = FALSE;
			}
		}

	for(int i=0;i<MAX_SOUND_NUMBER;i++)
	{
	 if(sounds[i].reserved==FALSE)
	 {
		if (!sounds[i].sample->Create(filename,mainsound,hwnd))
		{
			i = -1;
			break;
		}
	    sounds[i].hwnd = hwnd;
		sounds[i].reserved = TRUE;
		break;
	 }
	}
	
	return i;
}

 void playsound(int i)
{
    if(sounds[i].reserved)
	{
		sounds[i].sample->Play();
	}
}

void stopsound(int i)
{
    if(sounds[i].reserved)
	{
	 sounds[i].sample->Stop();
	}
}

BOOL closesound()
{
    int i;
	for(i=0;i<MAX_SOUND_NUMBER;i++) sounds[i].sample->Destroy();
	if(mainsound) delete mainsound;
	firsttime=TRUE;
	hWnd=NULL;
	return TRUE;
}

 BOOL closesound(int i)
{
	int k;
	BOOL found = FALSE;
	sounds[i].reserved = FALSE;
	sounds[i].sample->Destroy();
	sounds[i].sample=new AudioStream;

	for(k=0;k<MAX_SOUND_NUMBER;k++) 
	{
		if (sounds[k].reserved == TRUE)
		{
			found = TRUE;
			break;
		}
	}

	if (!found) closesound();
	return found;
}

void 
seekstart(int i)
{
    if(sounds[i].reserved)
	{
		sounds[i].sample->m_fCued = FALSE;	 
		sounds[i].sample->Cue();
	}
}




//***************************
//Things to do:
//	- built a LinkList with the used windows so as to preserve MemoryManagement
//	- use in a more clever way to cover every case
//***************************

static PyObject* py_create_sound(PyObject *self, PyObject *args)
	{
	PyObject *pPyObj;
	char *filename;
	if(!PyArg_ParseTuple(args, "Os", &pPyObj, &filename))
		return NULL;
	
	CWnd *pWnd = GetWndPtr(pPyObj);
	if(!pWnd) return NULL;

	GUI_BGN_SAVE;
	int ix = createsound(pWnd->m_hWnd,filename);
	GUI_END_SAVE;
	
	return Py_BuildValue("i",ix);
	}

static PyObject* py_play_sound(PyObject *self, PyObject *args)
	{
	int ix;
	if(!PyArg_ParseTuple(args, "i", &ix))
		return NULL;

	GUI_BGN_SAVE;
	SetFocus(hWnd);
	playsound(ix);
	GUI_END_SAVE;
	
	return Py_BuildValue("i",1);
	}


static PyObject* py_pause_sound(PyObject *self, PyObject *args)
	{
	int ix;
	if(!PyArg_ParseTuple(args, "i", &ix))
		return NULL;
	GUI_BGN_SAVE;
	stopsound(ix);
	GUI_END_SAVE;
	RETURN_NONE;
	}


static PyObject* py_close_sound(PyObject *self, PyObject *args)
	{
	int ix;
	if(!PyArg_ParseTuple(args, "i", &ix))
		return NULL;
	GUI_BGN_SAVE;
	BOOL res = closesound(ix);
	GUI_END_SAVE;
	return Py_BuildValue("i",res);
	}


static PyObject* py_close_all(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	GUI_BGN_SAVE;
	closesound();
	GUI_END_SAVE;
	RETURN_NONE;
	}


static PyObject* py_seek_start(PyObject *self, PyObject *args)
	{
	int ix;	
	if(!PyArg_ParseTuple(args, "i", &ix))
		return NULL;
	GUI_BGN_SAVE;
	seekstart(ix);
	GUI_END_SAVE;
	RETURN_NONE;
	}


BEGIN_PYMETHODDEF(Soundex)
	{ "Play", py_play_sound, 1},
    { "Create", py_create_sound, 1},
	{ "Pause", py_pause_sound, 1},
	{ "Close", py_close_sound, 1},
	{ "CloseAll", py_close_all, 1},
	{ "SeekStart", py_seek_start, 1},
END_PYMETHODDEF()


DEFINE_PYMODULETYPE("PySoundex",Soundex);
