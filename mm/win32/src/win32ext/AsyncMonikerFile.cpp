/***********************************************************
Copyright 1991-1999 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/


#include "stdafx.h"
#include "AsyncMonikerFile.h"

#include "moddef.h"
#include "CallbackHelper.h"

class AsyncMonikerFile : public CAsyncMonikerFile
	{
	public:
	AsyncMonikerFile();
	virtual ~AsyncMonikerFile();
	virtual BOOL Open(LPCTSTR lpszURL, CFileException* pError = NULL)
		{return CAsyncMonikerFile::Open(lpszURL,pError);}
	void SaveAs(LPCTSTR str){m_saveAsFile=str;}

	void SetStatusListener(PyObject *obj);
	PyObject *m_pyListener;

	protected:
	virtual void OnDataAvailable(DWORD dwSize, DWORD bscfFlag);
	virtual void OnProgress(ULONG ulProgress, ULONG ulProgressMax,ULONG ulStatusCode, LPCTSTR szStatusText);
	virtual void OnStopBinding(HRESULT hresult, LPCTSTR szError);

	CString m_saveAsFile;
	DWORD m_dwReadBefore;
	};


AsyncMonikerFile::AsyncMonikerFile()
:	m_dwReadBefore(0),
	m_pyListener(NULL)
	{
	}
AsyncMonikerFile::~AsyncMonikerFile()
	{
	Py_XDECREF(m_pyListener);
	m_pyListener=NULL;
	}

void AsyncMonikerFile::SetStatusListener(PyObject *obj)
	{
	Py_XDECREF(m_pyListener);
	if(obj==Py_None)m_pyListener=NULL;
	else m_pyListener=obj;
	Py_XINCREF(m_pyListener);
	}

void AsyncMonikerFile::OnDataAvailable(DWORD dwSize, DWORD bscfFlag)
	{
	/*
   if ((bscfFlag & BSCF_FIRSTDATANOTIFICATION) != 0)
		{
		FILE *f=fopen((LPCTSTR)m_saveAsFile,"wb");
		fclose(f);
		m_dwReadBefore = 0;
		}
   if ((bscfFlag & BSCF_INTERMEDIATEDATANOTIFICATION) != 0)
		{
		}
   if ((bscfFlag & BSCF_LASTDATANOTIFICATION) != 0)
		{
		}

	DWORD dwArriving = dwSize - m_dwReadBefore;

	if (dwArriving>0)
		{
		FILE *f=fopen((LPCTSTR)m_saveAsFile,"ab");
		BYTE buff[1024];
		DWORD dwActual=0;
		do	
			{
			dwActual=Read(buff,1024);
			fwrite(buff,1,dwActual,f);
			m_dwReadBefore += dwActual;
			} while(dwActual>0);
		fclose(f);
		}
	*/
	CAsyncMonikerFile::OnDataAvailable(dwSize, bscfFlag);
	}

void AsyncMonikerFile::OnProgress(ULONG ulProgress, ULONG ulProgressMax,ULONG ulStatusCode, LPCTSTR szStatusText)
	{
	CString str;
	str.Format("%lu/%lu status=%lu %s",ulProgress,ulProgressMax,ulStatusCode,szStatusText);
	CAsyncMonikerFile::OnProgress(ulProgress, ulProgressMax, ulStatusCode, szStatusText);
	if(m_pyListener)
		{
		CallbackHelper helper("OnProgress",m_pyListener);
		if(helper.HaveHandler())helper.call(ulProgress,ulProgressMax,ulStatusCode,szStatusText);
		}
	}

void AsyncMonikerFile::OnStopBinding(HRESULT hresult, LPCTSTR szError)
	{
	CAsyncMonikerFile::OnStopBinding(hresult, szError);
	Close();
	if(m_pyListener)
		{
		CallbackHelper helper("OnDownloadComplete",m_pyListener);
		if(helper.HaveHandler())helper.call();
		}

	}

////////////////////////////////////////////
PyAsyncMonikerFile::PyAsyncMonikerFile()
:	m_pAsyncMonikerFile(NULL)
	{
	}

PyAsyncMonikerFile::~PyAsyncMonikerFile()
	{
	// Close AsyncMonikerFile if not already close
	// (it is valid to call it on a closed AsyncMonikerFile)
	m_pAsyncMonikerFile->Close();
	delete m_pAsyncMonikerFile;
	}

//static
PyObject* PyAsyncMonikerFile::Create(PyObject *self, PyObject *args)
	{
	PyObject *pyObj=CPyObject::make(PyAsyncMonikerFile::type);
	PyAsyncMonikerFile *pObj=(PyAsyncMonikerFile*)pyObj;
	pObj->m_pAsyncMonikerFile=new AsyncMonikerFile;
	return pyObj;
	}

static 
PyObject* Open(PyObject *self, PyObject *args)
	{
	char* pszURL;
	if(!PyArg_ParseTuple(args,"s",&pszURL))
		return NULL;

	PyAsyncMonikerFile *pObj=(PyAsyncMonikerFile*)self;
	GUI_BGN_SAVE;
	BOOL ret=pObj->GetAsyncMonikerFile()->Open(pszURL);
	GUI_END_SAVE;
	return Py_BuildValue("i",ret);
	}

static 
PyObject* Close(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	PyAsyncMonikerFile *pObj=(PyAsyncMonikerFile*)self;
	pObj->GetAsyncMonikerFile()->Close();
	RETURN_NONE;
	}

static 
PyObject* SaveAs(PyObject *self, PyObject *args)
	{
	char* pszFn;
	if(!PyArg_ParseTuple(args,"s",&pszFn))
		return NULL;

	PyAsyncMonikerFile *pObj=(PyAsyncMonikerFile*)self;
	pObj->GetAsyncMonikerFile()->SaveAs(pszFn);
	RETURN_NONE;
	}

static
PyObject* Abort(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	PyAsyncMonikerFile *pObj=(PyAsyncMonikerFile*)self;
	IBinding* binding=pObj->GetAsyncMonikerFile()->GetBinding();
	if(binding)binding->Abort();
	RETURN_NONE;
	}

static
PyObject* Suspend(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	PyAsyncMonikerFile *pObj=(PyAsyncMonikerFile*)self;
	IBinding* binding=pObj->GetAsyncMonikerFile()->GetBinding();
	if(binding)binding->Suspend();
	RETURN_NONE;
	}

static
PyObject* Resume(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	PyAsyncMonikerFile *pObj=(PyAsyncMonikerFile*)self;
	IBinding* binding=pObj->GetAsyncMonikerFile()->GetBinding();
	if(binding)binding->Resume();
	RETURN_NONE;
	}

static
PyObject* SetStatusListener(PyObject *self, PyObject *args)
	{
	PyObject *obj;
	if (!PyArg_ParseTuple(args,"O",&obj))
		return NULL;
	PyAsyncMonikerFile *pObj=(PyAsyncMonikerFile*)self;
	pObj->GetAsyncMonikerFile()->SetStatusListener(obj);
	RETURN_NONE;
	}

static 
struct PyMethodDef PyAsyncMonikerFile_methods[] = 
	{
	{"Open",Open,1}, 
	{"Close",Close,1}, 
	{"SaveAs",SaveAs,1}, 
	{"SetStatusListener",SetStatusListener,1}, 
	{"Suspend",Suspend,1}, 
	{"Resume",Resume,1}, 
	{"Abort",Abort,1}, 
	{NULL,NULL}		
	};

//static 
CPyTypeObject PyAsyncMonikerFile::type(
				 "PyAsyncMonikerFile",
			     PyAsyncMonikerFile::GetBaseType(),
			     sizeof(PyAsyncMonikerFile),
			     PyAsyncMonikerFile_methods,
				 PyAsyncMonikerFile::CreateInstance);
