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
    virtual HRESULT __stdcall getSize(/* [out] */ int __RPC_FAR *pw, /* [out] */ int __RPC_FAR *ph);

	// Implemenation
	GRiNSPlayerAuto(GRiNSPlayerComModule *pModule);
	~GRiNSPlayerAuto();
	HWND getListener() {return m_pModule->getListenerHwnd();}
	void adviceSetSize(int w, int h){m_width=w;m_height=h;}
	private:
	long m_cRef;
	GRiNSPlayerComModule *m_pModule;
	HWND m_hWnd;
	int m_width, m_height;
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
		try {p->adviceSetSize(w, h);} catch(...){}
		}
	}

GRiNSPlayerAuto::GRiNSPlayerAuto(GRiNSPlayerComModule *pModule)
:	m_cRef(1), m_pModule(pModule), m_hWnd(0), m_width(0), m_height(0)
	{
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

HRESULT __stdcall GRiNSPlayerAuto::getSize(/* [out] */ int __RPC_FAR *pw, /* [out] */ int __RPC_FAR *ph)
	{
	*pw = m_width;
	*ph = m_height;
	return S_OK;
	}
            
