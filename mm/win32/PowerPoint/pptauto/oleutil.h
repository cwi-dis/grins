#ifndef INC_OLEUTIL
#define INC_OLEUTIL

#ifndef _OBJBASE_H_
#include <objbase.h>
#endif

#ifndef __oaidl_h__
#include <objidl.h>
#endif

#ifndef __wtypes_h__
#include <wtypes.h>
#endif

#ifndef _INC_STRING
#include <string.h>
#endif

#include <assert.h>

namespace OleUtil
	{
	char* ToMultiByte(const wchar_t *pwch);
	wchar_t* ToWideChar(const char *pch);
	HRESULT GetClassIDFromString(OLECHAR *psz, CLSID *pclsid);

	void VariantInitToValue(VARIANT* pvar, VARTYPE vartype, va_list& argList);
	void VariantToCType(VARIANT& var, void* pvRet);

	struct DOUBLE_STRUCT  { BYTE doubleBits[sizeof(double)]; };
	struct FLOAT_STRUCT  { BYTE floatBits[sizeof(float)]; };


	class Libs
		{
		public:
		Libs() : m_hr(::OleInitialize(NULL)) {}
		~Libs(){::OleUninitialize();}
		HRESULT m_hr;
		};

	class wstring
		{
		typedef wchar_t* wchar_ptr;
		wstring(const char *pch) : pwch(ToWideChar(pch)) {}
		~wstring() {if(pwch!=NULL) delete [] pwch;}
		operator wchar_ptr() {return pwch;}
		wchar_ptr pwch;
		};
	};

inline char* OleUtil::ToMultiByte(const wchar_t *pwch)
	{
	int len = wcslen(pwch);
	char *psz = new char[len+1];
	WideCharToMultiByte(CP_ACP, 0, pwch, len+1, psz, len+1, NULL, NULL);
	psz[len]='\0';
	return psz;
	}
inline wchar_t* OleUtil::ToWideChar(const char *pch)
	{
	int len = strlen(pch);
	wchar_t *pwch = new wchar_t[len+1];
	MultiByteToWideChar(CP_ACP, 0, pch, len+1, pwch, len+1);
	return pwch;
	}

inline HRESULT OleUtil::GetClassIDFromString(OLECHAR *psz, CLSID *pclsid)
	{
	HRESULT hr;
	if (psz[0] == OLECHAR('{'))
		hr = CLSIDFromString(psz, pclsid);
	else
		hr = CLSIDFromProgID(psz, pclsid);
	return hr;
	}

inline void OleUtil::VariantInitToValue(VARIANT* pvar, VARTYPE vartype, va_list& argList)
	{
	assert(pvar != NULL);
	memset(pvar, 0, sizeof(VARIANT));
	pvar->vt = vartype;
	switch(vartype)
		{
		case VT_UI1:
			pvar->bVal = va_arg(argList, BYTE);
			break;
		case VT_I2:
			pvar->iVal = va_arg(argList, short);
			break;
		case VT_I4:
			pvar->lVal = va_arg(argList, long);
			break;
		case VT_R4:
			pvar->fltVal = (float)va_arg(argList, double);
			break;
		case VT_R8:
			pvar->dblVal = va_arg(argList, double);
			break;
		case VT_DATE:
			pvar->date = va_arg(argList, DATE);
			break;
		case VT_CY:
			pvar->cyVal = *va_arg(argList, CY*);
			break;
		case VT_BSTR:
			{
			OLECHAR* psz = va_arg(argList, OLECHAR*);
			pvar->bstrVal = SysAllocString(psz);
			assert(psz == NULL || pvar->bstrVal != NULL);
			}
			break;
		case VT_DISPATCH:
			pvar->pdispVal = va_arg(argList, LPDISPATCH);
			break;
		case VT_ERROR:
			pvar->scode = va_arg(argList, SCODE);
			break;
		case VT_BOOL:
			V_BOOL(pvar) = (VARIANT_BOOL)(va_arg(argList, BOOL) ? -1 : 0);
			break;
		case VT_VARIANT:
			*pvar = *va_arg(argList, VARIANT*);
			break;
		case VT_UNKNOWN:
			pvar->punkVal = va_arg(argList, LPUNKNOWN);
			break;
		case VT_I2|VT_BYREF:
			pvar->piVal = va_arg(argList, short*);
			break;
		case VT_UI1|VT_BYREF:
			pvar->pbVal = va_arg(argList, BYTE*);
			break;
		case VT_I4|VT_BYREF:
			pvar->plVal = va_arg(argList, long*);
			break;
		case VT_R4|VT_BYREF:
			pvar->pfltVal = va_arg(argList, float*);
			break;
		case VT_R8|VT_BYREF:
			pvar->pdblVal = va_arg(argList, double*);
			break;
		case VT_DATE|VT_BYREF:
			pvar->pdate = va_arg(argList, DATE*);
			break;
		case VT_CY|VT_BYREF:
			pvar->pcyVal = va_arg(argList, CY*);
			break;
		case VT_BSTR | VT_BYREF:
			pvar->pbstrVal = va_arg(argList, BSTR*);
			break;
		case VT_DISPATCH|VT_BYREF:
			pvar->ppdispVal = va_arg(argList, LPDISPATCH*);
			break;
		case VT_ERROR|VT_BYREF:
			pvar->pscode = va_arg(argList, SCODE*);
			break;
		case VT_BOOL|VT_BYREF:
			{
			// coerce BOOL into VARIANT_BOOL
			BOOL* pboolVal = va_arg(argList, BOOL*);
			*pboolVal = *pboolVal ? MAKELONG(-1, 0) : 0;
			pvar->pboolVal = (VARIANT_BOOL*)pboolVal;
			}
			break;
		case VT_VARIANT|VT_BYREF:
			pvar->pvarVal = va_arg(argList, VARIANT*);
			break;
		case VT_UNKNOWN|VT_BYREF:
			pvar->ppunkVal = va_arg(argList, LPUNKNOWN*);
			break;
		default:
			assert(0);  // unknown type!
			break;
		}
	}

inline void OleUtil::VariantToCType(VARIANT& var, void* pvRet)
	{
	switch (var.vt)
		{
		case VT_UI1:
			*(BYTE*)pvRet = var.bVal;
			break;
		case VT_I2:
			*(short*)pvRet = var.iVal;
			break;
		case VT_I4:
			*(long*)pvRet = var.lVal;
			break;
		case VT_R4:
			*(FLOAT_STRUCT*)pvRet = *(FLOAT_STRUCT*)&var.fltVal;
			break;
		case VT_R8:
			*(DOUBLE_STRUCT*)pvRet = *(DOUBLE_STRUCT*)&var.dblVal;
			break;
		case VT_DATE:
			*(DOUBLE_STRUCT*)pvRet = *(DOUBLE_STRUCT*)&var.date;
			break;
		case VT_CY:
			*(CY*)pvRet = var.cyVal;
			break;
		case VT_BSTR:
			//BSTR2String(pvRet, vaResult.bstrVal);
			SysFreeString(var.bstrVal);
			break;
		case VT_DISPATCH:
			*(LPDISPATCH*)pvRet = var.pdispVal;
			break;
		case VT_ERROR:
			*(SCODE*)pvRet = var.scode;
			break;
		case VT_BOOL:
			*(BOOL*)pvRet = (V_BOOL(&var) != 0);
			break;
		case VT_VARIANT:
			*(VARIANT*)pvRet = var;
			break;
		case VT_UNKNOWN:
			*(LPUNKNOWN*)pvRet = var.punkVal;
			break;
		default:
			assert(0);
		}
	}

#endif // INC_OLEUTIL

