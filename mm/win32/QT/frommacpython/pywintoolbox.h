#ifndef INC_PYWINTOOLBOX
#define INC_PYWINTOOLBOX

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

#ifndef __EVENTS__
#include "Events.h"
#endif

int ToEventRecord(PyObject *obj, EventRecord  *pe);
int ToRect(PyObject *obj, Rect  *pr);

#endif

