#include "std.h"
#include "PyCppApi.h"

// Cpp framework 
// for modules that export PyObjects

// For rapid-dev we borrow win32ui's core mechanisms
// we 'll revisit this module

// Using Std C++ (not MFC or other lib)

// Associations (a central win32ui mechanism) has been removed
// If the need arises, reimplement them in a cleaner not intrusive way


////////////////////////////////////////////////
////////////////////////////////////////////////
// TypeObject

TypeObject::TypeObject(const char *name,TypeObject *pBase,int typeSize,
	struct PyMethodDef* methodList, Object *(*thector)())
	{
	static PyTypeObject type_template = 
		{
		PyObject_HEAD_INIT(&PyType_Type)
		0,											/*ob_size*/
		"unnamed",									/*tp_name*/
		sizeof(Object), 							/*tp_size*/
		0,											/*tp_itemsize*/
		(destructor)  Object::so_dealloc, 			/*tp_dealloc*/
		0,											/*tp_print*/
		(getattrfunc) Object::so_getattr, 			/*tp_getattr*/
		(setattrfunc) Object::so_setattr,			/*tp_setattr*/
		0,											/*tp_compare*/
		(reprfunc)    Object::so_repr,				/*tp_repr*/
    	0,											/*tp_as_number*/
		};

	// copy type_template to this PyTypeObject part
	*((PyTypeObject *)this) = type_template;

	methods = methodList;
	tp_name = (char*)name;
	tp_basicsize = typeSize;
	base = pBase;
	ctor = thector;
	}
TypeObject::~TypeObject()
	{
	}

////////////////////////////////////////////////
////////////////////////////////////////////////
// Object

Object::Object()
	{
	}

Object::~Object()
	{
	#ifdef TRACE_LIFETIMES
	TRACE("Destructing a '%s' at %p\n", ob_type->tp_name, this);
	#endif
	}

Object *Object::make(TypeObject &makeTypeRef)
	{
	TypeObject *makeType = &makeTypeRef; // use to pass ptr as param!
	if (makeType->ctor==NULL)
		RETURN_ERR("Internal error - the type does not declare a constructor");	
	Object *pNew = (*makeType->ctor)();
	pNew->ob_type = makeType;
	_Py_NewReference(pNew);
	#ifdef TRACE_LIFETIMES
	TRACE("Constructing a '%s' at %p\n",pNew->ob_type->tp_name, pNew);
	#endif
	return pNew;
	}

/*static*/ 
BOOL Object::is_object(PyObject *&o,TypeObject *which)
	{
	Object *ob = (Object *)o;
	if (ob==NULL || ob==Py_None)
		return FALSE;
	// quick fasttrack.
	if ((TypeObject *)ob->ob_type==which)
		return TRUE;
	// if Python instance, my be able to derive the paired Python type.
	if (PyInstance_Check(ob)) 
		{
		PyObject *obattr= PyObject_GetAttrString(ob, "_obj_");
		if (obattr==NULL) 
			{
			PyErr_Clear();
			TRACE("is_object fails due to object being an instance without an _obj_ attribute!\n");
			return FALSE;
			}
		if (obattr==Py_None) 
			{
			TRACE("is_object fails due to object being an instance with _obj_==None\n");
			return FALSE;
			}
		o = obattr;
		ob = (Object *)o;
		}
	return is_nativeobject(ob, which);
	}

/*static*/
BOOL Object::is_nativeobject(PyObject *ob, TypeObject *which)
	{
	// check for inheritance.
	TypeObject *thisType = (TypeObject *)ob->ob_type;
	while (thisType) 
		{
		if (which==thisType) return TRUE;
		thisType = thisType->base;
		}
	return FALSE;
	}

BOOL Object::is_object(TypeObject *which)
	{
	PyObject *cpy = this;
	BOOL ret = is_object(cpy,which);
	return ret;
	}

PyObject* Object::so_getattr(PyObject *self, char *name)
	{
	return ((Object *)self)->getattr(name);
	}

PyObject* Object::getattr(char *name)
	{
	// implement inheritance.
	PyObject *retMethod = NULL;
	TypeObject *thisType = (TypeObject *)ob_type;
	while (thisType) 
		{
		retMethod = Py_FindMethod(thisType->methods,(PyObject *)this,name);
		if (retMethod) break;
		thisType = thisType->base;
		if (thisType)PyErr_Clear();
		}
	return retMethod;
	}

int Object::so_setattr(PyObject *op, char *name, PyObject *v)
	{
	Object* bc = (Object *)op;
	return bc->setattr(name,v);
	}

int Object::setattr(char *name, PyObject *v)
	{
	char buf[128];
	sprintf(buf, "%s has read-only attributes", ob_type->tp_name );
	PyErr_SetString(PyExc_TypeError, buf);
	return -1;
	}

/*static*/ 
PyObject* Object::so_repr(PyObject *op)
	{
	Object* w = (Object *)op;
	string ret = w->repr();
	return Py_BuildValue("s",ret.c_str());
	}

string Object::repr()
	{
	string csRet;
	char buf[50];
	sprintf(buf, "object '%s'", ob_type->tp_name);
	return string(buf);
	}

void Object::cleanup()
	{
	string rep = repr();
	TRACE("cleanup detected %s, refcount = %d\n",rep.c_str(),ob_refcnt);
	}

/*static*/ 
void Object::so_dealloc(PyObject *obj)
	{
	delete (Object*)obj;
	}

// @pymethod |PyAssocObject|GetMethodByType|Given a method name and a type object, return the attribute.
/*static*/ 
PyObject* Object::GetMethodByType(PyObject *self, PyObject *args)
	{
	// @comm This function allows you to obtain attributes for base types.
	PyObject *obType;
	char *attr;
	Object *pAssoc = (Object *)self;
	if (pAssoc==NULL) return NULL;
	if (!PyArg_ParseTuple(args, "sO:GetAttributeByType", &attr, &obType ))
		return NULL;

	// check it is one of ours.
	PyObject *retMethod = NULL;
	TypeObject *thisType = (TypeObject *)pAssoc->ob_type;
	while (thisType) 
		{
		if ((PyObject *)thisType==obType)break;
		thisType = thisType->base;
		}
	if (thisType==NULL)
		RETURN_TYPE_ERR("The object is not of that type");
	return Py_FindMethod(thisType->methods, self, attr);
	}

struct PyMethodDef Object_methods[] = {
	{"GetMethodByType",Object::GetMethodByType,1},
	{NULL,	NULL}
};

TypeObject Object::type("Object", 
						NULL, 
						sizeof(Object), 
						Object_methods, 
						NULL);


////////////////////////////////////////////////
////////////////////////////////////////////////
// CallerHelper

CallerHelper::CallerHelper(const char *methodname,PyObject *obj)
:	handler(NULL),
	py_ob(NULL),
	retVal(NULL)
	{
	if(!methodname || !obj) return;
	csHandlerName = methodname;
	CEnterLeavePython elp;
	PyObject *t, *v, *tb;
	PyErr_Fetch(&t,&v,&tb);
	handler = PyObject_GetAttrString(obj,(char*)methodname);
	if (handler) 
		{
		// explicitely check a method returned, else the classes
		// delegation may cause a circular call chain.
		if (!PyMethod_Check(handler)) 
			{
			if (!PyCFunction_Check(handler))
				TRACE("Handler for object is not a method!\n");
			DODECREF(handler);
			handler = NULL;
			}
		}
	PyErr_Restore(t,v,tb);
	py_ob = obj;
	Py_INCREF(py_ob);
	//Py_XINCREF(handler);
	}
CallerHelper::~CallerHelper()
	{
	// XXX - Gross hack for speed.  This is called for eachh window message
	// so only grabs the Python lock if the objects need Python,
	if((retVal && retVal->ob_refcnt==1) || 
		(handler && handler->ob_refcnt==1) || 
		(py_ob && py_ob->ob_refcnt==1)) 
		{
		CEnterLeavePython _celp;
		XDODECREF(retVal);
		XDODECREF(handler);
		XDODECREF(py_ob);
		} 
	else 
		{
		XDODECREF(retVal);
		XDODECREF(handler);
		XDODECREF(py_ob);
		}
	}
PyObject *CallerHelper::GetHandler()
	{
	return handler;
	}
BOOL CallerHelper::do_call(PyObject *args)
	{
	CEnterLeavePython _celp;
	XDODECREF(retVal);	// our old one.
	retVal = NULL;
	ASSERT(handler);	// caller must trap this.
	ASSERT(args);
	PyObject *result = PyEval_CallObject(handler,args);
	DODECREF(args);
	if (result==NULL) 
		{
		char msg[256];
		TRACE("CallVirtual : callback failed with exception\n");
		print_error();
		PyObject *obRepr = PyObject_Repr(handler);
		char *szRepr = PyString_AsString(obRepr);
		sprintf(msg, "%s() virtual handler (%s) raised an exception",csHandlerName.c_str(), szRepr);
		Py_XDECREF(obRepr);
		PyErr_SetString(module_error, msg);
		print_error();
		return FALSE;
		}
	retVal = result;
	return TRUE;
	}

BOOL CallerHelper::call_args(PyObject *arglst)
	{
	if (!handler) return FALSE;
	return do_call(arglst);
	}

BOOL CallerHelper::call()
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("()");
	return do_call(arglst);
	}

BOOL CallerHelper::call(int val)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(i)",val);
	return do_call(arglst);
	}

BOOL CallerHelper::call(int val1, int val2)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(ii)",val1, val2);
	return do_call(arglst);
	}

BOOL CallerHelper::call(int val1, int val2, int val3)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(iii)",val1, val2, val3);
	return do_call(arglst);
	}

BOOL CallerHelper::call(int val1, int val2, int val3, int val4)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(iiii)",val1, val2, val3, val4);
	return do_call(arglst);
	}

BOOL CallerHelper::call(int val1, int val2, int val3, const char *val4)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(iiiz)",val1, val2, val3, val4);
	return do_call(arglst);
	}

BOOL CallerHelper::call(int val1, int val2, int val3, const char *val4, void* data)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(iiizl)",val1, val2, val3, val4, data);
	return do_call(arglst);
	}

BOOL CallerHelper::call(long val)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(l)",val);
	return do_call(arglst);
	}

BOOL CallerHelper::call(const char *val)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(z)",val);
	return do_call(arglst);
	}

BOOL CallerHelper::call(const char *val, int ival)
	{
	if(!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(zi)",val,ival);
	return do_call(arglst);
	}

BOOL CallerHelper::call(PyObject *ob)
	{
	if (!handler) return FALSE;
	if (!ob) ob=Py_None;
	PyObject *arglst = Py_BuildValue("(O)",ob);
	return do_call(arglst);
	}

BOOL CallerHelper::call(PyObject *ob, PyObject *ob2)
	{
	if (!handler) return FALSE;
	if (!ob)ob=Py_None;
	if (!ob2)ob2=Py_None;
	PyObject *arglst = Py_BuildValue("(OO)",ob, ob2);
	return do_call(arglst);
	}

BOOL CallerHelper::call(PyObject *ob, PyObject *ob2, int i)
	{
	if (!handler) return FALSE;
	if (!ob)
		ob=Py_None;
	if (!ob2)
		ob2=Py_None;
	PyObject *arglst = Py_BuildValue("(OOi)",ob, ob2, i);
	return do_call(arglst);
	}

BOOL CallerHelper::retnone()
	{
	ASSERT(retVal);
	if (!retVal)
		return FALSE;	// failed - assume didnt work in non debug
	return (retVal==Py_None);
	}

BOOL CallerHelper::retval( int &ret )
	{
	ASSERT(retVal);
	if (!retVal)
		return FALSE;	// failed - assume didnt work in non debug
	if (retVal==Py_None) 
		{
		ret = 0;
		return TRUE;
		}
	CEnterLeavePython _celp;
	ret = PyInt_AsLong(retVal);
	return !PyErr_Occurred();
	}

BOOL CallerHelper::retval( long &ret )
	{
	ASSERT(retVal);
	if (!retVal)
		return FALSE;	// failed - assume didnt work in non debug
	if (retVal==Py_None) 
		{
		ret = 0;
		return TRUE;
		}
	CEnterLeavePython _celp;
	ret = PyInt_AsLong(retVal);
	if (PyErr_Occurred()) 
		{
		PyErr_Clear();
		return FALSE;
		}
	return TRUE;
	}

BOOL CallerHelper::retval( char *&ret )
	{
	ASSERT(retVal);
	if (!retVal)
		return FALSE;	// failed - assume didnt work in non debug
	if (retVal==Py_None) 
		{
		ret = NULL;
		return TRUE;
		}
	CEnterLeavePython _celp;
	ret = PyString_AsString(retVal);
	if (PyErr_Occurred()) 
		{
		PyErr_Clear();
		return FALSE;
		}
	return TRUE;
	}

BOOL CallerHelper::retval(string &ret)
	{
	ASSERT(retVal);
	if (!retVal)
		return FALSE;	// failed - assume didnt work in non debug
	if (retVal==Py_None) 
		{
		ret="";
		return TRUE;
		}
	CEnterLeavePython elp;
	ret = PyString_AsString(retVal);
	if (PyErr_Occurred()) 
		{
		PyErr_Clear();
		return FALSE;
		}
	return TRUE;
	}

BOOL CallerHelper::retval(_object* &ret)
	{
	ASSERT(retVal);
	if (!retVal)
		return FALSE;	// failed - assume didnt work in non debug
	CEnterLeavePython elp;
	if (!PyArg_Parse(retVal, "O",&ret)) 
		{
		PyErr_Clear();
		return FALSE;
		}
	return TRUE;
	}

void CallerHelper::print_error()
	{
	// basic recursion control.
	static BOOL bInError = FALSE;
	if (bInError) return;
	bInError=TRUE;

	// Check if the exception is SystemExit - if so,
	// PyErr_Print will terminate then and there!  This is
	// not good (and not what we want!?
	PyObject *exception, *v, *tb;
	PyErr_Fetch(&exception, &v, &tb);
	PyErr_NormalizeException(&exception, &v, &tb);

	if (exception  && PyErr_GivenExceptionMatches(exception, PyExc_SystemExit)) 
		{
		// Replace it with a RuntimeError.
		TRACE("WARNING!!  SystemError - Replacing with RuntimeError!!\n");
		Py_DECREF(exception);
		Py_XINCREF(PyExc_RuntimeError);
		PyErr_Restore(PyExc_RuntimeError, v, tb);
		} 
	else
		PyErr_Restore(exception, v, tb);
	// Now print it.

	PyErr_Print();
	bInError=FALSE;
	}


