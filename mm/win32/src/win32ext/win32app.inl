
// @pymethod int|PyCWinApp|RunLoop|Starts the message pump.  Advanced users only
static PyObject *
ui_app_run_loop(PyObject *self, PyObject *args)
{
	PyObject *obWnd = Py_None;
	if(!PyArg_ParseTuple(args,"O:RunLoop",&obWnd))
		return NULL;
	CWnd *pWnd = GetWndPtr(obWnd);
	if(!pWnd)RETURN_TYPE_ERR("The arg must be a PyCWnd object");

	GUI_BGN_SAVE;

	if (AfxGetApp()->m_pMainWnd == NULL && AfxOleGetUserCtrl())
		{
		// Not launched /Embedding or /Automation, but has no main window!
		TRACE0("Warning: m_pMainWnd is NULL in CWinApp::Run - quitting application.\n");
		AfxPostQuitMessage(0);
		}
	///////////////////
	// for tracking the idle time state
	BOOL bIdle = TRUE;
	LONG lIdleCount = 0;
	BOOL msgInQueue=FALSE;
	HANDLE ahObjects[1];
	DWORD wait_result;
	// acquire and dispatch messages until a WM_QUIT message is received.
	for (;;)
	{
		// phase1: check to see if we can do idle work
		while (bIdle &&
			!::PeekMessage(&AfxGetApp()->m_msgCur, NULL, NULL, NULL, PM_NOREMOVE))
		{

			// call OnIdle while in bIdle state
			if (!AfxGetApp()->OnIdle(lIdleCount++))
				bIdle = FALSE; // assume "no idle" state

		}

		msgInQueue=::PeekMessage(&AfxGetApp()->m_msgCur, NULL, NULL, NULL, PM_NOREMOVE);	
		if(!msgInQueue)
			{
			wait_result = ::MsgWaitForMultipleObjects(0
                                             , ahObjects
                                             , TRUE
                                             , 500
                                             , QS_ALLEVENTS 
                                             );
			if(wait_result == WAIT_TIMEOUT)
				pWnd->SendMessage(WM_USER);
			}

		// phase2: pump messages while available
		do
		{
			// pump message, but quit on WM_QUIT
			//::GetMessage(&AfxGetApp()->m_msgCur, NULL, NULL, NULL);
			msgInQueue=::PeekMessage(&AfxGetApp()->m_msgCur, NULL, NULL, NULL, PM_REMOVE);

			if(msgInQueue && AfxGetApp()->m_msgCur.message==WM_QUIT)
				{
				goto exit;
				}

			if(!msgInQueue)
				{
				bIdle = TRUE;
				lIdleCount = 0;
				break;
				}

			if (AfxGetApp()->m_msgCur.message != WM_KICKIDLE && !AfxGetApp()->PreTranslateMessage(&AfxGetApp()->m_msgCur))
				{
				::TranslateMessage(&AfxGetApp()->m_msgCur);
				::DispatchMessage(&AfxGetApp()->m_msgCur);
				}

			// reset "no idle" state after pumping "normal" message
			if (AfxGetApp()->IsIdleMessage(&AfxGetApp()->m_msgCur))
			{
				bIdle = TRUE;
				lIdleCount = 0;
			}

		} while ((msgInQueue=::PeekMessage(&AfxGetApp()->m_msgCur, NULL, NULL, NULL, PM_NOREMOVE)));
	}

exit:

	////////////////
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
