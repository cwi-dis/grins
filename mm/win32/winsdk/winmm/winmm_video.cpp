
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include <windows.h>

#include "utils.h"

#include "../common/video.h"
#include "../common/platform.h"

// native video decoders/players
#include "mpeg_player.h"
#include "wnds_mpeg_input_stream.h"

#ifdef USE_GAPI
#include "../../CE/gx/inc/gx.h"
#pragma comment(lib, "..\\..\\CE\\gx\\ARM\\gx.lib")
#endif

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
	
	wnds_mpeg_input_stream *instream = new wnds_mpeg_input_stream(TextPtr(filename));
	if(instream == NULL)
		{
		char sz[MAX_PATH+32];
		sprintf(sz, "cant find file %s", filename);
		seterror("CreateVideoPlayerFromFile", sz);
		return NULL;
		}

	VideoPlayer *player = 0;

	// find/create decoder/player for given file
	player = new mpeg_player();
	if(player->set_input_stream(instream))
		return (PyObject*)PyVideoPlayer::createInstance(player);

	delete player;
	delete instream;
	seterror("CreateVideoPlayerFromFile", "cant find decoder for video format");
	return NULL;
	}

PyObject* Winmm_GetVideoDuration(PyObject *self, PyObject *args)
	{
	char *filename;
	if (!PyArg_ParseTuple(args, "s", &filename))
		return NULL;
	
	wnds_mpeg_input_stream *instream = new wnds_mpeg_input_stream(TextPtr(filename));
	if(instream ==NULL)
		{
		char sz[MAX_PATH+32];
		sprintf(sz, "cant find file %s", filename);
		seterror("CreateVideoPlayerFromFile", sz);
		return NULL;
		}

	VideoPlayer *player = 0;

	// find/create decoder/player for given file
	player = new mpeg_player();
	if(player->set_input_stream(instream))
		{
		double dur = player->get_duration();
		delete player;
		return Py_BuildValue("f", dur); 
		}

	delete player;
	delete instream;
	seterror("GetVideoDuration", "cant find decoder for video format");
	return NULL;
	}

PyObject* Winmm_GXOpenDisplay(PyObject *self, PyObject *args)
	{
	HWND hWnd;
	if (!PyArg_ParseTuple(args, "i", &hWnd))
		return NULL;
#ifdef USE_GAPI
	GXOpenDisplay(hWnd, GX_FULLSCREEN);
#endif
	return none();
	}

PyObject* Winmm_GXCloseDisplay(PyObject *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
#ifdef USE_GAPI
	GXCloseDisplay();
#endif
	return none();
	}

///////////////////////////////////////////
// module

static PyObject* PyVideoPlayer_GetVideoSize(PyVideoPlayer *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	return Py_BuildValue("ii", self->m_player->get_width(), self->m_player->get_height()); 
	}

static PyObject* PyVideoPlayer_GetVideoFrameRate(PyVideoPlayer *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	return Py_BuildValue("f", self->m_player->get_frame_rate()); 
	}

static PyObject* PyVideoPlayer_GetVideoBitRate(PyVideoPlayer *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	return Py_BuildValue("f", self->m_player->get_bit_rate()); 
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

// for use with GAPI
static PyObject* PyVideoPlayer_SetDirectUpdateBox(PyVideoPlayer *self, PyObject *args)
	{
	int x, y, w, h;
	if (!PyArg_ParseTuple(args,"(iiii)", &x, &y, &w, &h))
		return NULL;
	self->m_player->set_direct_update_box(x, y, w, h);
	return none(); 
	}

PyMethodDef PyVideoPlayer::methods[] = {
	{"GetVideoSize", (PyCFunction)PyVideoPlayer_GetVideoSize, METH_VARARGS, ""},
	{"GetVideoFrameRate", (PyCFunction)PyVideoPlayer_GetVideoFrameRate, METH_VARARGS, ""},
	{"GetVideoBitRate", (PyCFunction)PyVideoPlayer_GetVideoBitRate, METH_VARARGS, ""},
	{"PreparePlayback", (PyCFunction)PyVideoPlayer_PreparePlayback, METH_VARARGS, ""},
	{"SuspendPlayback", (PyCFunction)PyVideoPlayer_SuspendPlayback, METH_VARARGS, ""},
	{"ResumePlayback", (PyCFunction)PyVideoPlayer_ResumePlayback, METH_VARARGS, ""},
	{"FinishedPlayback", (PyCFunction)PyVideoPlayer_FinishedPlayback, METH_VARARGS, ""},
	{"LockSurface", (PyCFunction)PyVideoPlayer_LockSurface, METH_VARARGS, ""},
	{"UnlockSurface", (PyCFunction)PyVideoPlayer_UnlockSurface, METH_VARARGS, ""},
	{"SetDirectUpdateBox", (PyCFunction)PyVideoPlayer_SetDirectUpdateBox, METH_VARARGS, ""},
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

