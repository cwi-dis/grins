
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include <windows.h>
#include <mmsystem.h>

#include "winmm_wavehdr.h"

#include "utils.h"

#include "winmm_wavehdr_impl.h"
#include "winmm_waveout_impl.h"


PyObject* Winmm_CreateWaveHdr(PyObject *self, PyObject *args)
	{
	PyObject *strObj;
	if (!PyArg_ParseTuple(args,"S", &strObj))
		return NULL;
	return (PyObject*)PyWaveHdr::createInstance(strObj);
	}

///////////////////////////////////////////
// module

static PyObject* PyWaveHdr_PrepareHeader(PyWaveHdr *self, PyObject *args)
{
	PyWaveOut *wavOutObj;
	if (!PyArg_ParseTuple(args, "O!", &PyWaveOut::type, &wavOutObj))
		return NULL;
	MMRESULT mmres = waveOutPrepareHeader(wavOutObj->m_hWaveOut, self->m_pWaveHdr, sizeof(WAVEHDR));
	if(mmres != MMSYSERR_NOERROR)
		{
		seterror("waveOutPrepareHeader", mmres);
		return NULL;
		}
	return none(); 
}

static PyObject* PyWaveHdr_UnprepareHeader(PyWaveHdr *self, PyObject *args)
{
	PyWaveOut *wavOutObj;
	if (!PyArg_ParseTuple(args, "O", &PyWaveOut::type, &wavOutObj))
		return NULL;
	waveOutUnprepareHeader(wavOutObj->m_hWaveOut, self->m_pWaveHdr, sizeof(WAVEHDR));
	return none(); 
}


PyMethodDef PyWaveHdr::methods[] = {
	{"PrepareHeader", (PyCFunction)PyWaveHdr_PrepareHeader, METH_VARARGS, ""},
	{"UnprepareHeader", (PyCFunction)PyWaveHdr_UnprepareHeader, METH_VARARGS, ""},
	{NULL, (PyCFunction)NULL, 0, NULL}		// sentinel
};

PyTypeObject PyWaveHdr::type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,					// ob_size
	"PyWaveHdr",			// tp_name
	sizeof(PyWaveHdr),		// tp_basicsize
	0,					// tp_itemsize
	
	// methods
	(destructor)PyWaveHdr::dealloc,	// tp_dealloc
	(printfunc)0,				// tp_print
	(getattrfunc)PyWaveHdr::getattr,// tp_getattr
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

	"PyWaveHdr Type" // Documentation string
	};
