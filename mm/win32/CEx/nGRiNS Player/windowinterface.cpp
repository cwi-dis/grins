
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#include "stdafx.h"
#include "resource.h"

#include "windowinterface.h"

namespace windowinterface {

messagebox::messagebox(const TCHAR *text, 
	const char *mtype, 
	v_callback_v ok, 
	v_callback_v cancel)
	: m_res(0)
	{
	CString mt(mtype);

	UINT style = MB_OK;
	if(mt == "error")
		style = style | MB_ICONERROR;
		
	else if(mt == "warning")
		style = style | MB_ICONWARNING;
	
	else if(mt == "information")
		style = style | MB_ICONINFORMATION;
	
	else if(mt == "message")
		style = style | MB_ICONINFORMATION;
		
	else if(mt == "question")
		style =  MB_OKCANCEL | MB_ICONQUESTION;

	else if(mt == "yesno")
		style = MB_YESNO | MB_ICONQUESTION;

	m_res = ::AfxMessageBox(text, style);
	if(ok!=0 && m_res == IDOK)
		(*ok)();
	else if(cancel && m_res == IDCANCEL)
		(*cancel)();
	}

} // namespace windowinterface
