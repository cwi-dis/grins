
/*************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include "Python.h"

#include <windows.h>

#include "winuser_globals.h"

struct PyMenu
	{
	PyObject_HEAD
	HMENU m_hMenu;

	static PyTypeObject type;
	static PyMethodDef methods[];

	static PyMenu *createInstance()
		{
		PyMenu *instance = PyObject_NEW(PyMenu, &type);
		if (instance == NULL) return NULL;
		instance->m_hMenu = NULL;
		return instance;
		}

	static void dealloc(PyMenu *instance) 
		{ 
		PyMem_DEL(instance);
		}

	static PyObject *getattr(PyMenu *instance, char *name)
		{ 
		return Py_FindMethod(methods, (PyObject*)instance, name);
		}
	};

PyObject* Winuser_CreateMenu(PyObject *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	PyMenu *pymenu = PyMenu::createInstance();
	if(pymenu==NULL) return NULL;
	pymenu->m_hMenu = ::CreateMenu(); 
	return (PyObject*)pymenu;
	}

PyObject* Winuser_CreatePopupMenu(PyObject *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	PyMenu *pymenu = PyMenu::createInstance();
	if(pymenu==NULL) return NULL;
	pymenu->m_hMenu = ::CreatePopupMenu(); 
	return (PyObject*)pymenu;
	}

PyObject* Winuser_CreateMenuFromHandle(PyObject *self, PyObject *args)
{
	HMENU hMenu;
	if (!PyArg_ParseTuple(args, "i", &hMenu))
		return NULL;
	PyMenu *pymenu = PyMenu::createInstance();
	if(pymenu==NULL) return NULL;
	pymenu->m_hMenu = hMenu;
	return (PyObject*)pymenu;
}

///////////////////////////////////////////
// module

static PyObject* PyMenu_InsertMenu(PyMenu *self, PyObject *args)
{
	UINT uPosition; 
	UINT uFlags; 
	UINT uIDNewItem; 
	char *pNewItem;
	if (!PyArg_ParseTuple(args, "iiis", &uPosition, &uFlags, &uIDNewItem, &pNewItem))
		return NULL;
	BOOL res = InsertMenu(self->m_hMenu, uPosition, uFlags, uIDNewItem, pNewItem);
	if(!res){
		seterror("InsertMenu", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject* PyMenu_AppendMenu(PyMenu *self, PyObject *args)
{
	UINT uFlags; 
	UINT uIDNewItem; 
	char *pNewItem;
	if (!PyArg_ParseTuple(args, "iis", &uFlags, &uIDNewItem, &pNewItem))
		return NULL;
	BOOL res = AppendMenu(self->m_hMenu, uFlags, uIDNewItem, pNewItem);
	if(!res){
		seterror("AppendMenu", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject* PyMenu_DeleteMenu(PyMenu *self, PyObject *args)
{
	UINT uPosition; 
	UINT uFlags; 	
	if (!PyArg_ParseTuple(args,"ii",&uPosition, &uFlags))
		return NULL;
	BOOL res = DeleteMenu(self->m_hMenu, uPosition, uFlags);
	if(!res){
		seterror("DeleteMenu", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject* PyMenu_EnableMenuItem(PyMenu *self, PyObject *args)
{
	UINT uIDEnableItem; 
	UINT uEnable; 	
	if (!PyArg_ParseTuple(args,"ii",&uIDEnableItem, &uEnable))
		return NULL;
	UINT prevstate = EnableMenuItem(self->m_hMenu, uIDEnableItem, uEnable);
	return Py_BuildValue("i", prevstate);
}

static PyObject* PyMenu_GetSubMenu(PyMenu *self, PyObject *args)
{
	int nPos; 	
	if (!PyArg_ParseTuple(args,"i",&nPos))
		return NULL;
	PyMenu *pymenu = PyMenu::createInstance();
	if(pymenu==NULL) return NULL;
	pymenu->m_hMenu = GetSubMenu(self->m_hMenu, nPos);
	return (PyObject*)pymenu;
}


static PyObject* PyMenu_DestroyMenu(PyMenu *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	if(self->m_hMenu != NULL)
		{
		DestroyMenu(self->m_hMenu);
		self->m_hMenu = NULL;
		}
	return none();
}

static PyObject* PyMenu_Detach(PyMenu *self, PyObject *args)
	{
	HMENU hMenu = self->m_hMenu;
	self->m_hMenu = NULL;
	return Py_BuildValue("i", hMenu);
	}

static PyObject* PyMenu_GetHandle(PyMenu *self, PyObject *args)
	{ return Py_BuildValue("i", self->m_hMenu);}



PyMethodDef PyMenu::methods[] = {
	{"InsertMenu", (PyCFunction)PyMenu_InsertMenu, METH_VARARGS, ""},
	{"AppendMenu", (PyCFunction)PyMenu_AppendMenu, METH_VARARGS, ""},
	{"DeleteMenu", (PyCFunction)PyMenu_DeleteMenu, METH_VARARGS, ""},
	{"EnableMenuItem", (PyCFunction)PyMenu_EnableMenuItem, METH_VARARGS, ""},
	{"GetSubMenu", (PyCFunction)PyMenu_GetSubMenu, METH_VARARGS, ""},
	{"DestroyMenu", (PyCFunction)PyMenu_DestroyMenu, METH_VARARGS, ""},
	{"Detach", (PyCFunction)PyMenu_Detach, METH_VARARGS, ""},
	{"GetHandle", (PyCFunction)PyMenu_GetHandle, METH_VARARGS, ""},
	{NULL, (PyCFunction)NULL, 0, NULL}		// sentinel
};

PyTypeObject PyMenu::type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,					// ob_size
	"PyMenu",			// tp_name
	sizeof(PyMenu),		// tp_basicsize
	0,					// tp_itemsize
	
	// methods
	(destructor)PyMenu::dealloc,	// tp_dealloc
	(printfunc)0,				// tp_print
	(getattrfunc)PyMenu::getattr,// tp_getattr
	(setattrfunc)0,	// tp_setattr
	(cmpfunc)0,		// tp_compare
	(reprfunc)0,	// tp_repr
	0,				// tp_as_number
	0,				// tp_as_sequence
	0,				// tp_as_mapping
	(hashfunc)0,	// tp_hash
	(ternaryfunc)0,	// tp_call
	(reprfunc)0,	// tp_str

	// Space for future expansion
	0L,0L,0L,0L,

	"PyMenu Type" // Documentation string
	};

