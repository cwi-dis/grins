
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include <windows.h>
#include <mmsystem.h>

#include "winmm_wavehdr.h"

#include "utils.h"

struct PyWaveHdr
	{
	PyObject_HEAD
	WAVEHDR *m_pWaveHdr;
	PyObject *m_strObj;

	static PyTypeObject type;
	static PyMethodDef methods[];

	static PyWaveHdr *createInstance(PyObject *strObj = NULL)
		{
		PyWaveHdr *instance = PyObject_NEW(PyWaveHdr, &type);
		if (instance == NULL) return NULL;
		Py_XINCREF(strObj);
		instance->m_strObj = strObj;
		instance->m_pWaveHdr = new WAVEHDR;
		memset(instance->m_pWaveHdr, 0, sizeof(WAVEHDR));
		instance->m_pWaveHdr->dwUser = DWORD(instance);
		if(strObj != NULL)
			{
			instance->m_pWaveHdr->lpData = PyString_AS_STRING(strObj);
			instance->m_pWaveHdr->dwBufferLength = PyString_GET_SIZE(strObj);
			}
		return instance;
		}
	static void dealloc(PyWaveHdr *p) 
		{ 
		if(p->m_pWaveHdr != 0) delete p->m_pWaveHdr;
		Py_XDECREF(p->m_strObj);
		PyMem_DEL(p);
		}

	static PyObject *getattr(PyWaveHdr *instance, char *name)
		{ 
		return Py_FindMethod(methods, (PyObject*)instance, name);
		}

	};

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
	PyObject *wavOutObj;
	if (!PyArg_ParseTuple(args, "O",&wavOutObj))
		return NULL;
	HWAVEOUT hWaveOut = (HWAVEOUT)GetObjHandle(wavOutObj);
	MMRESULT mmres = waveOutPrepareHeader(hWaveOut, self->m_pWaveHdr, sizeof(WAVEHDR));
	if(mmres != MMSYSERR_NOERROR)
		{
		seterror("waveOutPrepareHeader", mmres);
		return NULL;
		}
	return none(); 
}

static PyObject* PyWaveHdr_UnprepareHeader(PyWaveHdr *self, PyObject *args)
{
	PyObject *wavOutObj;
	if (!PyArg_ParseTuple(args, "O",&wavOutObj))
		return NULL;
	HWAVEOUT hWaveOut = (HWAVEOUT)GetObjHandle(wavOutObj);
	waveOutUnprepareHeader(hWaveOut, self->m_pWaveHdr, sizeof(WAVEHDR));
	return none(); 
}

static PyObject* PyWaveHdr_HasWaveHeader(PyWaveHdr *self, PyObject *args)
{
	DWORD p;
	if (!PyArg_ParseTuple(args, "p", &p))
		return NULL;
	return Py_BuildValue("i", (p == DWORD(self->m_pWaveHdr)?1:0));
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
