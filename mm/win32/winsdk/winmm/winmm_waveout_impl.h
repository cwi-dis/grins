#ifndef INC_WINMM_WAVEOUT_IMPL
#define INC_WINMM_WAVEOUT_IMPL

struct PyWaveOut
	{
	PyObject_HEAD
	HWAVEOUT m_hWaveOut;

	static PyTypeObject type;
	static PyMethodDef methods[];

	static PyWaveOut *createInstance(HWAVEOUT hWaveOut = NULL)
		{
		PyWaveOut *instance = PyObject_NEW(PyWaveOut, &type);
		if (instance == NULL) return NULL;
		instance->m_hWaveOut = hWaveOut;
		return instance;
		}

	static void dealloc(PyWaveOut *p) 
		{ 
		if(p->m_hWaveOut != NULL) 
			waveOutClose(p->m_hWaveOut);
		PyMem_DEL(p);
		}

	static PyObject *getattr(PyWaveOut *instance, char *name)
		{ 
		return Py_FindMethod(methods, (PyObject*)instance, name);
		}
	};

#endif
