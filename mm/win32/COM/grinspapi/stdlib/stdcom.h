#ifndef INC_STDCOM
#define INC_STDCOM

inline BOOL InlineIsEqualGUID(REFGUID rguid1, REFGUID rguid2)
	{
   return (
	  ((PLONG) &rguid1)[0] == ((PLONG) &rguid2)[0] &&
	  ((PLONG) &rguid1)[1] == ((PLONG) &rguid2)[1] &&
	  ((PLONG) &rguid1)[2] == ((PLONG) &rguid2)[2] &&
	  ((PLONG) &rguid1)[3] == ((PLONG) &rguid2)[3]);
	}

inline BOOL InlineIsEqualUnknown(REFGUID rguid1)
	{
   return (
	  ((PLONG) &rguid1)[0] == 0 &&
	  ((PLONG) &rguid1)[1] == 0 &&
	  ((PLONG) &rguid1)[2] == 0x000000C0 &&
	  ((PLONG) &rguid1)[3] == 0x46000000);
	}


typedef HRESULT (WINAPI COM_CREATORFUNC)(void* pv, REFIID riid, LPVOID* ppv);

template <class T>
class ComCreator
	{
	public:
	static HRESULT WINAPI CreateInstance(void* pv,REFIID riid,LPVOID* ppv)
		{
		HRESULT hRes = E_OUTOFMEMORY;
		T* p = NULL;
		p = new T;
		if (p != NULL)
			{
			p->SetVoid(pv);
			hRes = p->QueryInterface(riid,ppv);
			p->Release();
			}
		return hRes;
		}
	};

class ClassFactory : public IClassFactory
	{
	public:
	// IUnknown
	virtual HRESULT __stdcall QueryInterface(const IID& iid, void** ppv); 
	virtual ULONG __stdcall AddRef() ;
	virtual ULONG __stdcall Release() ;

	// IClassFactory
	virtual HRESULT __stdcall CreateInstance(IUnknown* pUnknownOuter,const IID& iid,void** ppv) ;
	virtual HRESULT __stdcall LockServer(BOOL bLock); 

	ClassFactory() : 
		m_cRef(1)
		{}
	~ClassFactory() 
		{}

	void SetVoid(void *pv)
		{m_pfnCreateInstance = (COM_CREATORFUNC*)pv;}

	COM_CREATORFUNC* m_pfnCreateInstance;

	private:
	long m_cRef ;
	};

struct ComInfo
	{
	const CLSID* pclsid;
	COM_CREATORFUNC* pfnGetClassObject;
	COM_CREATORFUNC* pfnCreateInstance;
	IUnknown* pClassFactory;
	DWORD dwRegister; // used for exe servers

	ComInfo(const CLSID* p0,COM_CREATORFUNC* p1=NULL,COM_CREATORFUNC* p2=NULL,IUnknown* p3=NULL)
	:	pclsid(p0),
		pfnGetClassObject(p1),
		pfnCreateInstance(p2),
		pClassFactory(p3),
		dwRegister(0)
		{}
	};

typedef list<ComInfo> ComObjList;


class ComModule : public ComObjList
	{
	public:
	HRESULT init(HINSTANCE hInst,DWORD dwThreadID=0);
	HRESULT term();

	LONG lock();
	LONG unlock();
	LONG getLockCount()const {return m_nLockCnt;}

	HINSTANCE getModuleInstance() const {return m_hInst;}
	
	HRESULT getClassObject(const CLSID& clsid,const IID& iid,void** ppv);

	// exe support
	HRESULT createClassObjects();
	HRESULT registerClassObjects();
	HRESULT revokeClassObjects();
	
	HINSTANCE m_hInst;
	DWORD m_dwThreadID;
	LONG m_nLockCnt;
	};

template <class T>
void RegisterObject(const CLSID* pclsid,ComObjList* pl)
	{
	pl->push_back(ComInfo(pclsid,&T::ClassFactoryCreatorClass::CreateInstance,
		&T::CreatorClass::CreateInstance));
	}
#define REGISTER_COM_OBJECT(x)\
RegisterObject< ComClass<##x> >(&##x::GetCLSID(),&module);

template <class Base>
class ComClass : public Base
	{
	public:
	ComClass()
	: m_cRef(1)
		{ 
		module.lock();
		}
	~ComClass()
		{
		module.unlock();
		}

	virtual HRESULT __stdcall QueryInterface(const IID& iid, void** ppv)
		{  
		*ppv = NULL;

		if(m_ilist.size()==0)
			return E_NOINTERFACE;

		if(InlineIsEqualUnknown(iid))
			return m_ilist.front().pfnICast(ppv,this);
		
		for(list<IInfo>::iterator i=m_ilist.begin();i!=m_ilist.end();i++)
			{
			if(InlineIsEqualGUID(iid,*((*i).pI)))
				return (*i).pfnICast(ppv,this);
			}
		return E_NOINTERFACE;
		}

	virtual ULONG __stdcall AddRef()
		{
		return InterlockedIncrement(&m_cRef) ;
		}

	virtual ULONG __stdcall Release() 
		{
		if(InterlockedDecrement(&m_cRef) == 0)
			{
			delete this ;
			return 0 ;
			}
		return m_cRef ;
		}

	void SetVoid(void* pv)
		{}
	typedef ComCreator<ClassFactory> ClassFactoryCreatorClass;
	typedef ComCreator< ComClass<Base> > CreatorClass;

	private:
	long m_cRef ;
	};




template <class Base,const CLSID* pclsid>
class ComInterfaceProvider
	{
	public:
	typedef HRESULT (COM_ICAST)(void** ppv,Base* pB);
	struct IInfo
		{
		const IID* pI;
		COM_ICAST* pfnICast;

		IInfo(const IID* p1=NULL,COM_ICAST* p2=NULL)
			: pI(p1),pfnICast(p2){}
		};
	list<IInfo> m_ilist;

	template <class I>
	class InterfaceCaster
		{
		public:
		static HRESULT Cast(void** ppv,Base* pB)
			{
			I *p=static_cast<I*>(pB);
			p->AddRef();
			*ppv=p;
			return S_OK;
			}
		};


	void RegisterInterface(const IID* p,COM_ICAST* pfn)
		{m_ilist.push_back(IInfo(p,(COM_ICAST*)pfn));}

	static const CLSID& GetCLSID() {return *pclsid;}
	};

#define REGISTER_COM_INTERFACE(i)\
RegisterInterface(&IID_##i,&InterfaceCaster<##i>::Cast);


extern ComModule module;

void RegisterComObjects();
LONG RegisterServer();
LONG UnregisterServer();

void ComErrorMessage(HRESULT hr);


#endif

