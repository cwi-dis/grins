// Factory.cpp : Implementation of CFactory
#include "stdafx.h"
#include "GRiNSRenderer.h"
#include "Factory.h"

/////////////////////////////////////////////////////////////////////////////
// CFactory
STDMETHODIMP
CFactory::FindBehavior(BSTR bstrBehavior,    
                       BSTR bstrBehaviorUrl,
                       IElementBehaviorSite* pSite,
                       IElementBehavior** ppBehavior)
{
   HRESULT hr;
   CComObject<CBehavior>* pBehavior;

   // Create a Behavior object.
   hr = CComObject<CBehavior>::CreateInstance(&pBehavior);

   if (SUCCEEDED(hr))
   {
		hr = pBehavior->QueryInterface(IID_IElementBehavior, (void**)ppBehavior );
   }

   return hr;
}

