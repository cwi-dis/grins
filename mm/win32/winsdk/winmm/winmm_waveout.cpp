#include <windows.h>
#include <mmsystem.h>

#include "winmm_waveout.h"

#include "utils.h"

struct PyWaveOut
	{
	PyObject_HEAD
	HWAVEOUT m_hWaveOut;
	WAVEHDR *m_pWaveHdr;

	static PyTypeObject type;
	static PyMethodDef methods[];

	static PyWaveOut *createInstance(HWAVEOUT hWaveOut = NULL)
		{
		PyWaveOut *instance = PyObject_NEW(PyWaveOut, &type);
		if (instance == NULL) return NULL;
		instance->m_hWaveOut = hWaveOut;
		instance->m_pWaveHdr = new WAVEHDR;
		memset(instance->m_pWaveHdr, 0, sizeof(WAVEHDR));
		return instance;
		}

	static void dealloc(PyWaveOut *instance) 
		{ 
		if(instance->m_hWaveOut != NULL) 
			waveOutClose(instance->m_hWaveOut);
		if(instance->m_pWaveHdr != NULL)
			delete instance->m_pWaveHdr;
		PyMem_DEL(instance);
		}

	static PyObject *getattr(PyWaveOut *instance, char *name)
		{ 
		return Py_FindMethod(methods, (PyObject*)instance, name);
		}
	};

PyObject* Winmm_WaveOutOpen(PyObject *self, PyObject *args)
{
	int nChannels, nBlockAlign, wBitsPerSample, cbSize;
	long nSamplesPerSec, nAvgBytesPerSec;
	HWND hwnd;
	DWORD flags = WAVE_FORMAT_QUERY; // CALLBACK_WINDOW, CALLBACK_FUNCTION
	if(!PyArg_ParseTuple(args, "(illiii)il", 
		&nChannels, &nSamplesPerSec, &nAvgBytesPerSec, &nBlockAlign, &wBitsPerSample, &cbSize,
		&hwnd, &flags))
		return NULL;
	WAVEFORMATEX wf = {WAVE_FORMAT_PCM, 
		WORD(nChannels), 
		DWORD(nSamplesPerSec), 
		DWORD(nAvgBytesPerSec),
		WORD(nBlockAlign),
		WORD(wBitsPerSample),
		WORD(cbSize) 
		};
	HWAVEOUT hWaveOut;
	MMRESULT mmres = waveOutOpen(&hWaveOut, WAVE_MAPPER, &wf, (DWORD)hwnd, 0, flags);
	if(mmres != MMSYSERR_NOERROR)
		{
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

static PyObject* PyWaveOut_PlayChunk(PyWaveOut *self, PyObject *args)
{
	PyObject *obj;
	if (!PyArg_ParseTuple(args,"S",&obj))
		return NULL;
	if(self->m_pWaveHdr == NULL)
		{
		self->m_pWaveHdr = new WAVEHDR;
		memset(self->m_pWaveHdr, 0, sizeof(WAVEHDR));
		}
	WAVEHDR *pWaveHdr = self->m_pWaveHdr;
	pWaveHdr->lpData = PyString_AS_STRING(obj);
	pWaveHdr->dwBufferLength = PyString_GET_SIZE(obj);
	pWaveHdr->dwFlags = 0;
	pWaveHdr->dwLoops = 0;

	MMRESULT mmres = waveOutPrepareHeader(self->m_hWaveOut, pWaveHdr, sizeof(WAVEHDR));
	if(mmres != MMSYSERR_NOERROR)
		{
		seterror("waveOutPrepareHeader", mmres);
		return NULL;
		}
	mmres = waveOutWrite(self->m_hWaveOut, pWaveHdr, sizeof(WAVEHDR));
 	if(mmres != MMSYSERR_NOERROR)
		{
		waveOutUnprepareHeader(self->m_hWaveOut, pWaveHdr, sizeof(WAVEHDR));
		delete pWaveHdr;
		self->m_pWaveHdr = NULL;
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
	{"PlayChunk", (PyCFunction)PyWaveOut_PlayChunk, METH_VARARGS, ""},
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
