#include "stdafx.h"
#include "stdcom.h"

ComModule module;


////////////////////////////// ComModule
HRESULT ComModule::init(HINSTANCE h,DWORD dwThreadID)
	{
	m_hInst= h;
	m_dwThreadID=dwThreadID;
	m_nLockCnt=0L;
	return S_OK;
	}
HRESULT ComModule::getClassObject(REFCLSID rclsid, REFIID riid, LPVOID* ppv)
{
	if (ppv == NULL)
		return E_POINTER;
	
	HRESULT hRes = S_OK;

	for(ComModule::iterator i=begin();i!=end();i++)
		{
		if(InlineIsEqualGUID(rclsid,*(*i).pclsid))
			{
			if ((*i).pClassFactory == NULL)
				{
				hRes = (*i).pfnGetClassObject((*i).pfnCreateInstance,
					IID_IUnknown, (LPVOID*)&(*i).pClassFactory);
				}
			if ((*i).pClassFactory != NULL)
				hRes = (*i).pClassFactory->QueryInterface(riid, ppv);
			break;
			}
		}
	if(*ppv == NULL && hRes == S_OK)
		hRes = CLASS_E_CLASSNOTAVAILABLE;
	return hRes;
	}

HRESULT ComModule::createClassObjects()
	{
	for(ComModule::iterator i=begin();i!=end();i++)
		{
		if ((*i).pClassFactory == NULL)
			{
			(*i).pfnGetClassObject((*i).pfnCreateInstance,
				IID_IUnknown, (LPVOID*)&(*i).pClassFactory);
			}
		}
	return S_OK;
	}

HRESULT ComModule::registerClassObjects()
	{
	for(ComModule::iterator i=begin();i!=end();i++)
		{
		if ((*i).pClassFactory == NULL)
			{
			(*i).pfnGetClassObject((*i).pfnCreateInstance,
				IID_IUnknown, (LPVOID*)&(*i).pClassFactory);
			}
		if ((*i).pClassFactory != NULL)
			{
			::CoRegisterClassObject(
		                  *(*i).pclsid,
		                  (*i).pClassFactory,
		                  CLSCTX_LOCAL_SERVER,
		                  REGCLS_MULTIPLEUSE,
		                  &(*i).dwRegister);
			}
		}
	return S_OK;
	}
HRESULT ComModule::revokeClassObjects()
	{
	for(ComModule::iterator i=begin();i!=end();i++)
		{
		if ((*i).dwRegister!=0)
			{
			::CoRevokeClassObject((*i).dwRegister);
			}
		}
	return S_OK;
	}

LONG ComModule::lock() 
	{
	return InterlockedIncrement(&m_nLockCnt);
	}

LONG ComModule::unlock() 
	{
	InterlockedDecrement(&m_nLockCnt);
	if(m_nLockCnt<=0 && m_dwThreadID!=0)
		::PostThreadMessage(m_dwThreadID,WM_QUIT,0,0);
	return m_nLockCnt;
	}

HRESULT ComModule::term()
	{
	assert(m_hInst != NULL);
	for(ComModule::iterator i=begin();i!=end();i++)
		{
		if ((*i).pClassFactory != NULL)
			(*i).pClassFactory->Release();
		(*i).pClassFactory = NULL;
		}
	return S_OK;
	}

////////////////////////////// ClassFactory
HRESULT __stdcall ClassFactory::QueryInterface(const IID& iid, void** ppv)
	{    
	if(InlineIsEqualUnknown(iid) || InlineIsEqualGUID(iid,IID_IClassFactory))
		{
		IClassFactory* p=static_cast<IClassFactory*>(this);
		p->AddRef();
		*ppv = p; 
		return S_OK;
		}
	*ppv = NULL ;
	return E_NOINTERFACE ;
	}

ULONG __stdcall ClassFactory::AddRef()
	{
	return InterlockedIncrement(&m_cRef) ;
	}

ULONG __stdcall ClassFactory::Release() 
	{
	if (InterlockedDecrement(&m_cRef) == 0)
		{
		delete this ;
		return 0 ;
		}
	return m_cRef ;
	}

HRESULT __stdcall ClassFactory::
CreateInstance(IUnknown* pUnknownOuter,const IID& iid,void** ppv) 
	{
	return m_pfnCreateInstance(pUnknownOuter,iid,ppv);
	}

HRESULT __stdcall ClassFactory::
LockServer(BOOL bLock) 
	{
	if (bLock) module.lock(); 
	else module.unlock();
	return S_OK ;
	}

/////////////////////////
void ComErrorMessage(HRESULT hr)
	{
	void* pMsgBuf;
	::FormatMessage( 
		FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
		NULL,
		hr,
		MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
		(LPTSTR)&pMsgBuf,
		0,
		NULL 
	) ;

	char buf[256] ;
	sprintf(buf, "Error (%x): %s", hr, (char*)pMsgBuf) ;
	MessageLog(buf) ;
		
	// Free the buffer.
	LocalFree(pMsgBuf) ;
	}
