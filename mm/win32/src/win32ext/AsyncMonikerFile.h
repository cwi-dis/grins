#ifndef INC_ASYNCMONFILE
#define INC_ASYNCMONFILE

// include naming preferences
#ifndef INC_MODDEF
#include "moddef.h"
#endif

class AsyncMonikerFile;

// A PyObject that exports the functionality of CAsyncMonikerFile 
class PyAsyncMonikerFile : public CPyObject
	{
	public:
	// BGN_STD_PATTERN
	static CPyTypeObject type;
	static CPyObject *CreateInstance() {return new PyAsyncMonikerFile;}
	static CPyTypeObject* GetBaseType(){return &CPyObject::type;}
	static PyObject *Create(PyObject *self, PyObject *args);
	// END_STD_PATTERN
	
	PyAsyncMonikerFile();
	~PyAsyncMonikerFile();
	AsyncMonikerFile *GetAsyncMonikerFile(){return m_pAsyncMonikerFile;}
	private:
	AsyncMonikerFile *m_pAsyncMonikerFile;
	};

#endif // INC_ASYNCMONFILE
