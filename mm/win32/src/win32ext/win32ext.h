#ifndef INC_WIN32EXT
#define INC_WIN32EXT

#include "moddef.h"

#include "AsyncMonikerFile.h"

PyObject* py_create_html_wnd(PyObject *self, PyObject *args);
PyObject* py_has_svg_support(PyObject *self, PyObject *args);
PyObject* py_create_svg_wnd(PyObject *self, PyObject *args);
PyObject* ui_create_miniframe(PyObject *self, PyObject *args);

DECLARE_PYMODULECLASS(ig);
DECLARE_PYMODULECLASS(Util);

#define DEF_EXT_PY_METHODS \
	{"CreateHtmlWnd",py_create_html_wnd,1},\
	{"HasSvgSupport",py_has_svg_support,1},\
	{"CreateSvgWnd",py_create_svg_wnd,1},\
	{"CreateAsyncMonikerFile",PyAsyncMonikerFile::Create,1},\
	{"GetUtil",MUtil::create,1},\
	{"CreateMiniFrame",ui_create_miniframe,1},

#endif



