#include "stdafx.h"

#include "comobj.h"
#include "commod.h"

#include "comlib/comstl.h"
#include "comlib/comreg.h"

#include "idl/IGRiNSPlayerAuto.h"

static COMSERVER_INFO csi = 
	{
	&CLSID_GRiNSPlayerAuto, 
	"GRiNSPlayerAuto Component", 
	"GRiNSPlayerAuto", 
	"GRiNSPlayerAuto.1", 
	false
	};

bool RegisterGRiNSPlayerAutoServer()
	{
	return RegisterServer(GetModuleHandle(NULL), &csi);
	}

bool UnregisterGRiNSPlayerAutoServer()
	{
	return UnregisterServer(&csi);
	}

HRESULT CoRegisterGRiNSPlayerAutoClassObject(IClassFactory* pIFactory, LPDWORD  pdwRegister)
	{
	return CoRegisterClassObject(CLSID_GRiNSPlayerAuto, pIFactory, 
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
    virtual HRESULT __stdcall setWindow(/* [in] */ HWND hwnd);
    virtual HRESULT __stdcall open(/* [string][in] */ wchar_t __RPC_FAR *szFileOrUrl);
    virtual HRESULT __stdcall close();
    virtual HRESULT __stdcall play();
    virtual HRESULT __stdcall stop();
	virtual HRESULT __stdcall pause();
	virtual HRESULT __stdcall update();
    virtual HRESULT __stdcall getState(/* [out] */ int __RPC_FAR *pstate);
    virtual HRESULT __stdcall getSize(/* [out] */ int __RPC_FAR *pw, /* [out] */ int __RPC_FAR *ph);
    virtual HRESULT __stdcall getDuration(/* [out] */ double __RPC_FAR *pdur);
	virtual HRESULT __stdcall getTime(/* [out] */ double __RPC_FAR *pt);
    virtual HRESULT __stdcall setTime(/* [in] */ double t);
    virtual HRESULT __stdcall getSpeed(/* [out] */ double __RPC_FAR *ps);
	virtual HRESULT __stdcall setSpeed(/* [in] */ double s);
	
    virtual HRESULT __stdcall mouseClicked(/* [in] */ int x, /* [in] */ int y);
    virtual HRESULT __stdcall mouseMoved(/* [in] */ int x, /* [in] */ int y, /* [out] */ BOOL __RPC_FAR *phot);	

	// Implemenation
	GRiNSPlayerAuto(GRiNSPlayerComModule *pModule);
	~GRiNSPlayerAuto();
	HWND getListener() {return m_pModule->getListenerHwnd();}
	void adviceSetSize(int w, int h){m_width=w;m_height=h;}
	void adviceSetCursor(char *cursor){memcpy(m_cursor, cursor, strlen(cursor)+1);}
	
	private:
	long m_cRef;
	GRiNSPlayerComModule *m_pModule;

	
	HWND m_hWnd;
	int m_width, m_height;
	char m_cursor[32];
	};

HRESULT GetGRiNSPlayerAutoClassObject(IClassFactory** ppv, GRiNSPlayerComModule *pModule)
	{
	typedef ClassFactory<GRiNSPlayerAuto, GRiNSPlayerComModule> Factory;
	return ComCreator<Factory, GRiNSPlayerComModule>::CreateInstance(IID_IClassFactory, (void**)ppv, pModule);
	}

void GRiNSPlayerAutoAdviceSetSize(int id, int w, int h)
	{
	if(id!=0)
		{
		GRiNSPlayerAuto *p = (GRiNSPlayerAuto*)id;
		p->adviceSetSize(w, h);
		}
	}
void GRiNSPlayerAutoAdviceSetCursor(int id, char *cursor)
	{
	if(id!=0)
		{
		GRiNSPlayerAuto *p = (GRiNSPlayerAuto*)id;
		p->adviceSetCursor(cursor);
		}
	}

GRiNSPlayerAuto::GRiNSPlayerAuto(GRiNSPlayerComModule *pModule)
:	m_cRef(1), m_pModule(pModule), m_hWnd(0), m_width(0), m_height(0)
	{
	adviceSetCursor("arrow");
	m_pModule->lock();
	}

GRiNSPlayerAuto::~GRiNSPlayerAuto()
	{
	m_pModule->unlock();
	}

HRESULT __stdcall GRiNSPlayerAuto::setWindow(/* [in] */ HWND hwnd)
	{
	PostMessage(getListener(), WM_USER_SETHWND, WPARAM(this), LPARAM(hwnd));
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::open(wchar_t *wszFileOrUrl)
	{
	char *buf = new char[MAX_PATH];
    if(WideCharToMultiByte(CP_ACP, 0, wszFileOrUrl, -1, buf, MAX_PATH, NULL, NULL))
		{
		PostMessage(getListener(), WM_USER_OPEN, WPARAM(this), LPARAM(buf));
		}
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::close()
	{
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
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::getSize(/* [out] */ int __RPC_FAR *pw, /* [out] */ int __RPC_FAR *ph)
	{
	*pw = m_width;
	*ph = m_height;
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::getDuration(/* [out] */ double __RPC_FAR *pdur)
	{
	*pdur = -1;
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::getTime(/* [out] */ double __RPC_FAR *pt)
	{
	*pt = 0;
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::setTime(/* [in] */ double t)
	{
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::getSpeed(/* [out] */ double __RPC_FAR *ps)
	{
	*ps = 1;
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::setSpeed(/* [in] */ double s)
	{
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::mouseClicked(/* [in] */ int x, /* [in] */ int y)
	{
	PostMessage(getListener(), WM_USER_MOUSE_CLICKED, WPARAM(this), MAKELPARAM(x,y));	
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::mouseMoved(/* [in] */ int x, /* [in] */ int y, /* [out] */ BOOL __RPC_FAR *phot)
	{
	PostMessage(getListener(), WM_USER_MOUSE_MOVED, WPARAM(this), MAKELPARAM(x,y));	
	*phot=FALSE;
	if(strcmpi(m_cursor,"hand")==0)
		*phot=TRUE;
	return S_OK;
	}

            
