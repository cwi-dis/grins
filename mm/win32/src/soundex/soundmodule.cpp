// -*- Mode: C++; tab-width: 4 -*-
// $Id$
//
//#include "cmifex.h"
//#include "sampledll.h"

#define VC_EXTRALEAN
#define STRICT

#include <afxwin.h>
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

#define _SNDDLL_
#include "sampledll.h"

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
//static AudioStream *sample;




 void initmainsound()
{
	if (hWnd==NULL)
	{
		char cmifClass[200];
		strcpy(cmifClass, AfxRegisterWndClass( CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS));
		
		if((hWnd=CreateWindowEx(WS_EX_CLIENTEDGE,cmifClass,NULL,
						WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN,
						0, 0, 100, 100,
						NULL,
						NULL,NULL,NULL))==NULL)
		{
			return;
		}
	}
	 
		
	 
	 
	// hWnd = GetActiveWindow();//new CWnd;
	//hWnd->Create( NULL, " ");
	
	mainsound = new AudioStreamServices;
    if (mainsound)
    {
        mainsound->Initialize (hWnd);
    }
   
	createsound();
}


 void createsound()
{
	int i;
	for(i=0;i<MAX_SOUND_NUMBER;i++) 
	{
		sounds[i].sample = new AudioStream;
		sounds[i].hwnd = NULL;
		sounds[i].reserved = FALSE;
	}
}


 int createsound(HWND hwnd,LPSTR filename)
{
	int i;

	if(firsttime)
	{
		firsttime = FALSE;
		initmainsound();
		if (hWnd==NULL)
			return -1;
	}

	for(i=0;i<MAX_SOUND_NUMBER;i++)
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
		//PostMessage(sounds[i].hwnd, MM_MCINOTIFY, 2, 1);
		sounds[i].sample->Play();
	}
}

 void stopsound(int i)
{
    if(sounds[i].reserved)
	{
	 sounds[i].sample->Stop();
	 //PostMessage(sounds[i].hwnd, MM_MCINOTIFY, 1, 1); for pause
	}
}

 BOOL closesound()
{
    int i;
	for(i=0;i<MAX_SOUND_NUMBER;i++) sounds[i].sample->Destroy();
	if(mainsound) delete mainsound;
	firsttime=TRUE;
	//ASSERT(0);
	if (hWnd) DestroyWindow(hWnd);
	//delete hWnd;
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


static PyObject *CmifExError;

PYW_EXPORT CWnd *GetWndPtr(PyObject *);

#ifdef __cplusplus
extern "C" {
#endif
//***************************
//Things to do:
//	- built a LinkList with the used windows so as to preserve MemoryManagement
//	- use in a more clever way to cover every case
//***************************


static PyObject* py_example_PlaySound(PyObject *self, PyObject *args)
{
	int bit;
	PyObject *testOb = Py_None;

	//ASSERT(0);
	
	if(!PyArg_ParseTuple(args, "i", &bit))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}
	
	SetFocus(hWnd);
	playsound(bit);
	
	Py_INCREF(Py_None);
	return Py_None;

}




static PyObject* py_example_CreateSound(PyObject *self, PyObject *args)
{
	char *filename;
	//HWND hW;
	CWnd *obWnd;
	int bit;
	PyObject *testOb = Py_None;

	//ASSERT(0);

	if(!PyArg_ParseTuple(args, "Os", &testOb, &filename))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}
	
	obWnd = GetWndPtr(testOb);

	bit = createsound(obWnd->m_hWnd,filename);
	
	return Py_BuildValue("i",bit);
}



static PyObject* py_example_PauseSound(PyObject *self, PyObject *args)
{
	int bit;

	
	if(!PyArg_ParseTuple(args, "i", &bit))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}
	
	stopsound(bit);

	Py_INCREF(Py_None);
	return Py_None;
}


static PyObject* py_example_CloseSound(PyObject *self, PyObject *args)
{
	int bit;
	BOOL res = FALSE;
		
	if(!PyArg_ParseTuple(args, "i", &bit))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}
	
	res = closesound(bit);

	return Py_BuildValue("i",res);
}


static PyObject* py_example_CloseAll(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ""))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}
	
	closesound();
	
	Py_INCREF(Py_None);
	return Py_None;
}


static PyObject* py_example_SeekStart(PyObject *self, PyObject *args)
{
	int bit;
	
	if(!PyArg_ParseTuple(args, "i", &bit))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}
	
	seekstart(bit);

	Py_INCREF(Py_None);
	return Py_None;
}





static PyMethodDef CmifExMethods[] = 
{
	{ "Play", (PyCFunction)py_example_PlaySound, 1},
    { "Create", (PyCFunction)py_example_CreateSound, 1},
	{ "Pause", (PyCFunction)py_example_PauseSound, 1},
	{ "Close", (PyCFunction)py_example_CloseSound, 1},
	{ "CloseAll", (PyCFunction)py_example_CloseAll, 1},
	{ "SeekStart", (PyCFunction)py_example_SeekStart, 1},
	{ NULL, NULL }
};

__declspec(dllexport) 
void initdsoundex()
{
	PyObject *m, *d;
	m = Py_InitModule("dsoundex", CmifExMethods);
	d = PyModule_GetDict(m);
	CmifExError = PyString_FromString("dsoundex.error");
	PyDict_SetItemString(d, "error", CmifExError);
}

#ifdef __cplusplus
}
#endif
