#include "Std.h"
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
	struct PyMethodDef* methodList, RMAObject *(*thector)())
	{
	static PyTypeObject type_template = 
		{
		PyObject_HEAD_INIT(&PyType_Type)
		0,											/*ob_size*/
		"unnamed",									/*tp_name*/
		sizeof(RMAObject), 							/*tp_size*/
		0,											/*tp_itemsize*/
		(destructor)  RMAObject::so_dealloc, 			/*tp_dealloc*/
		0,											/*tp_print*/
		(getattrfunc) RMAObject::so_getattr, 			/*tp_getattr*/
		(setattrfunc) RMAObject::so_setattr,			/*tp_setattr*/
		0,											/*tp_compare*/
		(reprfunc)    RMAObject::so_repr,				/*tp_repr*/
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
// RMAObject

RMAObject::RMAObject()
	{
	}

RMAObject::~RMAObject()
	{
	#ifdef TRACE_LIFETIMES
	TRACE("Destructing a '%s' at %p\n", ob_type->tp_name, this);
	#endif
	}

RMAObject *RMAObject::make(TypeObject &makeTypeRef)
	{
	TypeObject *makeType = &makeTypeRef; // use to pass ptr as param!
	if (makeType->ctor==NULL)
		RETURN_ERR("Internal error - the type does not declare a constructor");	
	RMAObject *pNew = (*makeType->ctor)();
	pNew->ob_type = makeType;
	_Py_NewReference(pNew);
	#ifdef TRACE_LIFETIMES
	TRACE("Constructing a '%s' at %p\n",pNew->ob_type->tp_name, pNew);
	#endif
	return pNew;
	}

/*static*/ 
BOOL RMAObject::is_object(PyObject *&o,TypeObject *which)
	{
	RMAObject *ob = (RMAObject *)o;
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
		ob = (RMAObject *)o;
		}
	return is_nativeobject(ob, which);
	}

/*static*/
BOOL RMAObject::is_nativeobject(PyObject *ob, TypeObject *which)
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

BOOL RMAObject::is_object(TypeObject *which)
	{
	PyObject *cpy = this;
	BOOL ret = is_object(cpy,which);
	return ret;
	}

PyObject* RMAObject::so_getattr(PyObject *self, char *name)
	{
	return ((RMAObject *)self)->getattr(name);
	}

PyObject* RMAObject::getattr(char *name)
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

int RMAObject::so_setattr(PyObject *op, char *name, PyObject *v)
	{
	RMAObject* bc = (RMAObject *)op;
	return bc->setattr(name,v);
	}

int RMAObject::setattr(char *name, PyObject *v)
	{
	char buf[128];
	sprintf(buf, "%s has read-only attributes", ob_type->tp_name );
	PyErr_SetString(PyExc_TypeError, buf);
	return -1;
	}

/*static*/ 
PyObject* RMAObject::so_repr(PyObject *op)
	{
	RMAObject* w = (RMAObject *)op;
#if defined(_USE_STD_STR) && (!defined(_ABIO32) || _ABIO32 == 0)
	string ret = w->repr();
	return Py_BuildValue("s",ret.c_str());
#else
	char *str = w->repr();
	PyObject *ret = Py_BuildValue("s", str);
	free(str);
	return ret;
#endif
	}

#if defined(_USE_STD_STR) && (!defined(_ABIO32) || _ABIO32 == 0)
string
#else
char *
#endif
RMAObject::repr()
	{
	char buf[50];
	sprintf(buf, "object '%s'", ob_type->tp_name);
#if defined(_USE_STD_STR) && (!defined(_ABIO32) || _ABIO32 == 0)
	return string(buf);
#else
	return strdup(buf);
#endif
	}

void RMAObject::cleanup()
	{
#if defined(_USE_STD_STR) && (!defined(_ABIO32) || _ABIO32 == 0)
	string rep = repr();
	TRACE("cleanup detected %s, refcount = %d\n",rep.c_str(),ob_refcnt);
#else
	char *rep = repr();
	TRACE("cleanup detected %s, refcount = %d\n",rep,ob_refcnt);
	free(rep);
#endif
	}

/*static*/ 
void RMAObject::so_dealloc(PyObject *obj)
	{
	delete (RMAObject*)obj;
	}

// @pymethod |PyAssocObject|GetMethodByType|Given a method name and a type object, return the attribute.
/*static*/ 
PyObject* RMAObject::GetMethodByType(PyObject *self, PyObject *args)
	{
	// @comm This function allows you to obtain attributes for base types.
	PyObject *obType;
	char *attr;
	RMAObject *pAssoc = (RMAObject *)self;
	if (pAssoc==NULL) return NULL;
	if (!PyArg_ParseTuple(args, "sO:GetAttributeByType", &attr, &obType ))
		return NULL;

	// check it is one of ours.
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

struct PyMethodDef RMAObject_methods[] = {
	{"GetMethodByType",RMAObject::GetMethodByType,1},
	{NULL,	NULL}
};

TypeObject RMAObject::type("RMAObject", 
						NULL, 
						sizeof(RMAObject), 
						RMAObject_methods, 
						NULL);


