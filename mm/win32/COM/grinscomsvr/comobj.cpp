#include "stdafx.h"

#include "comobj.h"

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
    virtual HRESULT __stdcall setWindow( 
            /* [in] */ HWND hwnd);
    virtual HRESULT __stdcall open( 
            /* [string][in] */ wchar_t __RPC_FAR *szFileOrUrl);
    virtual HRESULT __stdcall close();
    virtual HRESULT __stdcall play();
    virtual HRESULT __stdcall stop();
	virtual HRESULT __stdcall pause();
	virtual HRESULT __stdcall update();


	// Implemenation
	GRiNSPlayerAuto(ComModule *pModule);
	~GRiNSPlayerAuto();
	HWND getListener() {return *(HWND*)m_pModule->getContext();}
	private:
	long m_cRef;
	ComModule *m_pModule;
	HWND m_hWnd;
	};

HRESULT GetGRiNSPlayerAutoClassObject(IClassFactory** ppv, ComModule *pModule)
	{
	return ComCreator< ClassFactory<GRiNSPlayerAuto> >::CreateInstance(IID_IClassFactory, (void**)ppv, pModule);
	}

GRiNSPlayerAuto::GRiNSPlayerAuto(ComModule *pModule)
:	m_cRef(1), m_pModule(pModule), m_hWnd(0)
	{
	m_pModule->lock();
	}

GRiNSPlayerAuto::~GRiNSPlayerAuto()
	{
	m_pModule->unlock();
	}

HRESULT __stdcall GRiNSPlayerAuto::setWindow(/* [in] */ HWND hwnd)
	{
	PostMessage(getListener(), WM_USER_SETHWND, 0, LPARAM(hwnd));
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::open(wchar_t *wszFileOrUrl)
	{
	char *buf = new char[MAX_PATH];
    if(WideCharToMultiByte(CP_ACP, 0, wszFileOrUrl, -1, buf, MAX_PATH, NULL, NULL))
		{
		PostMessage(getListener(), WM_USER_OPEN, 0, LPARAM(buf));
		}
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::close()
	{
	PostMessage(getListener(), WM_USER_CLOSE, 0, 0);
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::play()
	{
	PostMessage(getListener(), WM_USER_PLAY, 0, 0);
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::stop()
	{
	PostMessage(getListener(), WM_USER_STOP, 0, 0);
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::pause()
	{
	PostMessage(getListener(), WM_USER_PAUSE, 0, 0);
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayerAuto::update()
	{
	PostMessage(getListener(), WM_USER_UPDATE, 0, 0);
	return S_OK;
	}