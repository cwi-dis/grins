#ifndef INC_WIN32EXT
#define INC_WIN32EXT

#include "moddef.h"

#include "AsyncMonikerFile.h"

PyObject* py_create_html_wnd(PyObject *self, PyObject *args);
PyObject* ui_create_miniframe(PyObject *self, PyObject *args);

DECLARE_PYMODULECLASS(ig);
DECLARE_PYMODULECLASS(DS);
DECLARE_PYMODULECLASS(Util);

#define DEF_EXT_PY_METHODS \
	{"Getig",Mig::create,1},\
	{"CreateHtmlWnd",py_create_html_wnd,1},\
	{"GetDS",MDS::create,1},\
	{"CreateAsyncMonikerFile",PyAsyncMonikerFile::Create,1},\
	{"GetUtil",MUtil::create,1},\
	{"CreateMiniFrame",ui_create_miniframe,1},

#endif



