#ifndef INC_UTIL
#define INC_UTIL

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

////////////////////////////////////////////////
// python_type_object

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
		m_methods = methods;
		tp_name = (char*)name;
		tp_basicsize = sizeof(Object);
		}
	~python_type_object() {}

	Object* makeObject()
		{
		Object *self = PyObject_NEW(Object, (PyTypeObject*)this);
		if(self == NULL) return NULL;
		Object::Initialize(self);
		return self;
		}
	static void dealloc(Object *self)
		{
		Object::Release(self);
		PyMem_DEL(self);
		}
	static PyObject* getattr(Object *self, char *name)
		{
		python_type_object *type = (python_type_object*)self->ob_type;
		return Py_FindMethod(type->m_methods, (PyObject*)self, name);
		}

	struct PyMethodDef* m_methods;
	};

#endif
