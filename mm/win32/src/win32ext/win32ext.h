#ifndef INC_WIN32EXT
#define INC_WIN32EXT

#include "moddef.h"

PyObject* py_create_html_wnd(PyObject *self, PyObject *args);

DECLARE_PYMODULECLASS(ig);
DECLARE_PYMODULECLASS(DS);
DECLARE_PYMODULECLASS(Util);



#define DEF_EXT_PY_METHODS \
	{"Getig",Mig::create,1},\
	{"CreateHtmlWnd",py_create_html_wnd,1},\
	{"GetDS",MDS::create,1},\
	{"GetUtil",MUtil::create,1},

#endif



