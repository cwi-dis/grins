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

// Purpose: Enhancements to the PyCDC class needed by the Chameleon applications

// @pymethod object|PyCDC|SelectObjectFromHandle|Selects an object into the device context.<nl>
// Return Values: The handle of the previous GDI object
static PyObject *
ui_dc_select_object_from_handle(PyObject *self, PyObject *args)
{
  CDC *pDC = ui_dc_object::GetDC(self);
  if (!pDC)
	return NULL;
  HGDIOBJ h;
  // @pyparm object|ob||The object to select.
  if (!PyArg_ParseTuple (args, "i", &h))
	return NULL;
  GUI_BGN_SAVE;
  int hr=(int)::SelectObject(pDC->m_hDC,h);
  GUI_END_SAVE;
  return Py_BuildValue("i",hr);
}



// @pymethod |PyCDC|FrameRectFromHandle|Draws a border around the rectangle specified by rect
// Return Values: None
static PyObject *
ui_dc_framerect_from_handle(PyObject *self, PyObject *args)
{
	CDC *pDC = ui_dc_object::GetDC(self);
	if (!pDC)
		return NULL;
	RECT rect;
	HBRUSH hbr;
	if (!PyArg_ParseTuple (args, "(iiii)i:FrameRect", 
	          &rect.left, &rect.top, &rect.right, &rect.bottom,
			  // @pyparm (left, top, right, bottom|rect||Specifies the bounding rectangle, in logical units.
	          &hbr)) // @pyparm <HBRUSH>|brush||Specifies the brush to use.
		return NULL;
	GUI_BGN_SAVE;
	::FrameRect(pDC->m_hDC,&rect, hbr);
	GUI_END_SAVE;
	// @pyseemfc CDC|FrameRectFromHandle
	RETURN_NONE;
}

/*
// @mfcproto virtual int IntersectClipRect( LPCRECT lpRect );
// @pymethod |PyCDC|IntersectClipRect|Creates a new clipping region by forming the intersection of the current region and the rectangle specified
// Return Values: region type as integer
static PyObject *
ui_dc_intersect_clip_rect(PyObject *self, PyObject *args)
	{
	CDC *pDC = ui_dc_object::GetDC(self);
	if (!pDC) return NULL;

	RECT rect;
	if (!PyArg_ParseTuple (args, "(iiii):IntersectClipRect", 
	          &rect.left, &rect.top, &rect.right, &rect.bottom
			  // @pyparm (left, top, right, bottom|rect||Specifies the bounding rectangle, in logical units.
	          )) 
		return NULL;
	GUI_BGN_SAVE;
	int type=pDC->IntersectClipRect(&rect);
	GUI_END_SAVE;
	// @pyseemfc CDC|IntersectClipRect
	return Py_BuildValue("i",type);
	}
*/

/*
// @pymethod (int)|PyCDC|SetPolyFillMode|Sets the polygon-filling mode. 
// Return Values: The previous PolyFillMode as integer
static PyObject *
ui_dc_set_poly_fill_mode(PyObject *self, PyObject *args)
{
  CDC *pDC = ui_dc_object::GetDC(self);
  if (!pDC)
	return NULL;
  int nPolyFillMode;
  // @pyparm (x,y)|point||The new origin in device units.
  if (!PyArg_ParseTuple (args, "i",&nPolyFillMode))
	return NULL;
  GUI_BGN_SAVE;
  int pr = pDC->SetPolyFillMode(nPolyFillMode); // @pyseemfc CDC|SetPolyFillMode
  GUI_END_SAVE;
  return Py_BuildValue ("i", pr);
  // @rdesc The previous PolyFillMode.
}
*/

/*
// @pymethod |PyCDC|Polyline|Draws a Polyline.
// Return Values: None
static PyObject *ui_dc_polyline (PyObject *self, PyObject *args)
{
  PyObject * point_list;
  CDC *pDC = ui_dc_object::GetDC(self);
  if (!pDC)
	return NULL;
  if (!PyArg_ParseTuple(args,
						"O:Polyline",
						&point_list)) {
	return NULL;
  } else if (!PyList_Check(point_list)) {
	return NULL;
  } else {
	// Convert the list of point tuples into an array of POINT structs
	int num = PyList_Size (point_list);
	POINT * point_array = new POINT[num];
	for (int i=0; i < num; i++) {
	  PyObject * point_tuple = PyList_GetItem (point_list, i);
	  if (!PyTuple_Check (point_tuple) || PyTuple_Size (point_tuple) != 2) {
		PyErr_SetString (PyExc_ValueError,
						 "point list must be a list of (x,y) tuples");
		delete[] point_array;
		return NULL;
	  } else {
		long x, y;
		PyObject *px, *py;
		px = PyTuple_GetItem (point_tuple, 0);
		py = PyTuple_GetItem (point_tuple, 1);
		if ((!PyInt_Check(px)) || (!PyInt_Check(py))) {
		  PyErr_SetString (PyExc_ValueError,
						   "point list must be a list of (x,y) tuples");
		  delete[] point_array;
		  return NULL;
		} else {
		  x = PyInt_AsLong (px);
		  y = PyInt_AsLong (py);
		  point_array[i].x = x;
		  point_array[i].y = y;
		}
	  }
	}
	// we have an array of POINT structs, now we
	// can finally draw the polyline.
	GUI_BGN_SAVE;
	BOOL ret = pDC->Polyline(point_array, num);
	GUI_END_SAVE;
	delete[] point_array;
	if (!ret) {
	  RETURN_API_ERR("CDC::Polyline");
	} else {
	  RETURN_NONE;
	}
  }
}
*/

/*
// @pymethod x, y|PyCDC|OffsetWindowOrg|Modifies the coordinates of the window origin relative to the coordinates of the current window origin.
// Return Values: The previous origin as a tuple (x,y)
static PyObject *
ui_dc_offset_window_org(PyObject *self, PyObject *args)
	{
	CDC *pDC = ui_dc_object::GetDC(self);
	if (!pDC)return NULL;

	int x,y;
	// @pyparm int, int|x,y||The new origin offset.
	if (!PyArg_ParseTuple (args, "(ii)", &x, &y))
		return NULL;

	GUI_BGN_SAVE;
	CPoint old_org = pDC->OffsetWindowOrg(x, y);
    GUI_END_SAVE;
	return Py_BuildValue("(ii)", old_org.x, old_org.y);
	}
*/

/*
// @mfcproto virtual CPoint OffsetViewportOrg( int nWidth, int nHeight );
// @pymethod x, y|PyCDC|OffsetViewportOrg|Modifies the coordinates of the viewport origin relative to the coordinates of the current viewport origin
// Return Values: The previous viewport origin as a tuple (x,y)
static PyObject *
ui_dc_offset_viewport_org(PyObject *self, PyObject *args)
	{
	CDC *pDC = ui_dc_object::GetDC(self);
	if (!pDC)return NULL;

	int x,y;
	// @pyparm int, int|x,y||The new origin offset.
	if (!PyArg_ParseTuple (args, "(ii)", &x, &y))
		return NULL;

	GUI_BGN_SAVE;
	CPoint old_org = pDC->OffsetViewportOrg(x, y);
    GUI_END_SAVE;
	return Py_BuildValue("(ii)", old_org.x, old_org.y);
	}
*/

/*
// @pymethod obRgn|PyCDC|SelectClipRgn|Selects the given region as the current clipping region for the device context
// Return Values: The return value specifies the region's complexity (integer)
static PyObject *
ui_dc_select_clip_rgn(PyObject *self, PyObject *args)
	{
	CDC *pDC = ui_dc_object::GetDC(self);
	if (!pDC)return NULL;

	PyObject *objRgn = Py_None;
	if (!PyArg_ParseTuple(args,"O:SelectClipRgn",&objRgn))
		return NULL;

	CRgn *pRgn = PyCRgn::GetRgn(objRgn);
	if (!pRgn) return NULL;


	GUI_BGN_SAVE;
	int r=pDC->SelectClipRgn(pRgn);
    GUI_END_SAVE;

	return Py_BuildValue("i",r);
	}
*/

/*
// @mfcproto BOOL Rectangle( int x1, int y1, int x2, int y2 );
// @pymethod rc|PyCDC|Rectangle|Draws a rectangle using the current pen. The interior of the rectangle is filled using the current brush. 
// Return Values: None
static PyObject *
ui_dc_rectangle(PyObject *self, PyObject *args)
	{
	CDC *pDC = ui_dc_object::GetDC(self);
	if (!pDC)return NULL;
	RECT rect;
	if (!PyArg_ParseTuple(args,
						"(iiii)",
						&rect.left,&rect.top,
						&rect.right,&rect.bottom)) 
		return NULL;

	BOOL b=pDC->Rectangle(rect.left,rect.top,rect.right,rect.bottom);

	if(!b)RETURN_API_ERR("CDC::Rectangle");

	RETURN_NONE;
	}
*/

/*
// @mfcproto int DrawText( const CString& str, LPRECT lpRect, UINT nFormat );
// @pymethod s,rc,forat|PyCDC|DrawText|Formats text in the given rectangle
// Return Values: Height of text in pixels
static PyObject *
ui_dc_draw_text(PyObject *self, PyObject *args)
	{
	CDC *pDC = ui_dc_object::GetDC(self);
	if (!pDC)return NULL;

	char *psz;
	RECT rect;
	UINT nFormat=DT_SINGLELINE|DT_CENTER|DT_VCENTER;
	if (!PyArg_ParseTuple(args,
						"s(iiii)|i",&psz,
						&rect.left,&rect.top,
						&rect.right,&rect.bottom,&nFormat)) 
		return NULL;

	CString str(psz);
	int height=pDC->DrawText(str,&rect,nFormat);

	return Py_BuildValue("i",height);
	}
*/

/*
// @mfcproto BOOL StretchBlt( int x, int y, int nWidth, int nHeight, CDC* pSrcDC, int xSrc, int ySrc, int nSrcWidth, int nSrcHeight, DWORD dwRop );
// @pymethod |PyCDC|StretchBlt|Copies a bitmap from the source device context to this device context. 
static PyObject *
ui_dc_stretch_blt (PyObject *self, PyObject *args)
{
	CDC *pDC = ui_dc_object::GetDC(self);
	if (!pDC)
		return NULL;
	int x, y, width, height, xsrc, ysrc,widthsrc, heightsrc;
	DWORD rop;
	PyObject *dc_ob;
	if (!PyArg_ParseTuple (args, "(ii)(ii)O(ii)(ii)i", 
	          &x, &y,          // @pyparm (x,y)-ints|destPos||The logical x,y coordinates of the upper-left corner of the destination rectangle.
	          &width, &height, // @pyparm (width, height)-ints|size||Specifies the width and height (in logical units) of the destination rectangle and source bitmap.
	          &dc_ob,          // @pyparm <o PyCDC>|dc||Specifies the PyCDC object from which the bitmap will be copied. It must be None if rop specifies a raster operation that does not include a source.
	          &xsrc, &ysrc,    // @pyparm (xSrc, ySrc)-ints|srcPos||Specifies the logical x,y coordinates of the upper-left corner of the source bitmap.
	          &widthsrc, &heightsrc, // @pyparm (widthsrc, heightsrc)-ints|size||Specifies the width and height (in logical units) of the destination rectangle and source bitmap.
			  &rop))           // @pyparm int|rop||Specifies the raster operation to be performed. See the win32 api documentation for details.
		return NULL;
	if (!ui_base_class::is_uiobject (dc_ob, &ui_dc_object::type))
		RETURN_TYPE_ERR("The 'O' param must be a PyCDC object");
	CDC *pSrcDC = NULL;
	if (dc_ob!=Py_None) {
		pSrcDC = ui_dc_object::GetDC(dc_ob);
		if (!pSrcDC)
			RETURN_ERR("The source DC is invalid");
	}
	GUI_BGN_SAVE;
	int prevMode=pDC->SetStretchBltMode(COLORONCOLOR);
	BOOL ok = pDC->StretchBlt(x, y, width, height, pSrcDC, xsrc, ysrc,widthsrc, heightsrc, rop);
	pDC->SetStretchBltMode(prevMode);
	GUI_END_SAVE;
	if (!ok) // @pyseemfc CDC|StretchBlt
		RETURN_ERR("StretchBlt failed");
	RETURN_NONE;
}
*/

// @pymeth FrameRectFromHandle|Draws a border around the rectangle specified by rect
// @pymeth SelectObjectFromHandle|Selects an object into the DC from its handle.
// @pymeth SetPolyFillMode|Sets the polygon-filling mode.
// @pymeth Polyline|Draws a Polyline.
// @pymeth OffsetWindowOrg|Modifies the coordinates of the window origin relative to the coordinates of the current window origin.
// @pymeth SelectClipRgn|Selects the given region as the current clipping region for the device context
// @pymeth Rectangle|Draws a rectangle using the current pen. The interior of the rectangle is filled using the current brush. 
// @pymeth DrawText|Formats text in the given rectangle
#define DEF_NEW_PY_METHODS \
	{"FrameRectFromHandle", ui_dc_framerect_from_handle, 1},\
	{"SelectObjectFromHandle",	ui_dc_select_object_from_handle,1},

/*	{"SetPolyFillMode",     ui_dc_set_poly_fill_mode, 1},\
	{"Polyline",ui_dc_polyline,1},\
	{"OffsetWindowOrg",ui_dc_offset_window_org,1},\
	{"OffsetViewportOrg",ui_dc_offset_viewport_org,1},\
	{"SelectClipRgn",ui_dc_select_clip_rgn,1},\
	{"Rectangle",ui_dc_rectangle,1},\
	{"IntersectClipRect",ui_dc_intersect_clip_rect,1},\
	{"StretchBlt",ui_dc_stretch_blt,1},\
	{"DrawText",ui_dc_draw_text,1},*/


