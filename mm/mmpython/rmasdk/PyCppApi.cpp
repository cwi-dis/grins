#include "std.h"
#include "PyCppApi.h"

// Cpp framework 
// for modules that export PyObjects
// for modules that need a mechanism to call back 
// methods of cpp objects overridden in Python

// For rapid-dev we borrow win32ui's core mechanisms
// we 'll revisit this module

// Using Std C++ (not MFC or other lib)

////////////////////////////////////////////////
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


struct PyMethodDef Object::empty_methods[] = {
	{NULL,	NULL}
};

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

AssocManager AssocObject::assocMgr;

/*static*/
void *AssocObject::GetGoodCppObject(PyObject *&self, TypeObject *Type_check)
	{
	// first, call is_object, which may modify the "self" pointer.
	// this is to support a Python class instance being passed in,
	// and auto-convert it to the classes AttachedObject.
	if (Type_check && !is_object(self, Type_check)) 
		{
		string csRet = "object is not a ";
		csRet += Type_check->tp_name;
		TRACE("GetGoodCppObject fails RTTI\n");
		const char *ret = csRet.c_str();
		RETURN_TYPE_ERR((char *)ret);
		}
	AssocObject *s = (AssocObject *)self;
	if (s->assoc==NULL)
		RETURN_ERR("The object has been destroyed.");
	return s->assoc;
	}

void *AssocObject::GetGoodCppObject(TypeObject *Type_check) const
	{
	// Get a checked association.
	PyObject *temp = (PyObject *)this;
	void *ret = GetGoodCppObject(temp, Type_check);
	if (this!=(AssocObject *)temp)
		TRACE("GetGoodCpp called with this->, and this needs to be changed!");
	return (AssocObject *)ret;
	}


// @pymethod |PyAssocObject|AttachObject|Attaches a Python object for lookup of "virtual" functions.
PyObject *AssocObject::AttachObject(PyObject *self,PyObject *args)
	{
	PyObject *ob;
	AssocObject *pAssoc = (AssocObject*)self;
	if (pAssoc==NULL) return NULL;
	if (!PyArg_ParseTuple(args, "O:AttachObject", &ob ))
		return NULL;
	XDODECREF(pAssoc->virtualInst);
	pAssoc->virtualInst = NULL;
	if (ob!=Py_None) 
		{
		pAssoc->virtualInst = ob;
		DOINCREF(ob);
		}
	RETURN_NONE;
	}

// @object PyAssocObject|An internal class.
static struct PyMethodDef PyAssocObject_methods[] = {
	{"AttachObject",AssocObject::AttachObject,1}, // @pymeth AttachObject|Attaches a Python object for lookup of "virtual" functions.
	{NULL, NULL}
};

TypeObject AssocObject::type("PyAssocObject", 
							  &Object::type, 
							  sizeof(AssocObject), 
							  PyAssocObject_methods, 
							  NULL);

AssocObject::AssocObject()
	{
	assoc=0;
	virtualInst=NULL;
	}
AssocObject::~AssocObject()
	{
	KillAssoc();
	}

// handle is invalid - therefore release all refs I am holding for it.
void AssocObject::KillAssoc()
	{
	#ifdef TRACE_ASSOC
	string rep = repr();
	const char *szRep = rep;
	TRACE("Destroying association with %p and %s",this,szRep);
	#endif
	// note that _any_ of these may cause this to be deleted, as the reference
	// count may drop to zero.  If any one dies, and later ones will fail.  Therefore
	// I incref first, and decref at the end.
	// Note that this _always_ recurses when this happens as the destructor also
	// calls us to cleanup.  Forcing an INCREF/DODECREF in that situation causes death
	// by recursion, as each dec back to zero causes a delete.
	BOOL bDestructing = ob_refcnt==0;
	if (!bDestructing)
		Py_INCREF(this);
	DoKillAssoc(bDestructing);	// kill all map entries, etc.
	SetAssocInvalid();			// let child do whatever to detect
	if (!bDestructing)
		DODECREF(this);
	}

// the virtual version...
void AssocObject::DoKillAssoc(BOOL bDestructing/*= FALSE*/)
	{
	GET_THREAD_AND_DECREF(virtualInst);
	virtualInst = NULL;
	assocMgr.Assoc(0,this,assoc);
	}

// return an object, given an association, if we have one.
/* static */ 
AssocObject *AssocObject::GetPyObject(void *search)
	{
	return (AssocObject *)assocMgr.GetAssocObject(search);
	}

PyObject *AssocObject::GetGoodRet()
	{
	if (this==NULL) return NULL;
	if (virtualInst) 
		{
		DODECREF(this);
		DOINCREF(virtualInst);
		return virtualInst;
		} 
	else
		return this;
	}

/*static*/ 
AssocObject *AssocObject::make(TypeObject &makeType,void *search)
	{
	ASSERT(search);
	AssocObject* ret = (AssocObject*)assocMgr.GetAssocObject(search);
	if (ret) 
		{
		if (!ret->is_object(&makeType))
			RETURN_ERR("Internal error - existing object is not of same type as requested new object");
		DOINCREF(ret);
		return ret;
		}
	ret = (AssocObject*)Object::make(makeType);	// may fail if unknown class.
	if (ret) 
		{
		// do NOT keep a reference to the Python object, or it will
		// remain forever.  The destructor must remove itself from the map.
		#ifdef TRACE_ASSOC
		TRACE_ASSOC(" Associating 0x%x with 0x%x", search, ret);
		#endif
		// if I have an existing handle, remove it.
		assocMgr.Assoc(search, ret,NULL);
		ret->assoc = search;
		}
	return ret;
	}

string AssocObject::repr()
	{
	char buf[128];
	sprintf(buf, " - assoc is %p, vf=%s", assoc, virtualInst ? "True" : "False");
	return Object::repr() + buf;
	}

////////////////////////////////////////////////

AssocManager::AssocManager()
	{
	lastLookup = NULL;
	lastObject = NULL;
	}
AssocManager::~AssocManager()
	{
	}
// This should never detect objects.
void AssocManager::cleanup(void)
	{
	m_sync.Lock();
	ObjectMap::iterator i;
	for(i=objectMap.begin();i!=objectMap.end();i++)
		(*i).second->cleanup();
	objectMap.clear();
	m_sync.Unlock();
	}
void AssocManager::Assoc(void *handle, AssocObject *object, void *oldHandle)
	{
	m_sync.Lock();
	if (oldHandle) 
		{
		// if window previously closed, this may fail when the Python object
		// destructs - but this is not a problem.
		objectMap.erase(oldHandle);
		if (oldHandle==lastLookup)
			lastLookup = 0;	// set cache invalid.
		}
	if (handle)
		objectMap.insert(ObjectPair(handle,object));
	if (handle==lastLookup)
		lastObject = object;
	m_sync.Unlock();
	}

AssocObject *AssocManager::GetAssocObject(const void *handle)
	{
	if (handle==NULL) return NULL; // no possible association for NULL!
	AssocObject *ret;
	m_sync.Lock();
	// implement a basic 1 item cache.
	if (lastLookup==handle) 
		{
		ret = lastObject;
		}
	else 
		{
		ObjectMap::const_iterator i=objectMap.find((void*)handle);
		if(i==objectMap.end())
			{
			lastLookup = NULL;
			ret=lastObject=NULL;
			}
		else
			{
			lastLookup = (*i).first;
			ret = lastObject = (*i).second;
			}
		}
	m_sync.Unlock();
	return ret;
	}

////////////////////////////////////////////////
PyObject *call_object(PyObject *themeth, PyObject *thearglst)
	{
	return PyEval_CallObject(themeth,thearglst);
	}
void print_error(void)
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


VirtualHelper::VirtualHelper(const char *iname, const void *iassoc)
	{
	handler=NULL;
	py_ob = NULL;
	retVal=NULL;
	csHandlerName = iname;
	AssocObject *py_bob = AssocObject::assocMgr.GetAssocObject( iassoc );
	if(py_bob==NULL) return;
	if (!py_bob->is_object(&AssocObject::type)) 
		{
		TRACE("VirtualHelper::VirtualHelper Error: Call object is not of required type\n");
		return;
		}
	// ok - have the python data type - now see if it has an override.
	if (py_bob->virtualInst) 
		{
		CEnterLeavePython elp;
		PyObject *t, *v, *tb;
		PyErr_Fetch(&t,&v,&tb);
		handler = PyObject_GetAttrString(py_bob->virtualInst,(char*)iname);
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
		}
	py_ob = py_bob;
	Py_INCREF(py_ob);
	//Py_XINCREF(handler);
	}
VirtualHelper::~VirtualHelper()
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
PyObject *VirtualHelper::GetHandler()
	{
	return handler;
	}
BOOL VirtualHelper::do_call(PyObject *args)
	{
	CEnterLeavePython _celp;
	XDODECREF(retVal);	// our old one.
	retVal = NULL;
	ASSERT(handler);	// caller must trap this.
	ASSERT(args);
	PyObject *result = call_object(handler,args);
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

BOOL VirtualHelper::call_args(PyObject *arglst)
	{
	if (!handler) return FALSE;
	return do_call(arglst);
	}

BOOL VirtualHelper::call()
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("()");
	return do_call(arglst);
	}

BOOL VirtualHelper::call(int val)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(i)",val);
	return do_call(arglst);
	}

BOOL VirtualHelper::call(int val1, int val2, int val3)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(iii)",val1, val2, val3);
	return do_call(arglst);
	}

BOOL VirtualHelper::call(long val)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(l)",val);
	return do_call(arglst);
	}

BOOL VirtualHelper::call(const char *val)
	{
	if (!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(z)",val);
	return do_call(arglst);
	}

BOOL VirtualHelper::call(const char *val, int ival)
	{
	if(!handler) return FALSE;
	PyObject *arglst = Py_BuildValue("(zi)",val,ival);
	return do_call(arglst);
	}

BOOL VirtualHelper::call(PyObject *ob)
	{
	if (!handler) return FALSE;
	if (!ob) ob=Py_None;
	PyObject *arglst = Py_BuildValue("(O)",ob);
	return do_call(arglst);
	}

BOOL VirtualHelper::call(PyObject *ob, PyObject *ob2)
	{
	if (!handler) return FALSE;
	if (!ob)ob=Py_None;
	if (!ob2)ob2=Py_None;
	PyObject *arglst = Py_BuildValue("(OO)",ob, ob2);
	return do_call(arglst);
	}

BOOL VirtualHelper::call(PyObject *ob, PyObject *ob2, int i)
	{
	if (!handler) return FALSE;
	if (!ob)
		ob=Py_None;
	if (!ob2)
		ob2=Py_None;
	PyObject *arglst = Py_BuildValue("(OOi)",ob, ob2, i);
	return do_call(arglst);
	}

BOOL VirtualHelper::retnone()
	{
	ASSERT(retVal);
	if (!retVal)
		return FALSE;	// failed - assume didnt work in non debug
	return (retVal==Py_None);
	}

BOOL VirtualHelper::retval( int &ret )
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

BOOL VirtualHelper::retval( long &ret )
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

BOOL VirtualHelper::retval( char *&ret )
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

BOOL VirtualHelper::retval(string &ret)
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

BOOL VirtualHelper::retval(_object* &ret)
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


