#include "stdafx.h"

#include "Python.h"

#include "comobj.h"
#include "commod.h"

#include "comlib/comstl.h"
#include "comlib/comreg.h"
#include "comlib/comutil.h"

#include "idl/IGRiNSPlayerAuto.h"

#include "mtpycall.h"

static COMSERVER_INFO csi = 
	{
	&CLSID_GRiNSPlayerAuto, 
	"GRiNSPlayerAuto Component", 
	"GRiNSPlayerAuto", 
	"GRiNSPlayerAuto.1", 
	false
	};

static COMSERVER_INFO csim = 
	{
	&CLSID_GRiNSPlayerMoniker, 
	"GRiNSPlayerMoniker Component", 
	"GRiNSPlayerMoniker", 
	"GRiNSPlayerMoniker.1", 
	false
	};

bool RegisterGRiNSPlayerAutoServer()
	{
	return 
		RegisterServer(GetModuleHandle(NULL), &csi) &&
		RegisterServer(GetModuleHandle(NULL), &csim);
	}

bool UnregisterGRiNSPlayerAutoServer()
	{
	return 
		UnregisterServer(&csi) &&
		UnregisterServer(&csim);
	}

HRESULT CoRegisterGRiNSPlayerAutoClassObject(IClassFactory* pIFactory, LPDWORD  pdwRegister)
	{
	return CoRegisterClassObject(CLSID_GRiNSPlayerAuto, pIFactory, 
			CLSCTX_LOCAL_SERVER, REGCLS_MULTIPLEUSE, pdwRegister);
	}

HRESULT CoRegisterGRiNSPlayerMonikerClassObject(IClassFactory* pIFactory, LPDWORD  pdwRegister)
	{
	return CoRegisterClassObject(CLSID_GRiNSPlayerMoniker, pIFactory, 
			CLSCTX_LOCAL_SERVER, REGCLS_MULTIPLEUSE, pdwRegister);
	}

#define WM_USER_OPEN WM_USER+1
#define WM_USER_CLOSE WM_USER+2
#define WM_USER_PLAY WM_USER+3
#define WM_USER_STOP WM_USER+4
#define WM_USER_PAUSE WM_USER+5
#define WM_USER_GETSTATUS WM_USER+6
#define WM_USER_SETHWND WM_USER+7
#define WM_USER_UPDATE WM_USER+8
#define WM_USER_MOUSE_CLICKED WM_USER+9
#define WM_USER_MOUSE_MOVED WM_USER+10
#define WM_USER_SETPOS WM_USER+11
#define WM_USER_SETSPEED WM_USER+12
#define WM_USER_SELWND WM_USER+13

class GRiNSPlayerAuto : public IGRiNSPlayerAuto
	{
	public:
	// IUnknown
	virtual HRESULT __stdcall QueryInterface(const IID& iid, void** ppv)
		{
		if(!ppv) return E_POINTER;
		if(IsEqualGUID(iid, IID_IUnknown))
			return InterfaceCaster<IUnknown,GRiNSPlayerAuto>::Cast(ppv,this);
		else if(IsEqualGUID(iid, IID_IGRiNSPlayerAuto))
			return InterfaceCaster<IGRiNSPlayerAuto,GRiNSPlayerAuto>::Cast(ppv,this);
		*ppv = NULL;
		return E_NOINTERFACE;
		}
	virtual ULONG __stdcall AddRef() {return InterlockedIncrement(&m_cRef);}
	virtual ULONG __stdcall Release() 
		{
		LONG res = InterlockedDecrement(&m_cRef);
		if(res == 0) delete this;
		return res;
		}
	
	// IGRiNSPlayerAuto
    virtual HRESULT __stdcall getPermission(/* [string][in] */ wchar_t __RPC_FAR *pLicense,/* [out] */ int __RPC_FAR *pPermission);
    virtual HRESULT __stdcall open(/* [string][in] */ wchar_t __RPC_FAR *szFileOrUrl);
	virtual HRESULT __stdcall close();
    virtual HRESULT __stdcall play();
    virtual HRESULT __stdcall stop();
	virtual HRESULT __stdcall pause();
	virtual HRESULT __stdcall update();
    virtual HRESULT __stdcall getState(/* [out] */ int __RPC_FAR *pstate);

    virtual HRESULT __stdcall getTopLayoutCount(/* [out] */ int __RPC_FAR *count);
    virtual HRESULT __stdcall setTopLayoutWindow(/* [in] */ int index,/* [in] */ HWND hwnd);
    virtual HRESULT __stdcall getTopLayoutDimensions(/* [in] */ int index,/* [out] */ int __RPC_FAR *pw,/* [out] */ int __RPC_FAR *ph);
    virtual HRESULT __stdcall getTopLayoutTitle(/* [in] */ int index,/* [string][out] */ wchar_t __RPC_FAR *__RPC_FAR *pszTitle);
    virtual HRESULT __stdcall getTopLayoutState(/* [in] */ int index,/* [out] */ int __RPC_FAR *pstate);
    virtual HRESULT __stdcall mouseClicked(/* [in] */ int index,/* [in] */ int x, /* [in] */ int y);
    virtual HRESULT __stdcall mouseMoved(/* [in] */ int index,/* [in] */ int x, /* [in] */ int y, /* [out] */ BOOL __RPC_FAR *phot);	
 
	virtual HRESULT __stdcall getDuration(/* [out] */ double __RPC_FAR *pdur);
	virtual HRESULT __stdcall getTime(/* [out] */ double __RPC_FAR *pt);
    virtual HRESULT __stdcall setTime(/* [in] */ double t);
    virtual HRESULT __stdcall getSpeed(/* [out] */ double __RPC_FAR *ps);
	virtual HRESULT __stdcall setSpeed(/* [in] */ double s);
    virtual HRESULT __stdcall getCookie(/* [out] */ long __RPC_FAR *cookie);
    virtual HRESULT __stdcall getFrameRate(/* [out] */ long __RPC_FAR *pfr);
    virtual HRESULT __stdcall getMediaFrameRate( 
            /* [string][in] */ wchar_t __RPC_FAR *szFileOrUrl,
            /* [out] */ long __RPC_FAR *pfr);

	// Implemenation
	GRiNSPlayerAuto(GRiNSPlayerComModule *pModule);
	~GRiNSPlayerAuto();
	HWND getListener() {return m_pModule->getListenerHwnd();}
	PyObject *getPyListener() {return m_pModule->getPyListener();}

	struct Viewport {
		Viewport(int id, int w, int h, const char *title)
			: m_id(id), m_w(w), m_h(h), m_title(NULL), m_isopen(true)
			{
			if(!title){
				m_title = new char[2];
				m_title[0]='\0';
				}
			else {
				m_title = new char[strlen(title)+1];
				strcpy(m_title, title);
				}
			}
		~Viewport(){delete[] m_title;}
		int m_id;
		int m_w, m_h;
		char *m_title;
		bool m_isopen;
		};
	void adviceNewPeerWnd(int wndid, int w, int h, const char *title)
		{
		if(m_nViewports<8) 
			m_pViewports[m_nViewports++] = new Viewport(wndid, w, h, title);
		}
	void adviceClosePeerWnd(int wndid)
		{
		for(int i=0; i<m_nViewports;i++)
			if(m_pViewports[i]->m_id == wndid) m_pViewports[i]->m_isopen = false;
		}

	void adviceSetCursor(char *cursor){memcpy(m_cursor, cursor, strlen(cursor)+1);}
	void adviceSetDur(double dur){m_dur=dur;}
	void adviceSetFrameRate(int fr){m_framerate=fr;}
	
	static CSimpleMap<int, GRiNSPlayerAuto*> s_documents;

	private:
	long m_cRef;
	GRiNSPlayerComModule *m_pModule;
	enum {STOPPED, PAUSING, PLAYING};
	
	HWND m_hWnd;

	// viewports
	int m_nViewports;
	Viewport *m_pViewports[8];
	Viewport *getViewport(int id)
		{
		for(int i=0; i<m_nViewports;i++)
			if(m_pViewports[i]->m_id == id) return m_pViewports[i];
		return NULL;
		}
	void clearViewports(){
		for(int i=0; i<m_nViewports;i++) delete m_pViewports[i];
		m_nViewports = 0;
		}
	double m_dur; // in secs
	char m_cursor[32];
	int m_focuswndid;
	int m_framerate;
	int m_permission;
	};

class GRiNSPlayerMoniker : public IGRiNSPlayerMoniker
	{
	public:
	// IUnknown
	virtual HRESULT __stdcall QueryInterface(const IID& iid, void** ppv)
		{
		if(!ppv) return E_POINTER;
		if(IsEqualGUID(iid, IID_IUnknown))
			return InterfaceCaster<IUnknown,GRiNSPlayerMoniker>::Cast(ppv,this);
		else if(IsEqualGUID(iid, IID_IGRiNSPlayerMoniker))
			return InterfaceCaster<IGRiNSPlayerMoniker,GRiNSPlayerMoniker>::Cast(ppv,this);
		*ppv = NULL;
		return E_NOINTERFACE;
		}
	virtual ULONG __stdcall AddRef() {return InterlockedIncrement(&m_cRef);}
	virtual ULONG __stdcall Release() 
		{
		LONG res = InterlockedDecrement(&m_cRef);
		if(res == 0) delete this;
		return res;
		}

	// IGRiNSPlayerMoniker
    virtual HRESULT __stdcall getGRiNSPlayerAuto( 
            /* [in] */ long cookie,
            /* [out] */ IGRiNSPlayerAuto __RPC_FAR *__RPC_FAR *pI);

	// Implemenation
	GRiNSPlayerMoniker(GRiNSPlayerComModule *pModule);
	~GRiNSPlayerMoniker();
			
	private:
	long m_cRef;
	GRiNSPlayerComModule *m_pModule;
	};

HRESULT GetGRiNSPlayerAutoClassObject(IClassFactory** ppv, GRiNSPlayerComModule *pModule)
	{
	typedef ClassFactory<GRiNSPlayerAuto, GRiNSPlayerComModule> Factory;
	return ComCreator<Factory, GRiNSPlayerComModule>::CreateInstance(IID_IClassFactory, (void**)ppv, pModule);
	}

HRESULT GetGRiNSPlayerMonikerClassObject(IClassFactory** ppv, GRiNSPlayerComModule *pModule)
	{
	typedef ClassFactory<GRiNSPlayerMoniker, GRiNSPlayerComModule> Factory;
	return ComCreator<Factory, GRiNSPlayerComModule>::CreateInstance(IID_IClassFactory, (void**)ppv, pModule);
	}

void GRiNSPlayerAutoAdviceNewPeerWnd(int docid, int wndid, int w, int h, const char *title)
	{
	GRiNSPlayerAuto *p = GRiNSPlayerAuto::s_documents.Lookup(docid);
	if(p) p->adviceNewPeerWnd(wndid, w, h, title);
	}
void GRiNSPlayerAutoAdviceClosePeerWnd(int docid, int wndid)
	{
	GRiNSPlayerAuto *p = GRiNSPlayerAuto::s_documents.Lookup(docid);
	if(p) p->adviceClosePeerWnd(wndid);
	}

void GRiNSPlayerAutoAdviceSetCursor(int docid, char *cursor)
	{
	GRiNSPlayerAuto *p = GRiNSPlayerAuto::s_documents.Lookup(docid);
	if(p) p->adviceSetCursor(cursor);
	}
void GRiNSPlayerAutoAdviceSetDur(int docid, double dur)
	{
	GRiNSPlayerAuto *p = GRiNSPlayerAuto::s_documents.Lookup(docid);
	if(p) p->adviceSetDur(dur);
	}
void GRiNSPlayerAutoAdviceSetFrameRate(int docid, int fr)
	{
	GRiNSPlayerAuto *p = GRiNSPlayerAuto::s_documents.Lookup(docid);
	if(p) p->adviceSetFrameRate(fr);
	}

// static
CSimpleMap<int, GRiNSPlayerAuto*> GRiNSPlayerAuto::s_documents;

GRiNSPlayerAuto::GRiNSPlayerAuto(GRiNSPlayerComModule *pModule)
:	m_cRef(1), m_pModule(pModule), m_hWnd(0), m_nViewports(0),
	m_dur(-2.0), m_focuswndid(0), m_framerate(20), m_permission(0)
	{
	s_documents.Add(int(this), this);
	adviceSetCursor("arrow");
	m_pModule->lock();
	}

GRiNSPlayerAuto::~GRiNSPlayerAuto()
	{
	s_documents.Remove(int(this));
	clearViewports();
	m_pModule->unlock();
	}

 HRESULT __stdcall GRiNSPlayerAuto::getPermission(/* [string][in] */ wchar_t __RPC_FAR *pLicense,/* [out] */ int __RPC_FAR *pPermission)
	{
	if(m_permission != 0) 
		{
		*pPermission = m_permission;
		return S_OK;
		}
	*pPermission = 0;
	char *buf = new char[MAX_PATH];
	if(!WideCharToMultiByte(CP_ACP, 0, pLicense, -1, buf, MAX_PATH, NULL, NULL))
		return E_UNEXPECTED;
	if(getPyListener())
		{
		CallbackHelper helper("GetPermission", getPyListener());
		if(helper.cancall())
			{
			PyObject *arg = Py_BuildValue("(s)", buf);
			int temp = 0;
			if(helper.call(arg) && helper.retval(temp))
				m_permission = temp;
			}
		}
	*pPermission = m_permission;
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::open(wchar_t *wszFileOrUrl)
	{
	if(m_permission == 0) return E_UNEXPECTED;
	char *buf = new char[MAX_PATH];
    if(WideCharToMultiByte(CP_ACP, 0, wszFileOrUrl, -1, buf, MAX_PATH, NULL, NULL))
		{
		PostMessage(getListener(), WM_USER_OPEN, WPARAM(this), LPARAM(buf));
		}
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::close()
	{
	clearViewports();
	PostMessage(getListener(), WM_USER_CLOSE, WPARAM(this), 0);
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::play()
	{
	PostMessage(getListener(), WM_USER_PLAY, WPARAM(this), 0);
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::stop()
	{
	PostMessage(getListener(), WM_USER_STOP, WPARAM(this), 0);
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::pause()
	{
	PostMessage(getListener(), WM_USER_PAUSE, WPARAM(this), 0);
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::update()
	{
	PostMessage(getListener(), WM_USER_UPDATE, WPARAM(this), 0);
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::getState(/* [out] */ int __RPC_FAR *pstate)
	{
	*pstate = 0;
	if(getPyListener())
		{
		CallbackHelper helper("GetState",getPyListener());
		if(helper.cancall())
			{
			PyObject *arg = Py_BuildValue("(i)",int(this));
			int st=0;
			if(helper.call(arg) && helper.retval(st))
				*pstate = st;
			}
		}
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::getTopLayoutCount(/* [out] */ int __RPC_FAR *count)
	{
	*count = m_nViewports;
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::setTopLayoutWindow(/* [in] */ int index,/* [in] */ HWND hwnd)
	{
	if(index >= m_nViewports) return E_UNEXPECTED;
	Viewport *p = m_pViewports[index];
	char *buf = new char[64];
	sprintf(buf, "%d %d", p->m_id, int(hwnd));
	PostMessage(getListener(), WM_USER_SETHWND, WPARAM(this), LPARAM(buf));
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::getTopLayoutDimensions(/* [in] */ int index,/* [out] */ int __RPC_FAR *pw,/* [out] */ int __RPC_FAR *ph)
	{
	if(index >= m_nViewports) return E_UNEXPECTED;
	Viewport *p = m_pViewports[index];
	*pw = p->m_w;
	*ph = p->m_h;
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::getTopLayoutTitle(/* [in] */ int index,/* [string][out] */ wchar_t __RPC_FAR *__RPC_FAR *pszTitle)
	{
	if(index >= m_nViewports || !pszTitle) return E_UNEXPECTED;
	Viewport *p = m_pViewports[index];
	WCHAR pwsz[512];
	MultiByteToWideChar(CP_ACP,0,p->m_title,-1,pwsz,512);
	const int iLength = (strlen(p->m_title)+1)*sizeof(wchar_t);
	wchar_t* pBuf = static_cast<wchar_t*>(::CoTaskMemAlloc(iLength)) ;
	if (pBuf == NULL) return E_OUTOFMEMORY;
	wcscpy(pBuf, pwsz);
	*pszTitle = pBuf;
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::getTopLayoutState(/* [in] */ int index,/* [out] */ int __RPC_FAR *pstate)
	{
	if(index >= m_nViewports) return E_UNEXPECTED;
	Viewport *p = m_pViewports[index];
	*pstate = p->m_isopen?1:0;
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::mouseClicked(/* [in] */ int index,/* [in] */ int x, /* [in] */ int y)
	{
	if(index >= m_nViewports) return E_UNEXPECTED;
	Viewport *p = m_pViewports[index];
	if(p->m_id != m_focuswndid)
		{
		SendMessage(getListener(), WM_USER_SELWND, WPARAM(this), LPARAM(p->m_id));
		m_focuswndid = p->m_id;
		}
	SendMessage(getListener(), WM_USER_MOUSE_CLICKED, WPARAM(this), MAKELPARAM(x,y));
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::mouseMoved(/* [in] */ int index,/* [in] */ int x, /* [in] */ int y, /* [out] */ BOOL __RPC_FAR *phot)
	{
	if(index >= m_nViewports) return E_UNEXPECTED;
	Viewport *p = m_pViewports[index];
	if(p->m_id != m_focuswndid)
		{
		SendMessage(getListener(), WM_USER_SELWND, WPARAM(this), LPARAM(p->m_id));
		m_focuswndid = p->m_id;
		}
	SendMessage(getListener(), WM_USER_MOUSE_MOVED, WPARAM(this), MAKELPARAM(x,y));
	*phot=FALSE;
	if(strcmpi(m_cursor,"hand")==0)
		*phot=TRUE;
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::getDuration(/* [out] */ double __RPC_FAR *pdur)
	{
	*pdur = m_dur;
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::getTime(/* [out] */ double __RPC_FAR *pt)
	{	
	*pt = 0.0;
	if(getPyListener())
		{
		CallbackHelper helper("GetPos",getPyListener());
		if(helper.cancall())
			{
			PyObject *arg = Py_BuildValue("(i)",int(this));
			int tmsec=0;
			if(helper.call(arg) && helper.retval(tmsec))
				*pt = 0.001*tmsec;
			}
		}
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::setTime(/* [in] */ double t)
	{
	PostMessage(getListener(), WM_USER_SETPOS, WPARAM(this), LPARAM(floor(1000.0*t+0.5)));	
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::getSpeed(/* [out] */ double __RPC_FAR *ps)
	{
	*ps = 1.0;
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::setSpeed(/* [in] */ double s)
	{
	PostMessage(getListener(), WM_USER_SETSPEED, WPARAM(this), LPARAM(floor(1000.0*s+0.5)));	
	return S_OK;
	}


HRESULT __stdcall GRiNSPlayerAuto::getCookie(/* [out] */ long __RPC_FAR *cookie)
	{
	*cookie = int(this);
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::getFrameRate(/* [out] */ long __RPC_FAR *pfr)
	{
	*pfr = m_framerate;
	return S_OK;
	}



HRESULT __stdcall GRiNSPlayerAuto::getMediaFrameRate(/* [string][in] */ wchar_t __RPC_FAR *wszFileOrUrl,
            /* [out] */ long __RPC_FAR *pfr) 
	{
	*pfr = 1;
	if(getPyListener())
		{
		CallbackHelper helper("GetMediaFrameRate",getPyListener());
		if(helper.cancall())
			{
			int fr = 2;
			char buf[MAX_PATH];
			WideCharToMultiByte(CP_ACP, 0, wszFileOrUrl, -1, buf, MAX_PATH, NULL, NULL);
			PyObject *arg = Py_BuildValue("(is)",int(this), buf);
			if(helper.call(arg) && helper.retval(fr)) *pfr = fr;
			}
		}
	return S_OK;
	}

////////////////////////
GRiNSPlayerMoniker::GRiNSPlayerMoniker(GRiNSPlayerComModule *pModule)
:	m_cRef(1), m_pModule(pModule)
	{
	m_pModule->lock();
	}

GRiNSPlayerMoniker::~GRiNSPlayerMoniker()
	{
	m_pModule->unlock();
	}

HRESULT __stdcall GRiNSPlayerMoniker::getGRiNSPlayerAuto( 
            /* [in] */ long cookie,
            /* [out] */ IGRiNSPlayerAuto __RPC_FAR *__RPC_FAR *pI)
	{
	// temp: use com module map
	if(cookie!=0)
		{
		GRiNSPlayerAuto *p = (GRiNSPlayerAuto*) cookie;
		return p->QueryInterface(IID_IGRiNSPlayerAuto, (void**)pI);
		}
	return E_NOINTERFACE;
	}

