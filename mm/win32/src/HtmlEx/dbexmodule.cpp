
#include "dbex.h"
#include "gridctrl.h"
#include "DbWnd.h"


static PyObject *DbExError;

#define IDC_GRIDCTRL 110
char cmifClass[100]="";


PyIMPORT CWnd *GetWndPtr(PyObject *);


int table[MAX_ROWS][MAX_COLS];   //global table holding all values in grid

#ifdef __cplusplus
extern "C" {
#endif


static PyObject* py_Grid_Create(PyObject *self, PyObject *Wnd)
{
	PyObject *Ob = Py_None;
	CDbWnd *Db; 
	CRect rc;
	int rows, cols;

	AfxEnableControlContainer();

	if(!PyArg_ParseTuple(Wnd, "Oii", &Ob, &rows, &cols))
	{
		Py_INCREF(Py_None);
		AfxMessageBox("cannot parse arguments", MB_OK);
		return Py_None;return NULL;
	}    
	
	Db = (CDbWnd*) GetWndPtr(Ob);

	GetClientRect(Db->m_hWnd, &rc);
	
	//create the Grid control
	BOOL bRet = Db->m_grid.Create(NULL, WS_VISIBLE|WS_BORDER,
						rc, Db, IDC_GRIDCTRL);

	AfxOleLockControl(Db->m_grid.GetClsid());


	Db->m_rows = rows;
	Db->m_cols = cols;


	Db->m_grid.SetRows(rows);
	Db->m_grid.SetCols(cols);

	Db->m_bgrid = TRUE;

	
	return Py_BuildValue("i", bRet);
		
}
	

static PyObject* py_Grid_DisplayInt(PyObject *self, PyObject *args)
{
		
	PyObject *Ob = Py_None;
	CDbWnd *Db; 
	CString str;
	int i, j, data;
	
	if(!PyArg_ParseTuple(args, "Oiii", &Ob, &i, &j, &data))
	{
		Py_INCREF(Py_None);
		AfxMessageBox("Cannot parse arguments!");
		return Py_None;return NULL;
	}
	
	Db = (CDbWnd*) GetWndPtr(Ob);

	
	if (i<MAX_ROWS && j<MAX_COLS)
	{

		Db->m_grid.SetRow(i);
		Db->m_grid.SetCol(j);

		str.Format("%d", data);
		Db->m_grid.SetText(str);

		Db->m_table[i][j] = data;
		Db->m_btable[i][j] = INT_NUM;
	}

	else
	{
		str.Format("Only %d rows and %d columns exist", MAX_ROWS, MAX_COLS);
		AfxMessageBox(str, MB_OK);
		return Py_BuildValue("i", 0);
	}


	

	return Py_BuildValue("i", 1);

}



static PyObject* py_Grid_DisplayStr(PyObject *self, PyObject *args)
{
		
	PyObject *Ob = Py_None;
	CDbWnd *Db; 
	CString str;
	int i, j;
	char *data;
	
	if(!PyArg_ParseTuple(args, "Oiis", &Ob, &i, &j, &data))
	{
		Py_INCREF(Py_None);
		AfxMessageBox("Cannot parse arguments!");
		return Py_None;return NULL;
	}
	
	Db = (CDbWnd*) GetWndPtr(Ob);

	
	if (i<MAX_ROWS && j<MAX_COLS)
	{

		Db->m_grid.SetRow(i);
		Db->m_grid.SetCol(j);

		str.Format("%s", data);
		Db->m_grid.SetText(str);

		strcpy(Db->m_strtable[i][j], data);  //store value
		Db->m_btable[i][j] = TEXT;
	}

	else
	{
		str.Format("Only %d rows and %d columns exist", MAX_ROWS, MAX_COLS);
		AfxMessageBox(str, MB_OK);
		return Py_BuildValue("i", 0);
	}


	

	return Py_BuildValue("i", 1);

}



static PyObject* py_CreateWindow(PyObject *self, PyObject *args)
{
	char *wndName;
	PyObject *testOb = Py_None;
	CWnd  *mainWnd;
	CDbWnd *newWnd;
	PyCWnd *testWnd;
	int left, top, right, bottom;
	
	newWnd = new CDbWnd;

	if(!PyArg_ParseTuple(args, "siiii", &wndName, &top, &left, &right, &bottom))
	{
		Py_INCREF(Py_None);
		return Py_None;return NULL;
	}

	TRACE("Before getting mainWnd\n");
	mainWnd = AfxGetMainWnd();
		
	TRACE("Window Handle %X\n", mainWnd->m_hWnd);
	
	if(cmifClass[0]==0)
	strcpy(cmifClass, AfxRegisterWndClass(CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS, LoadCursor (NULL, IDC_ARROW), (HBRUSH) GetStockObject (WHITE_BRUSH)));

	TRACE("Cmifclass is %s", cmifClass);
		
	if(newWnd->CreateEx(WS_EX_CLIENTEDGE,
						/*AfxRegisterWndClass(CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS),*/
						cmifClass,
						wndName,
						WS_OVERLAPPEDWINDOW|WS_VISIBLE, 
						left, top, right, bottom,
						mainWnd->m_hWnd,
						NULL))
		TRACE("CmifEx CreateWindow OK!\n");
	else
	{
		TRACE("CmifEx CreateWindow FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	testOb = testWnd->GetGoodRet();

	return Py_BuildValue("O", testOb);
}


static PyObject* py_CreateChildWindow(PyObject *self, PyObject *args)
{
	PyObject *testOb = Py_None, *ob = Py_None;
	CWnd *newWnd, *parentWnd;
	PyCWnd *testWnd;
	int left, top, right, bottom;
	char *title;
		
	if(!PyArg_ParseTuple(args, "sOiiii", &title, &ob, &left, &top, &right, &bottom))
	{
		Py_INCREF(Py_None);
		return Py_None;return NULL;
	}

	newWnd = new CDbWnd;
	parentWnd = GetWndPtr(ob);

	if(newWnd->CreateEx(WS_EX_CONTROLPARENT|WS_EX_CLIENTEDGE,
						AfxRegisterWndClass(CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS),
						title,
						WS_CHILD | WS_VISIBLE,
						left, top, right, bottom,
						parentWnd->m_hWnd,
						NULL))
		TRACE("CmifEx CreateChildWindow OK!\n");
	else
	{
		TRACE("CmifEx CreateChildWindow FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	testWnd = testWnd->make(testWnd->type,(CWnd*)(newWnd));
	testOb = testWnd->GetGoodRet();

	return Py_BuildValue("O", testOb);
}






static PyMethodDef DbExMethods[] = 
{
	{ "CreateSheet", py_Grid_Create, 1},
	{ "DisplayInt", py_Grid_DisplayInt, 1},
	{ "DisplayStr", py_Grid_DisplayStr, 1},
	{ "CreateWindow", py_CreateWindow, 1},
	{ "CreateChildWindow", py_CreateChildWindow, 1},
	{ NULL, NULL }
};


PyEXPORT 
void initdbex()
{
	PyObject *m, *d;
	m = Py_InitModule("dbex", DbExMethods);
	d = PyModule_GetDict(m);
	DbExError = PyString_FromString("dbex.error");
	PyDict_SetItemString(d, "error", DbExError);

	for (UINT k=0; k<MAX_ROWS; k++){
		for (UINT l=0; l<MAX_COLS; l++)
				table[k][l] = 0;
	}
}




#ifdef __cplusplus
}
#endif




















