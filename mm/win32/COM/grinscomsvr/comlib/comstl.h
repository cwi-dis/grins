#ifndef INC_COMSTL
#define INC_COMSTL

template <class T, class M>
class ComCreator
	{
	public:
	static HRESULT WINAPI CreateInstance(REFIID riid, void** ppv, M *pModule)
		{
		HRESULT hr = E_OUTOFMEMORY;
		T* p = NULL;
		p = new T(pModule); 
		if (p != NULL)
			{
			hr = p->QueryInterface(riid,ppv);
			p->Release();
			}
		return hr;
		}
	};

template <class I, class Base>
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

template <class T, class M>
class ClassFactory : public IClassFactory
	{
	public:
	// IUnknown
	virtual HRESULT __stdcall QueryInterface(const IID& iid, void** ppv)
		{   
		if(!ppv) return E_POINTER;
		*ppv = NULL;
		if(InlineIsEqualGUID(iid, IID_IUnknown))
			return InterfaceCaster<IUnknown,ClassFactory>::Cast(ppv,this);
		else if(InlineIsEqualGUID(iid, IID_IClassFactory))
			return InterfaceCaster<IClassFactory,ClassFactory>::Cast(ppv,this);
		return E_NOINTERFACE;
		}
	virtual ULONG __stdcall AddRef() {return InterlockedIncrement(&m_cRef);}
	virtual ULONG __stdcall Release()
		{
		LONG res = InterlockedDecrement(&m_cRef);
		if(res == 0) delete this;
		return res;
		}

	// IClassFactory
	virtual HRESULT __stdcall CreateInstance(IUnknown* pUnknownOuter,const IID& iid,void** ppv)
		{
		if(pUnknownOuter) return CLASS_E_NOAGGREGATION;
		return ComCreator<T, M>::CreateInstance(iid, ppv, m_pModule);
		}
	virtual HRESULT __stdcall LockServer(BOOL bLock)
		{
		if (bLock) m_pModule->lock(); 
		else m_pModule->unlock();
		return S_OK;
		}

	// Implementation
	ClassFactory(M *p) : m_cRef(1), m_pModule(p) { /*cout << "ClassFactory" << endl;*/}
	~ClassFactory() {/*cout << "~ClassFactory" << endl;*/}

	private:
	M *m_pModule;
	long m_cRef ;
	};


#endif