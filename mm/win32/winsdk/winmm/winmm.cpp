
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include <windows.h>
#include <mmsystem.h>

#include "Python.h"

#include "utils.h"

#include "winmm_waveout.h"
#include "winmm_wavehdr.h"
#include "winmm_video.h"

#ifdef LINK_MP3LIB
#include "winmm_mp3dec.h"
#endif

PyObject *WinMM_ErrorObject;

static PyObject* WaveOutGetNumDevs(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	UINT n = waveOutGetNumDevs();
	return Py_BuildValue("i", n);
}

static PyObject* WaveOutGetDevCaps(PyObject *self, PyObject *args)
{
	UINT device_index;
	if (!PyArg_ParseTuple(args, "i", &device_index))
		return NULL;
	WAVEOUTCAPS woc;
	MMRESULT mmres  = waveOutGetDevCaps(device_index, &woc, sizeof(WAVEOUTCAPS));
	if(mmres != MMSYSERR_NOERROR)
		{
		seterror("waveOutGetDevCaps", mmres);
		return NULL;
		}
	return Py_BuildValue("(slil)", TextPtr(woc.szPname).c_str(), woc.dwFormats, int(woc.wChannels), woc.dwSupport); 
}


static PyObject* SndPlaySound(PyObject *self, PyObject *args)
{
	char *pszSoundName;
	UINT flags = SND_ASYNC;
	if (!PyArg_ParseTuple(args, "s|i", &pszSoundName, flags))
		return NULL;
	BOOL res = sndPlaySound(TextPtr(pszSoundName), flags);
	if(!res)
		{
		seterror("sndPlaySound() failed");
		return NULL;
		}
	return none(); 
}

static PyObject* SndStopSound(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	BOOL res = sndPlaySound(NULL, SND_ASYNC);
	if(!res)
		{
		seterror("sndPlaySound() failed");
		return NULL;
		}
	return none(); 
}


static struct PyMethodDef winmm_methods[] = {
	{"WaveOutGetNumDevs", (PyCFunction)WaveOutGetNumDevs, METH_VARARGS, ""},
	{"WaveOutGetDevCaps", (PyCFunction)WaveOutGetDevCaps, METH_VARARGS, ""},
	{"WaveOutQuery", (PyCFunction)Winmm_WaveOutQuery, METH_VARARGS, ""},
#ifdef LINK_MP3LIB
	{"CreateMp3Decoder", (PyCFunction)Winmm_CreateMp3Decoder, METH_VARARGS, ""},
#endif
	{"CreateWaveHdr", (PyCFunction)Winmm_CreateWaveHdr, METH_VARARGS, ""},
	{"WaveOutOpen", (PyCFunction)Winmm_WaveOutOpen, METH_VARARGS, ""},
	{"WaveOutFromHandle", (PyCFunction)Winmm_WaveOutFromHandle, METH_VARARGS, ""},
	{"SndPlaySound", (PyCFunction)SndPlaySound, METH_VARARGS, ""},
	{"SndStopSound", (PyCFunction)SndStopSound, METH_VARARGS, ""},

	{"CreateVideoPlayerFromFile", (PyCFunction)Winmm_CreateVideoPlayerFromFile, METH_VARARGS, ""},
	{"GetVideoDuration", (PyCFunction)Winmm_GetVideoDuration, METH_VARARGS, ""},
	{"GXOpenDisplay", (PyCFunction)Winmm_GXOpenDisplay, METH_VARARGS, ""},
	{"GXCloseDisplay", (PyCFunction)Winmm_GXCloseDisplay, METH_VARARGS, ""},
	{NULL, (PyCFunction)NULL, 0, NULL}		// sentinel
};

/////////////////////////////////////

struct enumentry {char* s;int n;};

static struct enumentry wave_formats[] ={
    {"WAVE_FORMAT_1M08", WAVE_FORMAT_1M08}, // 11.025 kHz, mono, 8-bit
    {"WAVE_FORMAT_1M16", WAVE_FORMAT_1M16}, // 11.025 kHz, mono, 16-bit
    {"WAVE_FORMAT_1S08", WAVE_FORMAT_1S08}, // 11.025 kHz, stereo, 8-bit
    {"WAVE_FORMAT_1S16", WAVE_FORMAT_1S16}, // 11.025 kHz, stereo, 16-bit
    {"WAVE_FORMAT_2M08", WAVE_FORMAT_2M08}, // 22.05 kHz, mono, 8-bit 
    {"WAVE_FORMAT_2M16", WAVE_FORMAT_2M16}, // 22.05 kHz, mono, 16-bit
    {"WAVE_FORMAT_2S08", WAVE_FORMAT_2S08}, // 22.05 kHz, stereo, 8-bit
    {"WAVE_FORMAT_2S16", WAVE_FORMAT_2S16}, // 22.05 kHz, stereo, 16-bit
    {"WAVE_FORMAT_4M08", WAVE_FORMAT_4M08}, // 44.1 kHz, mono, 8-bit
    {"WAVE_FORMAT_4M16", WAVE_FORMAT_4M16}, // 44.1 kHz, mono, 16-bit
    {"WAVE_FORMAT_4S08", WAVE_FORMAT_4S08}, // 44.1 kHz, stereo, 8-bit
    {"WAVE_FORMAT_4S16", WAVE_FORMAT_4S16}, // 44.1 kHz, stereo, 16-bit
	{NULL,0}
	};

// add symbolic constants of enum
static int 
SetItemEnum(PyObject *d,enumentry e[])
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

#define FATAL_ERROR_IF(exp) if(exp){Py_FatalError("can't initialize winmm module");return;}	

static char winmm_module_documentation[] =
"Windows multimedia module"
;

extern "C" __declspec(dllexport)
void initwinmm()
{
	PyObject *m, *d;
	bool bPyErrOccurred = false;
	
	// Create the module and add the functions
	m = Py_InitModule4("winmm", winmm_methods,
		winmm_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	// add 'error'
	d = PyModule_GetDict(m);
	WinMM_ErrorObject = PyString_FromString("winmm.error");
	PyDict_SetItemString(d, "error", WinMM_ErrorObject);

	// add symbolic constants of enum
	FATAL_ERROR_IF(SetItemEnum(d, wave_formats)<0)

	// Check for errors
	if (PyErr_Occurred())
		Py_FatalError("can't initialize winmm module");
}
