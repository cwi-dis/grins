
static PyObject *
gdi_delete_object(PyObject *self, PyObject *args)
	{
	CGdiObject *pGDI=PyCGdiObject::GetGdiObject(self);
	if(pGDI->GetSafeHandle())
		pGDI->DeleteObject();	
	RETURN_NONE;
	}

#define DEF_NEW_PY_METHODS \
	{"DeleteObject",gdi_delete_object,1},
