#ifndef INC_UTILS
#define INC_UTILS

template<class Object>
class python_type_object : public PyTypeObject 
	{
	public:
	python_type_object(const char *name, struct PyMethodDef* methods, const char *doc=0)
		{
		static PyTypeObject type_template = {
			PyObject_HEAD_INIT(&PyType_Type)
			0,						// ob_size
			"placeholder",			// tp_name
			0,						// tp_basicsize
			0,						// tp_itemsize
			// methods 
			(destructor)dealloc,	// tp_dealloc
			(printfunc)0,			// tp_print
			(getattrfunc)getattr,	// tp_getattr
			(setattrfunc)0,			// tp_setattr
			(cmpfunc)0,				// tp_compare
			(reprfunc)0,			// tp_repr
			0,						// tp_as_number
			0,						// tp_as_sequence
			0,						// tp_as_mapping
			(hashfunc)0,			// tp_hash
			(ternaryfunc)0,			// tp_call
			(reprfunc)0,			// tp_str
			// Space for future expansion 
			0L,0L,0L,0L,
			(char*) doc				// Documentation string 
			};
		*((PyTypeObject*)this) = type_template;
		tp_name = (char*)name;
		m_methods = methods;
		tp_basicsize = sizeof(Object);
		}
	~python_type_object() {}

	Object* CreateInstance()
		{
		Object *self = PyObject_NEW(Object, (PyTypeObject*)this);
		if(self == NULL) return NULL;
		Object::InitInstance(self);
		return self;
		}
	static void dealloc(Object *self)
		{
		self->Release();
		PyMem_DEL(self);
		}
	static PyObject* getattr(Object *self, char *name)
		{
		python_type_object *type = (python_type_object*)self->ob_type;
		return Py_FindMethod(type->m_methods, (PyObject*)self, name);
		}

	struct PyMethodDef* m_methods;
	};

class PyPtListConverter
	{
	public:
	PyPtListConverter() 
	:	m_numpoints(0), m_ppt(NULL) {sz[0]='\0';}

	bool convert(PyObject *pyptlist)
		{
		if(m_ppt!=NULL) delete[] m_ppt;
		m_numpoints = PyList_Size(pyptlist);
		m_ppt = new POINT[m_numpoints];
		for(int i=0;i<m_numpoints;i++) 
			{
			PyObject * pypt = PyList_GetItem(pyptlist, i);
			if(!PyTuple_Check(pypt) || PyTuple_Size(pypt)!=2) 
				{
				strcpy(sz, "PyTuple_Check or PyTuple_Size");
				return false;
				}
			else if(!getPoint(pypt, m_ppt[i]))
				return false;
			}
		return true;
		}
	~PyPtListConverter(){if(m_ppt) delete[] m_ppt;}

	int getSize() const {return m_numpoints;}
	const POINT *getPoints() const {return m_ppt;}
	const char* getErrorStr() const {return sz;}

	private:
	bool getPoint(PyObject *pypt, POINT& pt)
		{
		PyObject *px = PyTuple_GetItem(pypt, 0);
		PyObject *py = PyTuple_GetItem (pypt, 1);
		if((!PyInt_Check(px)) || (!PyInt_Check(py)))
			{
			strcpy(sz, "PyInt_Check");
			return false;
			}
		pt.x = PyInt_AsLong(px);
		pt.y = PyInt_AsLong(py);
		return true;
		}
	char sz[80];
	int m_numpoints;
	POINT *m_ppt;
	};

class PyIntListConverter
	{
	public:
	PyIntListConverter() 
	:	m_num(0), m_pint(NULL), m_pbyte(NULL) {}

	bool convert(PyObject *pylist)
		{
		if(m_pint!=NULL) delete[] m_pint;
		m_num = PyList_Size(pylist);
		m_pint = new int[m_num];
		for(int i=0;i< m_num;i++) 
			{
			PyObject * pyval = PyList_GetItem(pylist, i);
			if(!PyInt_Check(pyval)) 
				return false;
			m_pint[i] = PyInt_AsLong(pyval);
			}
		return true;
		}
	~PyIntListConverter()
		{
		if(m_pint)delete[] m_pint;
		if(m_pbyte)delete[] m_pbyte;
		}

	int getSize() const {return m_num;}
	const int *getInts() const {return m_pint;}
	const BYTE *packInts()
		{
		if(!m_pint || m_num==0)
			return NULL;
		if(m_pbyte!=NULL) delete[] m_pbyte;
		m_pbyte = new BYTE[m_num];
		for(int i=0;i<m_num;i++) 
			m_pbyte[i]=BYTE(m_pint[i]);
		return m_pbyte;
		}
	private:
	int m_num;
	int *m_pint;
	BYTE *m_pbyte;
	};

class PyDictParser 
	{
	public:
	PyDictParser(PyObject *pydict)
		: m_pydict(pydict){}

	bool hasAttr(const char *name)
		{
		return PyDict_GetItemString(m_pydict, (char*)name)!=NULL;
		}

	int getIntAttr(const char *name, int defvalue=0)
		{
		PyObject *v = PyDict_GetItemString(m_pydict, (char*)name);
		if(v && PyInt_Check(v))
			return PyInt_AsLong(v);
		return defvalue;
		}

	const char* getStrAttr(const char *name, char *buf, int n, const char *pszdefault)
		{
		PyObject *v = PyDict_GetItemString(m_pydict, (char*)name);
		if(v && PyString_Check(v))
			{
			n = min(PyString_GET_SIZE(v), n);
			strncpy(buf, PyString_AsString(v), n-1);
			buf[n-1] = '\0';
			return buf;
			}
		n = min((int)strlen(pszdefault), n);
		strncpy(buf, pszdefault, n-1);
		buf[n-1] = '\0';
		return buf;
		}

	private:
	PyObject *m_pydict;
	};

#endif

