/* this ALWAYS GENERATED file contains the definitions for the interfaces */


/* File created by MIDL compiler version 5.01.0164 */
/* at Fri Oct 06 12:40:01 2000
 */
/* Compiler settings for D:\ufs\mm\cmif\win32\COM\GRiNSPE\GRiNSPE.idl:
    Oicf (OptLev=i2), W1, Zp8, env=Win32, ms_ext, c_ext
    error checks: allocation ref bounds_check enum stub_data 
*/
//@@MIDL_FILE_HEADING(  )


/* verify that the <rpcndr.h> version is high enough to compile this file*/
#ifndef __REQUIRED_RPCNDR_H_VERSION__
#define __REQUIRED_RPCNDR_H_VERSION__ 440
#endif

#include "rpc.h"
#include "rpcndr.h"

#ifndef __RPCNDR_H_VERSION__
#error this stub requires an updated version of <rpcndr.h>
#endif // __RPCNDR_H_VERSION__

#ifndef COM_NO_WINDOWS_H
#include "windows.h"
#include "ole2.h"
#endif /*COM_NO_WINDOWS_H*/

#ifndef __GRiNSPE_h__
#define __GRiNSPE_h__

#ifdef __cplusplus
extern "C"{
#endif 

/* Forward Declarations */ 

#ifndef __IGRiNSPlayer_FWD_DEFINED__
#define __IGRiNSPlayer_FWD_DEFINED__
typedef interface IGRiNSPlayer IGRiNSPlayer;
#endif 	/* __IGRiNSPlayer_FWD_DEFINED__ */


#ifndef __GRiNSPlayer_FWD_DEFINED__
#define __GRiNSPlayer_FWD_DEFINED__

#ifdef __cplusplus
typedef class GRiNSPlayer GRiNSPlayer;
#else
typedef struct GRiNSPlayer GRiNSPlayer;
#endif /* __cplusplus */

#endif 	/* __GRiNSPlayer_FWD_DEFINED__ */


/* header files for imported files */
#include "oaidl.h"
#include "ocidl.h"

void __RPC_FAR * __RPC_USER MIDL_user_allocate(size_t);
void __RPC_USER MIDL_user_free( void __RPC_FAR * ); 

#ifndef __IGRiNSPlayer_INTERFACE_DEFINED__
#define __IGRiNSPlayer_INTERFACE_DEFINED__

/* interface IGRiNSPlayer */
/* [unique][helpstring][dual][uuid][object] */ 


EXTERN_C const IID IID_IGRiNSPlayer;

#if defined(__cplusplus) && !defined(CINTERFACE)
    
    MIDL_INTERFACE("DCAB2A67-BF5F-45B4-A006-B810653C9586")
    IGRiNSPlayer : public IDispatch
    {
    public:
        virtual /* [helpstring][id] */ HRESULT STDMETHODCALLTYPE Open( 
            /* [in] */ BSTR fileOrUrl) = 0;
        
        virtual /* [helpstring][id] */ HRESULT STDMETHODCALLTYPE Play( void) = 0;
        
        virtual /* [helpstring][id] */ HRESULT STDMETHODCALLTYPE Stop( void) = 0;
        
        virtual /* [helpstring][id] */ HRESULT STDMETHODCALLTYPE Pause( void) = 0;
        
    };
    
#else 	/* C style interface */

    typedef struct IGRiNSPlayerVtbl
    {
        BEGIN_INTERFACE
        
        HRESULT ( STDMETHODCALLTYPE __RPC_FAR *QueryInterface )( 
            IGRiNSPlayer __RPC_FAR * This,
            /* [in] */ REFIID riid,
            /* [iid_is][out] */ void __RPC_FAR *__RPC_FAR *ppvObject);
        
        ULONG ( STDMETHODCALLTYPE __RPC_FAR *AddRef )( 
            IGRiNSPlayer __RPC_FAR * This);
        
        ULONG ( STDMETHODCALLTYPE __RPC_FAR *Release )( 
            IGRiNSPlayer __RPC_FAR * This);
        
        HRESULT ( STDMETHODCALLTYPE __RPC_FAR *GetTypeInfoCount )( 
            IGRiNSPlayer __RPC_FAR * This,
            /* [out] */ UINT __RPC_FAR *pctinfo);
        
        HRESULT ( STDMETHODCALLTYPE __RPC_FAR *GetTypeInfo )( 
            IGRiNSPlayer __RPC_FAR * This,
            /* [in] */ UINT iTInfo,
            /* [in] */ LCID lcid,
            /* [out] */ ITypeInfo __RPC_FAR *__RPC_FAR *ppTInfo);
        
        HRESULT ( STDMETHODCALLTYPE __RPC_FAR *GetIDsOfNames )( 
            IGRiNSPlayer __RPC_FAR * This,
            /* [in] */ REFIID riid,
            /* [size_is][in] */ LPOLESTR __RPC_FAR *rgszNames,
            /* [in] */ UINT cNames,
            /* [in] */ LCID lcid,
            /* [size_is][out] */ DISPID __RPC_FAR *rgDispId);
        
        /* [local] */ HRESULT ( STDMETHODCALLTYPE __RPC_FAR *Invoke )( 
            IGRiNSPlayer __RPC_FAR * This,
            /* [in] */ DISPID dispIdMember,
            /* [in] */ REFIID riid,
            /* [in] */ LCID lcid,
            /* [in] */ WORD wFlags,
            /* [out][in] */ DISPPARAMS __RPC_FAR *pDispParams,
            /* [out] */ VARIANT __RPC_FAR *pVarResult,
            /* [out] */ EXCEPINFO __RPC_FAR *pExcepInfo,
            /* [out] */ UINT __RPC_FAR *puArgErr);
        
        /* [helpstring][id] */ HRESULT ( STDMETHODCALLTYPE __RPC_FAR *Open )( 
            IGRiNSPlayer __RPC_FAR * This,
            /* [in] */ BSTR fileOrUrl);
        
        /* [helpstring][id] */ HRESULT ( STDMETHODCALLTYPE __RPC_FAR *Play )( 
            IGRiNSPlayer __RPC_FAR * This);
        
        /* [helpstring][id] */ HRESULT ( STDMETHODCALLTYPE __RPC_FAR *Stop )( 
            IGRiNSPlayer __RPC_FAR * This);
        
        /* [helpstring][id] */ HRESULT ( STDMETHODCALLTYPE __RPC_FAR *Pause )( 
            IGRiNSPlayer __RPC_FAR * This);
        
        END_INTERFACE
    } IGRiNSPlayerVtbl;

    interface IGRiNSPlayer
    {
        CONST_VTBL struct IGRiNSPlayerVtbl __RPC_FAR *lpVtbl;
    };

    

#ifdef COBJMACROS


#define IGRiNSPlayer_QueryInterface(This,riid,ppvObject)	\
    (This)->lpVtbl -> QueryInterface(This,riid,ppvObject)

#define IGRiNSPlayer_AddRef(This)	\
    (This)->lpVtbl -> AddRef(This)

#define IGRiNSPlayer_Release(This)	\
    (This)->lpVtbl -> Release(This)


#define IGRiNSPlayer_GetTypeInfoCount(This,pctinfo)	\
    (This)->lpVtbl -> GetTypeInfoCount(This,pctinfo)

#define IGRiNSPlayer_GetTypeInfo(This,iTInfo,lcid,ppTInfo)	\
    (This)->lpVtbl -> GetTypeInfo(This,iTInfo,lcid,ppTInfo)

#define IGRiNSPlayer_GetIDsOfNames(This,riid,rgszNames,cNames,lcid,rgDispId)	\
    (This)->lpVtbl -> GetIDsOfNames(This,riid,rgszNames,cNames,lcid,rgDispId)

#define IGRiNSPlayer_Invoke(This,dispIdMember,riid,lcid,wFlags,pDispParams,pVarResult,pExcepInfo,puArgErr)	\
    (This)->lpVtbl -> Invoke(This,dispIdMember,riid,lcid,wFlags,pDispParams,pVarResult,pExcepInfo,puArgErr)


#define IGRiNSPlayer_Open(This,fileOrUrl)	\
    (This)->lpVtbl -> Open(This,fileOrUrl)

#define IGRiNSPlayer_Play(This)	\
    (This)->lpVtbl -> Play(This)

#define IGRiNSPlayer_Stop(This)	\
    (This)->lpVtbl -> Stop(This)

#define IGRiNSPlayer_Pause(This)	\
    (This)->lpVtbl -> Pause(This)

#endif /* COBJMACROS */


#endif 	/* C style interface */



/* [helpstring][id] */ HRESULT STDMETHODCALLTYPE IGRiNSPlayer_Open_Proxy( 
    IGRiNSPlayer __RPC_FAR * This,
    /* [in] */ BSTR fileOrUrl);


void __RPC_STUB IGRiNSPlayer_Open_Stub(
    IRpcStubBuffer *This,
    IRpcChannelBuffer *_pRpcChannelBuffer,
    PRPC_MESSAGE _pRpcMessage,
    DWORD *_pdwStubPhase);


/* [helpstring][id] */ HRESULT STDMETHODCALLTYPE IGRiNSPlayer_Play_Proxy( 
    IGRiNSPlayer __RPC_FAR * This);


void __RPC_STUB IGRiNSPlayer_Play_Stub(
    IRpcStubBuffer *This,
    IRpcChannelBuffer *_pRpcChannelBuffer,
    PRPC_MESSAGE _pRpcMessage,
    DWORD *_pdwStubPhase);


/* [helpstring][id] */ HRESULT STDMETHODCALLTYPE IGRiNSPlayer_Stop_Proxy( 
    IGRiNSPlayer __RPC_FAR * This);


void __RPC_STUB IGRiNSPlayer_Stop_Stub(
    IRpcStubBuffer *This,
    IRpcChannelBuffer *_pRpcChannelBuffer,
    PRPC_MESSAGE _pRpcMessage,
    DWORD *_pdwStubPhase);


/* [helpstring][id] */ HRESULT STDMETHODCALLTYPE IGRiNSPlayer_Pause_Proxy( 
    IGRiNSPlayer __RPC_FAR * This);


void __RPC_STUB IGRiNSPlayer_Pause_Stub(
    IRpcStubBuffer *This,
    IRpcChannelBuffer *_pRpcChannelBuffer,
    PRPC_MESSAGE _pRpcMessage,
    DWORD *_pdwStubPhase);



#endif 	/* __IGRiNSPlayer_INTERFACE_DEFINED__ */



#ifndef __GRINSPELib_LIBRARY_DEFINED__
#define __GRINSPELib_LIBRARY_DEFINED__

/* library GRINSPELib */
/* [helpstring][version][uuid] */ 


EXTERN_C const IID LIBID_GRINSPELib;

EXTERN_C const CLSID CLSID_GRiNSPlayer;

#ifdef __cplusplus

class DECLSPEC_UUID("6D2A3400-DFE3-473B-97F8-967FABE83AD7")
GRiNSPlayer;
#endif
#endif /* __GRINSPELib_LIBRARY_DEFINED__ */

/* Additional Prototypes for ALL interfaces */

unsigned long             __RPC_USER  BSTR_UserSize(     unsigned long __RPC_FAR *, unsigned long            , BSTR __RPC_FAR * ); 
unsigned char __RPC_FAR * __RPC_USER  BSTR_UserMarshal(  unsigned long __RPC_FAR *, unsigned char __RPC_FAR *, BSTR __RPC_FAR * ); 
unsigned char __RPC_FAR * __RPC_USER  BSTR_UserUnmarshal(unsigned long __RPC_FAR *, unsigned char __RPC_FAR *, BSTR __RPC_FAR * ); 
void                      __RPC_USER  BSTR_UserFree(     unsigned long __RPC_FAR *, BSTR __RPC_FAR * ); 

/* end of Additional Prototypes */

#ifdef __cplusplus
}
#endif

#endif
