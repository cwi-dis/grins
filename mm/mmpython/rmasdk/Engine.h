#ifndef INC_ENGINE
#define INC_ENGINE

interface IRMAClientEngine;

IRMAClientEngine* GetEngine();
void CloseEngine();
void EngineObject_AddRef();
void EngineObject_Release();
PyObject *EngineObject_CreateInstance(PyObject *self, PyObject *args);

#endif

