/*
 * (C) Copyright Kleanthis Kleanthous 2001.
 * Permission to copy, use, modify, sell and distribute this software
 * is granted provided this copyright notice appears in all copies.
 * This software is provided "as is" without express or implied
 * warranty, and with no claim as to its suitability for any purpose.
*/

// Based on MFC COleDispatchDriver.
// Special not MFC, not STL implememetation.

#ifndef INC_DISPATCHDRIVER
#define INC_DISPATCHDRIVER

#ifndef _OBJBASE_H_
#include <objbase.h>
#endif

#ifndef __oaidl_h__
#include <objidl.h>
#endif

#ifndef __wtypes_h__
#include <wtypes.h>
#endif

#include <assert.h>

#ifndef INC_OLEUTIL
#include "OleUtil.h"
#endif

namespace ComAuto {

class DispatchDriver
	{
	public:
	typedef IDispatch* pitype;

	DispatchDriver() : m_pi(NULL) {}

	DispatchDriver(IDispatch* p) : m_pi(p) {}

	DispatchDriver(const DispatchDriver& other)
		{
		m_pi = other.m_pi;
		if(m_pi != NULL) m_pi->AddRef();
		}

	const DispatchDriver& operator=(const DispatchDriver& other)
		{
		if(this != &other)
			{
			pitype temp = m_pi;
			m_pi = other.m_pi;
			if(m_pi != NULL) m_pi->AddRef();
			if(temp != NULL) temp->Release();
			}
		return *this;
		}
	
	const DispatchDriver& operator=(const pitype& pi)
		{
		if(this->m_pi != pi)
			{
			pitype temp = m_pi;
			m_pi = pi;
			if(temp != NULL) temp->Release();
			}
		return *this;
		}

	HRESULT create(REFCLSID clsid)
		{
		assert(m_pi == NULL);
		IUnknown* pUnknown = NULL;
		HRESULT hr = CoCreateInstance(clsid, NULL, CLSCTX_SERVER, IID_IUnknown, (void**)&pUnknown);
		if(FAILED(hr)){return hr;}
		hr = OleRun(pUnknown);
		if(FAILED(hr)){return hr;}
		hr = pUnknown->QueryInterface(IID_IDispatch, (void**)&m_pi);
		if (FAILED(hr))
			{
			pUnknown->Release();
			return hr;
			}
		pUnknown->Release();
		return S_OK;
		}

	HRESULT create(OLECHAR *pszProgID)
		{
		assert(m_pi == NULL);
		CLSID clsid;
		HRESULT hr = OleUtil::GetClassIDFromString(pszProgID, &clsid);
		if(FAILED(hr)){return hr;}
		return create(clsid);
		}

	virtual ~DispatchDriver() {release();}
	

	void attach(IDispatch* p)
		{
		release();  
		m_pi = p;
		}

	IDispatch* detach()
		{
		pitype temp = m_pi;
		m_pi = NULL;  
		return temp;
		}
	
	bool is_attached() const {return m_pi != NULL;}

	void release() 
		{
		if(m_pi != NULL) 
			{
			m_pi->Release(); 
			m_pi = NULL;
			}
		}

	HRESULT toID(OLECHAR *name, DISPID *pdispid)
		{return m_pi->GetIDsOfNames(IID_NULL, &name, 1, LOCALE_USER_DEFAULT, pdispid);}

	HRESULT invoke(OLECHAR *method);
	HRESULT __cdecl invoke(OLECHAR *member, WORD memberType, 
		VARTYPE vtRet, void* pvRet, const VARTYPE *inParamsInfo, ...);

	HRESULT getInterface(OLECHAR *property, DispatchDriver *pDD);
	HRESULT __cdecl getInterface(OLECHAR *property, DispatchDriver *pDD, VARTYPE vartype, ...);

	HRESULT getNumericValue(OLECHAR *property, int *pval);

	HRESULT __cdecl set(OLECHAR *property, VARTYPE vartype, ...);

	private:
	pitype m_pi;
	HRESULT invokeArgList(DISPID dwDispID, WORD memberType, VARTYPE vtRet, void* pvRet, 
		const VARTYPE *inParamsInfo, va_list& argList);
	};


inline HRESULT DispatchDriver::invoke(OLECHAR *method)
	{
	DISPID dispid;
	HRESULT hr = toID(method, &dispid);
	if(FAILED(hr)) return hr;
    DISPPARAMS dp = {NULL, NULL, 0, 0};
	return m_pi->Invoke(dispid, IID_NULL, LOCALE_USER_DEFAULT, 
		DISPATCH_METHOD, &dp, NULL, NULL, NULL);
	}

inline HRESULT __cdecl DispatchDriver::invoke(OLECHAR *member, WORD memberType, VARTYPE vtRet, void* pvRet, const VARTYPE *inParamsInfo, ...)
	{
	DISPID dispid;
	HRESULT hr = toID(member, &dispid);
	if(FAILED(hr)) return hr;
	va_list argList;
	va_start(argList, inParamsInfo);
	hr = invokeArgList(dispid, memberType, vtRet, pvRet, inParamsInfo, argList);
	va_end(argList);
	return hr;
	}

inline HRESULT __cdecl DispatchDriver::set(OLECHAR *property, VARTYPE vartype, ...)
	{
	DISPID dispid;
	HRESULT hr = toID(property, &dispid);
	if(FAILED(hr)) return hr;
	va_list argList;  
	va_start(argList, vartype);
	VARIANT arg;
	OleUtil::VariantInitToValue(&arg, vartype, argList);
	va_end(argList);
	DISPID dispidNamed = DISPID_PROPERTYPUT;
    DISPPARAMS dp = {&arg, &dispidNamed, 1, 1};
	hr = m_pi->Invoke(dispid, IID_NULL, LOCALE_USER_DEFAULT, 
		DISPATCH_PROPERTYPUT, &dp, NULL, NULL, NULL);
	if(vartype == VT_BSTR) VariantClear(&arg);
	return hr;
	}

inline HRESULT DispatchDriver::getInterface(OLECHAR *property, DispatchDriver *pDD)
	{
	DISPID dispid;
	HRESULT hr = toID(property, &dispid);
	if(FAILED(hr)) return hr;
    DISPPARAMS dp = {NULL, NULL, 0, 0};
	VARIANT vResult;
	memset(&vResult, 0, sizeof(VARIANT));
	hr = m_pi->Invoke(dispid, IID_NULL, LOCALE_USER_DEFAULT, 
		DISPATCH_PROPERTYGET, &dp, &vResult, NULL, NULL);
	if(FAILED(hr)){return hr;}
	pDD->m_pi = vResult.pdispVal;
    return S_OK;
	}

inline HRESULT __cdecl DispatchDriver::getInterface(OLECHAR *property, DispatchDriver *pDD, VARTYPE vartype, ...)
	{
	DISPID dispid;
	HRESULT hr = toID(property, &dispid);
	if(FAILED(hr)) return hr;
	va_list argList;  
	va_start(argList, vartype);
	VARIANT arg;
	OleUtil::VariantInitToValue(&arg, vartype, argList);
	va_end(argList);
    DISPPARAMS dp = {&arg, NULL, 1, 0};
	VARIANT vResult;
	memset(&vResult, 0, sizeof(VARIANT));
	hr = m_pi->Invoke(dispid, IID_NULL, LOCALE_USER_DEFAULT, 
		DISPATCH_METHOD, &dp, &vResult, NULL, NULL);
	if(vartype == VT_BSTR) VariantClear(&arg);
	if(FAILED(hr)){return hr;}
	pDD->m_pi = vResult.pdispVal;
    return S_OK;
	}

inline HRESULT DispatchDriver::getNumericValue(OLECHAR *property, int *pval)
	{
	DISPID dispid;
	HRESULT hr = toID(property, &dispid);
	if(FAILED(hr)) return hr;

    DISPPARAMS dp = {NULL, NULL, 0, 0};
	VARIANT vResult;
	memset(&vResult, 0, sizeof(VARIANT));
	hr = m_pi->Invoke(dispid, IID_NULL, LOCALE_USER_DEFAULT, 
		DISPATCH_PROPERTYGET, &dp, &vResult, NULL, NULL);
	if(FAILED(hr)){return hr;}
	if(vResult.vt != VT_I4)
		{
		hr = VariantChangeType(&vResult, &vResult, 0, VT_I4);
		if(FAILED(hr)){return hr;}
		}
    *pval = vResult.lVal;
	return S_OK;
	}

inline HRESULT DispatchDriver::invokeArgList(DISPID dwDispID, WORD memberType, VARTYPE vtRet, void* pvRet, 
		const VARTYPE *inParamsInfo, va_list& argList)
	{
	if(m_pi == NULL) return E_UNEXPECTED;

	DISPPARAMS dispparams = {NULL, NULL, 0, 0};

	const VARTYPE *pvt = inParamsInfo;
	while(*pvt++) dispparams.cArgs++;

	DISPID dispidNamed = DISPID_PROPERTYPUT;
	if (memberType & (DISPATCH_PROPERTYPUT | DISPATCH_PROPERTYPUTREF))
		{
		assert(dispparams.cArgs > 0);
		dispparams.cNamedArgs = 1;
		dispparams.rgdispidNamedArgs = &dispidNamed;
		}

	if(dispparams.cArgs>0)
		dispparams.rgvarg = new VARIANT[dispparams.cArgs];

	if (dispparams.cArgs > 0)
		{
		int n = dispparams.cArgs - 1;
		pvt = inParamsInfo;
		while(n>=0)
			{
			VARIANT& var = *(dispparams.rgvarg+n);
			OleUtil::VariantInitToValue(&var, *pvt, argList);
			n--;pvt++;
			}
		}

	VARIANT* pvarResult = NULL;
	VARIANT vaResult;
	memset(&vaResult, 0, sizeof(VARIANT));
	if(vtRet != VT_EMPTY)
		pvarResult = &vaResult;
	
	HRESULT hr = m_pi->Invoke(dwDispID, IID_NULL, LOCALE_USER_DEFAULT, 
		memberType, &dispparams, pvarResult, NULL, NULL);

	if (dispparams.cArgs > 0)
		{
		int n = dispparams.cArgs - 1;
		pvt = inParamsInfo;
		while(n>=0)
			{
			if(*pvt == VT_BSTR)
				::VariantClear(dispparams.rgvarg+n);
			n--;pvt++;
			}
		}
	if(dispparams.cArgs>0)
		delete[] dispparams.rgvarg;
	if(FAILED(hr)) return hr;

	if (vtRet != VT_EMPTY)
		{
		if(vtRet != VT_VARIANT)
			{
			hr = ::VariantChangeType(&vaResult, &vaResult, 0, vtRet);
			if(FAILED(hr)) return hr;
			}
		OleUtil::VariantToCType(vaResult, pvRet);
		}
	return S_OK;
	}

} // namespace ComAuto

#endif // INC_DISPATCHDRIVER
