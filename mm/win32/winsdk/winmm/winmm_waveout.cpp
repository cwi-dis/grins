
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include <windows.h>
#include <mmsystem.h>

#include "winmm_waveout.h"

#include "utils.h"

#include "winmm_waveout_impl.h"
#include "winmm_wavehdr_impl.h"

PyObject* Winmm_WaveOutQuery(PyObject *self, PyObject *args)
{
	int nChannels, nBlockAlign, wBitsPerSample;
	long nSamplesPerSec, nAvgBytesPerSec;
	if(!PyArg_ParseTuple(args, "(illii)", 
		&nChannels, &nSamplesPerSec, &nAvgBytesPerSec, &nBlockAlign, &wBitsPerSample))
		return NULL;
	WAVEFORMATEX wf = {WAVE_FORMAT_PCM, 
		WORD(nChannels), 
		DWORD(nSamplesPerSec), 
		DWORD(nAvgBytesPerSec),
		WORD(nBlockAlign),
		WORD(wBitsPerSample),
		WORD(0) 
		};
	DWORD flags = WAVE_FORMAT_QUERY;
	MMRESULT mmres = waveOutOpen(NULL, WAVE_MAPPER, &wf, 0, 0, flags);
	if(mmres != MMSYSERR_NOERROR)
		return Py_BuildValue("i", 0);
	return Py_BuildValue("i", 1);
}

PyObject* Winmm_WaveOutOpen(PyObject *self, PyObject *args)
{
	int nChannels, nBlockAlign, wBitsPerSample;
	long nSamplesPerSec, nAvgBytesPerSec;
	PyObject *cbobj;
	DWORD flags = CALLBACK_WINDOW; // CALLBACK_WINDOW, CALLBACK_FUNCTION
	if(!PyArg_ParseTuple(args, "(illii)O|l", 
		&nChannels, &nSamplesPerSec, &nAvgBytesPerSec, &nBlockAlign, &wBitsPerSample,
		&cbobj, &flags))
		return NULL;
	if( (flags & WAVE_FORMAT_QUERY) ==  WAVE_FORMAT_QUERY)
		{
		seterror("Invalid flag (WAVE_FORMAT_QUERY)");
		return NULL;
		}
	WAVEFORMATEX wf = {WAVE_FORMAT_PCM, 
		WORD(nChannels), 
		DWORD(nSamplesPerSec), 
		DWORD(nAvgBytesPerSec),
		WORD(nBlockAlign),
		WORD(wBitsPerSample),
		WORD(0) 
		};
	HWAVEOUT hWaveOut = NULL;
	HWND hwnd = (HWND)GetObjHandle(cbobj);
	MMRESULT mmres = waveOutOpen(&hWaveOut, WAVE_MAPPER, &wf, (DWORD)hwnd, 0, flags);
	if(mmres != MMSYSERR_NOERROR)
		{
		if(mmres == MMSYSERR_INVALHANDLE)
			seterror("waveOutOpen", "MMSYSERR_INVALHANDLE, Specified device handle is invalid.");
		else if(mmres == MMSYSERR_BADDEVICEID)
			seterror("waveOutOpen", "MMSYSERR_BADDEVICEID, Specified device identifier is out of range.");
		else if(mmres == MMSYSERR_NODRIVER)
			seterror("waveOutOpen", "MMSYSERR_NODRIVER, No device driver is present");
		else if(mmres == MMSYSERR_NOMEM)
			seterror("waveOutOpen", "MMSYSERR_NOMEM, Unable to allocate or lock memory.");
		else if(mmres == WAVERR_BADFORMAT)
			seterror("waveOutOpen", "WAVERR_BADFORMAT, Attempted to open with an unsupported waveform-audio format.");
		else if(mmres == WAVERR_SYNC)
			seterror("waveOutOpen", "WAVERR_SYNC, Device is synchronous but waveOutOpen was called without using the WAVE_ALLOWSYNC flag");
		else
			seterror("waveOutOpen", mmres);
		return NULL;
		}
	return (PyObject*)PyWaveOut::createInstance(hWaveOut); 
}

///////////////////////////////////////////
// module

static PyObject* PyWaveOut_Close(PyWaveOut *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	MMRESULT mmres = waveOutClose(self->m_hWaveOut);
	if(mmres != MMSYSERR_NOERROR)
		{
		seterror("waveOutClose", mmres);
		return NULL;
		}
	self->m_hWaveOut = NULL;
	return none(); 
}

static PyObject* PyWaveOut_Reset(PyWaveOut *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	MMRESULT mmres = waveOutReset(self->m_hWaveOut);
	if(mmres != MMSYSERR_NOERROR)
		{
		seterror("waveOutReset", mmres);
		return NULL;
		}
	return none(); 
}

static PyObject* PyWaveOut_Write(PyWaveOut *self, PyObject *args)
{
	PyWaveHdr *obj;
	if (!PyArg_ParseTuple(args,"O!", &PyWaveHdr::type, &obj))
		return NULL;
	MMRESULT mmres = waveOutWrite(self->m_hWaveOut, obj->m_pWaveHdr, sizeof(WAVEHDR));
 	if(mmres != MMSYSERR_NOERROR)
		{
		seterror("waveOutWrite", mmres);
		return NULL;
		}
	return none();
}

static PyObject* PyWaveOut_Pause(PyWaveOut *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	MMRESULT mmres = waveOutPause(self->m_hWaveOut);
	if(mmres != MMSYSERR_NOERROR)
		{
		seterror("waveOutPause", mmres);
		return NULL;
		}
	return none(); 
}

static PyObject* PyWaveOut_Restart(PyWaveOut *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	MMRESULT mmres = waveOutRestart(self->m_hWaveOut);
	if(mmres != MMSYSERR_NOERROR)
		{
		seterror("waveOutRestart", mmres);
		return NULL;
		}
	return none(); 
}

PyMethodDef PyWaveOut::methods[] = {
	{"Close", (PyCFunction)PyWaveOut_Close, METH_VARARGS, ""},
	{"Reset", (PyCFunction)PyWaveOut_Reset, METH_VARARGS, ""},
	{"Write", (PyCFunction)PyWaveOut_Write, METH_VARARGS, ""},
	{"Pause", (PyCFunction)PyWaveOut_Pause, METH_VARARGS, ""},
	{"Restart", (PyCFunction)PyWaveOut_Restart, METH_VARARGS, ""},
	{NULL, (PyCFunction)NULL, 0, NULL}		// sentinel
};

PyTypeObject PyWaveOut::type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,					// ob_size
	"PyWaveOut",			// tp_name
	sizeof(PyWaveOut),		// tp_basicsize
	0,					// tp_itemsize
	
	// methods
	(destructor)PyWaveOut::dealloc,	// tp_dealloc
	(printfunc)0,				// tp_print
	(getattrfunc)PyWaveOut::getattr,// tp_getattr
	(setattrfunc)0,	// tp_setattr
	(cmpfunc)0,		// tp_compare
	(reprfunc)0,	// tp_repr
	0,				// tp_as_number
	0,				// tp_as_sequence
	0,				// tp_as_mapping
	(hashfunc)0,	// tp_hash
	(ternaryfunc)0,	// tp_call
	(reprfunc)0,	// tp_str

	// Space for future expansion
	0L,0L,0L,0L,

	"PyWaveOut Type" // Documentation string
	};
