// CMIF_ADD
//
// kk@epsilon.com.gr
//
#ifndef INC_WIN32EXT
#define INC_WIN32EXT

#include "moddef.h"

PyObject* py_create_html_wnd(PyObject *self, PyObject *args);

DECLARE_PYMODULECLASS(Gifex);
DECLARE_PYMODULECLASS(ig);
DECLARE_PYMODULECLASS(DS);



#define DEF_EXT_PY_METHODS \
	{"GetGifex",MGifex::create,1},\
	{"Getig",Mig::create,1},\
	{"CreateHtmlWnd",py_create_html_wnd,1},\
	{"GetDS",MDS::create,1},

#endif



