

// @pymethod int|PyCWinApp|RunLoop|Starts the message pump.  Advanced users only
static PyObject *
ui_app_run_loop(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args,""))
		return NULL;
	
	GUI_BGN_SAVE;

	if (AfxGetApp()->m_pMainWnd == NULL && AfxOleGetUserCtrl())
		{
		// Not launched /Embedding or /Automation, but has no main window!
		TRACE0("Warning: m_pMainWnd is NULL in CWinApp::Run - quitting application.\n");
		AfxPostQuitMessage(0);
		}
	
	// for tracking the idle time state
	BOOL bIdle = TRUE;
	LONG lIdleCount = 0;
	BOOL msgInQueue=FALSE;
	BOOL shouldExit = FALSE;
	
	// acquire and dispatch messages until a WM_QUIT message is received.
	while(!shouldExit)
		{
		// phase1: check to see if we can do idle work
		while (bIdle && !::PeekMessage(&AfxGetApp()->m_msgCur, NULL, NULL, NULL, PM_NOREMOVE))
			{
			// call OnIdle while in bIdle state
			if (!AfxGetApp()->OnIdle(lIdleCount++))
				bIdle = FALSE; // assume "no idle" state
			}
		
		// phase2: pump messages while available
		do	{
			// pump message, but quit on WM_QUIT
			if (!AfxGetApp()->PumpMessage())
				{
				shouldExit = TRUE;
				break;
				}

			// reset "no idle" state after pumping "normal" message
			if (AfxGetApp()->IsIdleMessage(&AfxGetApp()->m_msgCur))
				{
				bIdle = TRUE;
				lIdleCount = 0;
				}
			} while (::PeekMessage(&AfxGetApp()->m_msgCur, NULL, NULL, NULL, PM_NOREMOVE));

		}
	
	GUI_END_SAVE;
	RETURN_NONE;
}

// @mfcproto void CloseAllDocuments( BOOL bEndSession );
// @pymethod int|PyCWinApp|CloseAllDocuments|Close all open documents 
static PyObject *
ui_app_close_all_documents(PyObject *self, PyObject *args)
{
	BOOL  bEndSession;
	if (!PyArg_ParseTuple(args, "i",
				&bEndSession)) // @pyparm int|bEndSession||Specifies whether or not the Windows session is being ended
		return NULL;
	GUI_BGN_SAVE;
	GetApp()->CloseAllDocuments(bEndSession);
	GUI_END_SAVE;

	RETURN_NONE;
}

#define DEF_NEW_PY_METHODS \
	{"RunLoop", ui_app_run_loop, 1},\
	{"CloseAllDocuments", ui_app_close_all_documents, 1},
