#ifndef INC_WINMM_WAVEHDR_IMPL
#define INC_WINMM_WAVEHDR_IMPL

struct PyWaveHdr
	{
	PyObject_HEAD
	WAVEHDR *m_pWaveHdr;
	PyObject *m_strObj;

	static PyTypeObject type;
	static PyMethodDef methods[];

	static PyWaveHdr *createInstance(PyObject *strObj = NULL)
		{
		PyWaveHdr *instance = PyObject_NEW(PyWaveHdr, &type);
		if (instance == NULL) return NULL;
		Py_XINCREF(strObj);
		instance->m_strObj = strObj;
		instance->m_pWaveHdr = new WAVEHDR;
		memset(instance->m_pWaveHdr, 0, sizeof(WAVEHDR));
		instance->m_pWaveHdr->dwUser = DWORD(instance);
		if(strObj != NULL)
			{
			instance->m_pWaveHdr->lpData = PyString_AS_STRING(strObj);
			instance->m_pWaveHdr->dwBufferLength = PyString_GET_SIZE(strObj);
			}
		return instance;
		}
	static void dealloc(PyWaveHdr *p) 
		{ 
		if(p->m_pWaveHdr != 0) delete p->m_pWaveHdr;
		Py_XDECREF(p->m_strObj);
		PyMem_DEL(p);
		}

	static PyObject *getattr(PyWaveHdr *instance, char *name)
		{ 
		return Py_FindMethod(methods, (PyObject*)instance, name);
		}

	};

#endif

