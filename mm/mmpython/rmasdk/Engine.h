#ifndef INC_ENGINE
#define INC_ENGINE

interface IRMAClientEngine;
class ExampleClientContext;

IRMAClientEngine* GetEngine();
ExampleClientContext* GetContext();

void CloseEngine();
void CloseContext();
void EngineObject_AddRef();
void EngineObject_Release();

PyObject *EngineObject_CreateInstance(PyObject *self, PyObject *args);

#endif

