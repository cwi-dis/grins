
// @pymethod string|PyCMenu|DestroyMenu|Destroys the menu.
PyObject *PyCMenu::DestroyMenu(PyObject *self, PyObject *args)
{
	HMENU hMenu = GetMenu( self );
	if (!hMenu) return NULL;
	::DestroyMenu(hMenu);
	RETURN_NONE;
}

// @pymethod |PyCMenu|CheckMenuItem|Adds check marks to or removes check marks from menu items in the pop-up menu
PyObject *PyCMenu::CheckMenuItem(PyObject *self, PyObject *args)
{
	HMENU hMenu = GetMenu( self );
	if (!hMenu)
		return NULL;
	int id=0;
	int flags;
	if (!PyArg_ParseTuple(args,"ii", 
	                      &id, 		 // @pyparm int|id||Specifies the menu item to be checked, as determined by flags
	                      &flags))  // @pyparm int|flags||Specifies how to check the menu item and how to determine the item’s position in the menu.
          {
            return NULL;
          }
	GUI_BGN_SAVE;
	UINT nCheck =::CheckMenuItem(hMenu,id,flags);
	GUI_END_SAVE;
	return Py_BuildValue("i",nCheck);
	}

// @pymethod |PyCMenu|GetMenuState|retrieves the menu flags associated with the specified menu item
PyObject *PyCMenu::GetMenuState(PyObject *self, PyObject *args)
{
	HMENU hMenu = GetMenu( self );
	if (!hMenu)
		return NULL;
	int id=0;
	int flags;
	if (!PyArg_ParseTuple(args,"ii", 
	                      &id, 		 // @pyparm int|id||Specifies the menu item to be checked, as determined by flags
	                      &flags))  // @pyparm int|flags||Specifies how to check the menu item and how to determine the item’s position in the menu.
          {
            return NULL;
          }
	GUI_BGN_SAVE;
	UINT nCheck =::GetMenuState(hMenu,id,flags);
	GUI_END_SAVE;
	//if(nCheck==0xFFFFFFFF)
	//	RETURN_ERR("GetMenuState: Item not found");		
	return Py_BuildValue("i",nCheck);
	}

#define DEF_NEW_PY_METHODS \
	{"DestroyMenu",(PyCFunction)PyCMenu::DestroyMenu,1},\
	{"CheckMenuItem",(PyCFunction)PyCMenu::CheckMenuItem,1},\
	{"GetMenuState",(PyCFunction)PyCMenu::GetMenuState,	1}, 