
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include <windows.h>
#include <mmsystem.h>

#include "utils.h"

////////////////////////////////////////
// define LINK_MP3LIB to include mp3 decode support

#ifdef LINK_MP3LIB

#include "../../CE/mp3lib/mp3lib.h"

// just in case we need instance variables (state)
struct PyMP3Decoder
	{
	PyObject_HEAD

	static PyTypeObject type;
	static PyMethodDef methods[];

	static PyMP3Decoder *createInstance(int equalizer, char *eqfactors)
		{
		PyMP3Decoder *instance = PyObject_NEW(PyMP3Decoder, &type);
		if (instance == NULL) return NULL;
		mp3_lib_init(equalizer, eqfactors);
		return instance;
		}

	static void dealloc(PyMP3Decoder *p) 
		{ 
		mp3_lib_finalize();
		PyMem_DEL(p);
		}

	static PyObject *getattr(PyMP3Decoder *instance, char *name)
		{ 
		return Py_FindMethod(methods, (PyObject*)instance, name);
		}
	};

PyObject* Winmm_CreateMp3Decoder(PyObject *self, PyObject *args)
	{
	int equalizer = 0;
	char *eqfactors = NULL;
	if (!PyArg_ParseTuple(args, "|is", &equalizer, &eqfactors))
		return NULL;
	return (PyObject*)PyMP3Decoder::createInstance(equalizer, eqfactors);
	}

///////////////////////////////////////////
// module

// for use with WaveOutQuery/WaveOutOpen
static PyObject* MP3Decoder_GetWaveFormat(PyMP3Decoder *self, PyObject *args)
	{
	PyObject *obj;
	int nSamplesPerSec = 0;
	if (!PyArg_ParseTuple(args,"S|i",&obj, &nSamplesPerSec))
		return NULL;
	unsigned char *inbuf = (unsigned char*)PyString_AS_STRING(obj);
	int insize = PyString_GET_SIZE(obj);
	int nChannels, BitRate;
	mp3_lib_decode_header(inbuf, insize, &nSamplesPerSec, &nChannels, &BitRate);
	int wBitsPerSample = 16; 
	int nBlockAlign = nChannels*wBitsPerSample/8; 
	long nAvgBytesPerSec = nBlockAlign*nSamplesPerSec;
	return Py_BuildValue("(illii)", nChannels, long(nSamplesPerSec), nAvgBytesPerSec, nBlockAlign, wBitsPerSample); 
	}

// mp3_lib_decode_header
static PyObject* MP3Decoder_DecodeHeader(PyMP3Decoder *self, PyObject *args)
	{
	PyObject *obj;
	int nSamplesPerSec = 0;
	if (!PyArg_ParseTuple(args,"S|i",&obj, &nSamplesPerSec))
		return NULL;
	unsigned char *inbuf = (unsigned char*)PyString_AS_STRING(obj);
	int insize = PyString_GET_SIZE(obj);
	int nChannels, BitRate;
	mp3_lib_decode_header(inbuf, insize, &nSamplesPerSec, &nChannels, &BitRate);
	return Py_BuildValue("(iii)", nSamplesPerSec, nChannels, BitRate); 
	}

// mp3_lib_decode_buffer
static PyObject* MP3Decoder_DecodeBuffer(PyMP3Decoder *self, PyObject *args)
	{
	PyObject *obj = NULL;
	int outbufsize = 4800;
	if (!PyArg_ParseTuple(args,"|Si",&obj, &outbufsize))
		return NULL;

	unsigned char *inbuf = NULL;
	int insize = 0;	
	if(obj != NULL)
		{
		inbuf = (unsigned char*)PyString_AS_STRING(obj);
		insize = PyString_GET_SIZE(obj);
		if(insize == 0)
			inbuf = NULL;
		}
	PyObject *outbufobj = PyString_FromStringAndSize(NULL, outbufsize);
	if(outbufobj == NULL)
		return NULL;
	char *outbuf = PyString_AsString(outbufobj);
	int done = 0, inputpos = 0;
	int status = mp3_lib_decode_buffer(inbuf, insize, outbuf, outbufsize, &done, &inputpos);
	PyObject *rv = Py_BuildValue("(Oiii)", outbufobj, done, inputpos, status);
	Py_DECREF(outbufobj);
	return rv;
	}

static PyObject* MP3Decoder_Reset(PyMP3Decoder *self, PyObject *args)
	{
	int equalizer = 0;
	char *eqfactors = 0;
	if (!PyArg_ParseTuple(args, "|is", &equalizer, &eqfactors))
		return NULL;
	mp3_lib_finalize();
	mp3_lib_init(equalizer, eqfactors);
	return none();
	}

PyMethodDef PyMP3Decoder::methods[] = {
	{"GetWaveFormat", (PyCFunction)MP3Decoder_GetWaveFormat, METH_VARARGS, ""},
	{"DecodeHeader", (PyCFunction)MP3Decoder_DecodeHeader, METH_VARARGS, ""},
	{"DecodeBuffer", (PyCFunction)MP3Decoder_DecodeBuffer, METH_VARARGS, ""},
	{"Reset", (PyCFunction)MP3Decoder_Reset, METH_VARARGS, ""},
	{NULL, (PyCFunction)NULL, 0, NULL}		// sentinel
};

PyTypeObject PyMP3Decoder::type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,					// ob_size
	"PyMP3Decoder",			// tp_name
	sizeof(PyMP3Decoder),		// tp_basicsize
	0,					// tp_itemsize
	
	// methods
	(destructor)PyMP3Decoder::dealloc,	// tp_dealloc
	(printfunc)0,				// tp_print
	(getattrfunc)PyMP3Decoder::getattr,// tp_getattr
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

	"PyMP3Decoder Type" // Documentation string
	};

#endif // LINK_MP3LIB
//////////////////////////////////