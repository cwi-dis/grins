// CMIF_ADD
//
// kk@epsilon.com.gr
//
//
// Note that this source file contains embedded documentation.
// This documentation consists of marked up text inside the
// C comments, and is prefixed with an '@' symbol.  The source
// files are processed by a tool called "autoduck" which
// generates Windows .hlp files.
// @doc


#ifndef INC_MODDEF
#define INC_MODDEF

// Template classs for creating Python objects

template <class T,class C>
class PyClass : public ui_assoc_object 
	{
	public:
	static ui_base_class *PyObConstruct() 
		{ 
		BOOL bOld = AfxEnableMemoryTracking(FALSE); 
		ui_base_class * ret = new PyClass<T,C>; 
		AfxEnableMemoryTracking(bOld);
		return ret; 
		}
	static ui_type type;
	static PyObject *Create(PyObject *self,PyObject *args)
		{return C::Create(self,args);}
	T* GetObject()
		{return (T *)GetGoodCppObject(&PyClass<T,C>::type);}

	protected:
	PyClass(){}
	~PyClass(){DoKillAssoc(TRUE);}
	virtual void DoKillAssoc(BOOL bDestructing=FALSE)
		{
		delete GetObject();
		ui_assoc_object::DoKillAssoc(bDestructing);
		}
	virtual CString repr()
		{return ui_assoc_object::repr();}
	};
 
template <class T,class C>
class PyIClass : public PyClass<T,C> 
	{
	protected:
	PyIClass(){}
	~PyIClass(){DoKillAssoc(TRUE);}
	virtual void DoKillAssoc(BOOL bDestructing=FALSE)
		{
		T* pI=GetObject();
		if(pI)pI->Release();
		ui_assoc_object::DoKillAssoc(bDestructing);
		}
	};


// Utilities to simlify hosting of modules
// in win32ui

#define DECLARE_PYMODULECLASS(module)\
\
class M##module : public ui_assoc_object\
	{public:\
	MAKE_PY_CTOR(M##module)\
	static ui_type type;\
	static PyObject *create(PyObject *self, PyObject *args);\
	\
	M##module();\
	~M##module();\
	virtual void DoKillAssoc(BOOL bDestructing = FALSE);\
	virtual CString repr();\
	\
	};\




#define IMPLEMENT_PYMODULECLASS(module,getfn,strRepr)\
\
static char M##module_sig[]=#module;\
\
M##module::M##module(){}\
M##module::~M##module()\
{M##module::DoKillAssoc(TRUE);}\
\
PyObject *\
M##module::create (PyObject *self, PyObject *args)\
	{\
	CHECK_NO_ARGS2(args,##getfn);\
	M##module *ret = (M##module *)ui_assoc_object::make(M##module::type,M##module_sig);\
	return ret;\
	}\
void M##module::DoKillAssoc( BOOL bDestructing)\
	{\
    ui_assoc_object::DoKillAssoc(bDestructing);\
	}\
\
CString M##module::repr()\
	{return ui_base_class::repr() + " " + strRepr;}\


#define DEFINE_PYMODULETYPE(pyType,module)\
	ui_type M##module::type (pyType,\
				&ui_assoc_object::type,\
				sizeof(M##module),\
				M##module_methods,\
				GET_PY_CTOR(M##module));

#define BEGIN_PYMETHODDEF(module)\
static struct PyMethodDef M##module_methods[] = {

#define END_PYMETHODDEF() {NULL, 	NULL}};


#define DEFINE_MODULEERROR(module) PYW_EXPORT PyObject *##module_error;


#define PY_INITMODULE(module)\
extern "C" __declspec(dllexport)\
void init##module()\
{\
  PyObject *dict, *modl;\
  modl = Py_InitModule(#module,M##module_methods);\
  dict = PyModule_GetDict(modl);\
  ##module_error = PyString_FromString(#module);\
  PyDict_SetItemString(dict, "error", ##module_error);\
  PyObject *copyright = PyString_FromString("Copyright 1998 Epsilon (epsilon.com.gr)");\
  PyDict_SetItemString(dict, "copyright", copyright);\
  Py_XDECREF(copyright);\
}


#include <fstream.h>
#define AfxMessageLog(str){ofstream ofs("log.txt",ios::app);if(ofs) ofs << str << endl;ofs.close();}


#endif
