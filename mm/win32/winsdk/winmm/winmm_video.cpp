
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include <windows.h>

#include "utils.h"

#include "../common/video.h"
#include "../common/platform.h"

// native video decoders/players
#include "../mpeg2dec/mpeg_player.h"

struct PyVideoPlayer
	{
	PyObject_HEAD
	VideoPlayer *m_player;
	PyObject *m_py_dib_surf;

	static PyTypeObject type;
	static PyMethodDef methods[];

	static PyVideoPlayer *createInstance(VideoPlayer *player = 0)
		{
		PyVideoPlayer *instance = PyObject_NEW(PyVideoPlayer, &type);
		if (instance == NULL) return NULL;
		instance->m_player = player;
		instance->m_py_dib_surf = 0;
		return instance;
		}

	static void dealloc(PyVideoPlayer *p) 
		{ 
		if(p->m_player != 0)
			{
			p->m_player->close();
			delete p->m_player;
			}
		Py_XDECREF(p->m_py_dib_surf);
		PyMem_DEL(p);
		}

	static PyObject *getattr(PyVideoPlayer *instance, char *name)
		{ 
		return Py_FindMethod(methods, (PyObject*)instance, name);
		}
	};

PyObject* Winmm_CreateVideoPlayerFromFile(PyObject *self, PyObject *args)
	{
	char *filename;
	if (!PyArg_ParseTuple(args, "s", &filename))
		return NULL;
	
	int handle = platform::open(TextPtr(filename));
	if(handle == -1)
		{
		char sz[MAX_PATH+32];
		sprintf(sz, "cant find file %s", filename);
		seterror("CreateVideoPlayerFromFile", sz);
		return NULL;
		}

	VideoPlayer *player = 0;

	// find/create decoder/player for given file
	player = new MpegPlayer();
	if(player->can_decode(handle))
		return (PyObject*)PyVideoPlayer::createInstance(player);
	else
		delete player;

	platform::close(handle);
	seterror("CreateVideoPlayerFromFile", "cant find decoder for video format");
	return NULL;
	}

///////////////////////////////////////////
// module

static PyObject* PyVideoPlayer_GetVideoSize(PyVideoPlayer *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	return Py_BuildValue("ii", self->m_player->get_width(), self->m_player->get_height()); 
	}

static PyObject* PyVideoPlayer_GetVideoDuration(PyVideoPlayer *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	return Py_BuildValue("f", self->m_player->get_duration()); 
	}

static PyObject* PyVideoPlayer_PreparePlayback(PyVideoPlayer *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	
	HDC hdc = GetDC(NULL);
	int w = self->m_player->get_width();
	int h = self->m_player->get_height();

	PyObject* wingdi_mod = PyImport_ImportModule("wingdi");
	if(wingdi_mod == NULL)
		{
		seterror("PreparePlayback()", " import wingdi module failed");
		return NULL;
		}
	PyObject *d = PyModule_GetDict(wingdi_mod);
	PyObject *ga = PyDict_GetItemString(d, "CreateDIBSurface");
	PyObject *arglist = Py_BuildValue("iii", int(hdc), w, h);
	PyObject *retobj = PyEval_CallObject(ga, arglist);
	Py_DECREF(arglist);
	if (retobj == NULL)
		{
		PyErr_Print();
		PyErr_Clear();
		return NULL;
		}
	Py_DECREF(wingdi_mod);
	DeleteDC(hdc);

	// keep a copy since will be used by video player
	Py_INCREF(retobj);
	self->m_py_dib_surf = retobj;

	surface<color_repr_t> *psurf = GetPyDIBSurfPtr(retobj);
	self->m_player->prepare_playback(psurf);

	return retobj;
	}

static PyObject* PyVideoPlayer_SuspendPlayback(PyVideoPlayer *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	self->m_player->suspend_playback();
	return none(); 
	}

static PyObject* PyVideoPlayer_ResumePlayback(PyVideoPlayer *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	self->m_player->resume_playback();
	return none(); 
	}

static PyObject* PyVideoPlayer_FinishedPlayback(PyVideoPlayer *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	int ret = self->m_player->finished_playback()?1:0;
	return Py_BuildValue("i", ret); 
	}

static PyObject* PyVideoPlayer_LockSurface(PyVideoPlayer *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	self->m_player->lock_surface();
	return none(); 
	}

static PyObject* PyVideoPlayer_UnlockSurface(PyVideoPlayer *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	self->m_player->unlock_surface();
	return none(); 
	}

PyMethodDef PyVideoPlayer::methods[] = {
	{"GetVideoSize", (PyCFunction)PyVideoPlayer_GetVideoSize, METH_VARARGS, ""},
	{"GetVideoDuration", (PyCFunction)PyVideoPlayer_GetVideoDuration, METH_VARARGS, ""},
	{"PreparePlayback", (PyCFunction)PyVideoPlayer_PreparePlayback, METH_VARARGS, ""},
	{"SuspendPlayback", (PyCFunction)PyVideoPlayer_SuspendPlayback, METH_VARARGS, ""},
	{"ResumePlayback", (PyCFunction)PyVideoPlayer_ResumePlayback, METH_VARARGS, ""},
	{"FinishedPlayback", (PyCFunction)PyVideoPlayer_FinishedPlayback, METH_VARARGS, ""},
	{"LockSurface", (PyCFunction)PyVideoPlayer_LockSurface, METH_VARARGS, ""},
	{"UnlockSurface", (PyCFunction)PyVideoPlayer_UnlockSurface, METH_VARARGS, ""},
	{NULL, (PyCFunction)NULL, 0, NULL}		// sentinel
};

PyTypeObject PyVideoPlayer::type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,					// ob_size
	"PyVideoPlayer",			// tp_name
	sizeof(PyVideoPlayer),		// tp_basicsize
	0,					// tp_itemsize
	
	// methods
	(destructor)PyVideoPlayer::dealloc,	// tp_dealloc
	(printfunc)0,				// tp_print
	(getattrfunc)PyVideoPlayer::getattr,// tp_getattr
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

	"PyVideoPlayer Type" // Documentation string
	};

