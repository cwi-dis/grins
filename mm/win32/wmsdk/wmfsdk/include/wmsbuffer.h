/* this ALWAYS GENERATED file contains the definitions for the interfaces */


/* File created by MIDL compiler version 5.01.0164 */
/* at Tue Feb 01 17:43:32 2000
 */
/* Compiler settings for .\wmsbuffer.idl:
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

#ifndef __wmsbuffer_h__
#define __wmsbuffer_h__

#ifdef __cplusplus
extern "C"{
#endif 

/* Forward Declarations */ 

#ifndef __INSSBuffer_FWD_DEFINED__
#define __INSSBuffer_FWD_DEFINED__
typedef interface INSSBuffer INSSBuffer;
#endif 	/* __INSSBuffer_FWD_DEFINED__ */


/* header files for imported files */
#include "objidl.h"
#include "ocidl.h"

void __RPC_FAR * __RPC_USER MIDL_user_allocate(size_t);
void __RPC_USER MIDL_user_free( void __RPC_FAR * ); 

/* interface __MIDL_itf_wmsbuffer_0000 */
/* [local] */ 

//=========================================================================
//
//  THIS SOFTWARE HAS BEEN LICENSED FROM MICROSOFT CORPORATION PURSUANT 
//  TO THE TERMS OF AN END USER LICENSE AGREEMENT ("EULA").  
//  PLEASE REFER TO THE TEXT OF THE EULA TO DETERMINE THE RIGHTS TO USE THE SOFTWARE.  
//
// Copyright (C) Microsoft Corporation, 1999 - 1999  All Rights Reserved.
//
//=========================================================================
#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000

EXTERN_GUID( IID_INSSBuffer, 0xE1CD3524,0x03D7,0x11d2,0x9E,0xED,0x00,0x60,0x97,0xD2,0xD7,0xCF );


extern RPC_IF_HANDLE __MIDL_itf_wmsbuffer_0000_v0_0_c_ifspec;
extern RPC_IF_HANDLE __MIDL_itf_wmsbuffer_0000_v0_0_s_ifspec;

#ifndef __INSSBuffer_INTERFACE_DEFINED__
#define __INSSBuffer_INTERFACE_DEFINED__

/* interface INSSBuffer */
/* [version][uuid][unique][object][local] */ 


EXTERN_C const IID IID_INSSBuffer;

#if defined(__cplusplus) && !defined(CINTERFACE)
    
    MIDL_INTERFACE("E1CD3524-03D7-11d2-9EED-006097D2D7CF")
    INSSBuffer : public IUnknown
    {
    public:
        virtual HRESULT STDMETHODCALLTYPE GetLength( 
            /* [out] */ DWORD __RPC_FAR *pdwLength) = 0;
        
        virtual HRESULT STDMETHODCALLTYPE SetLength( 
            /* [in] */ DWORD dwLength) = 0;
        
        virtual HRESULT STDMETHODCALLTYPE GetMaxLength( 
            /* [out] */ DWORD __RPC_FAR *pdwLength) = 0;
        
        virtual HRESULT STDMETHODCALLTYPE GetBuffer( 
            /* [out] */ BYTE __RPC_FAR *__RPC_FAR *ppdwBuffer) = 0;
        
        virtual HRESULT STDMETHODCALLTYPE GetBufferAndLength( 
            /* [out] */ BYTE __RPC_FAR *__RPC_FAR *ppdwBuffer,
            /* [out] */ DWORD __RPC_FAR *pdwLength) = 0;
        
    };
    
#else 	/* C style interface */

    typedef struct INSSBufferVtbl
    {
        BEGIN_INTERFACE
        
        HRESULT ( STDMETHODCALLTYPE __RPC_FAR *QueryInterface )( 
            INSSBuffer __RPC_FAR * This,
            /* [in] */ REFIID riid,
            /* [iid_is][out] */ void __RPC_FAR *__RPC_FAR *ppvObject);
        
        ULONG ( STDMETHODCALLTYPE __RPC_FAR *AddRef )( 
            INSSBuffer __RPC_FAR * This);
        
        ULONG ( STDMETHODCALLTYPE __RPC_FAR *Release )( 
            INSSBuffer __RPC_FAR * This);
        
        HRESULT ( STDMETHODCALLTYPE __RPC_FAR *GetLength )( 
            INSSBuffer __RPC_FAR * This,
            /* [out] */ DWORD __RPC_FAR *pdwLength);
        
        HRESULT ( STDMETHODCALLTYPE __RPC_FAR *SetLength )( 
            INSSBuffer __RPC_FAR * This,
            /* [in] */ DWORD dwLength);
        
        HRESULT ( STDMETHODCALLTYPE __RPC_FAR *GetMaxLength )( 
            INSSBuffer __RPC_FAR * This,
            /* [out] */ DWORD __RPC_FAR *pdwLength);
        
        HRESULT ( STDMETHODCALLTYPE __RPC_FAR *GetBuffer )( 
            INSSBuffer __RPC_FAR * This,
            /* [out] */ BYTE __RPC_FAR *__RPC_FAR *ppdwBuffer);
        
        HRESULT ( STDMETHODCALLTYPE __RPC_FAR *GetBufferAndLength )( 
            INSSBuffer __RPC_FAR * This,
            /* [out] */ BYTE __RPC_FAR *__RPC_FAR *ppdwBuffer,
            /* [out] */ DWORD __RPC_FAR *pdwLength);
        
        END_INTERFACE
    } INSSBufferVtbl;

    interface INSSBuffer
    {
        CONST_VTBL struct INSSBufferVtbl __RPC_FAR *lpVtbl;
    };

    

#ifdef COBJMACROS


#define INSSBuffer_QueryInterface(This,riid,ppvObject)	\
    (This)->lpVtbl -> QueryInterface(This,riid,ppvObject)

#define INSSBuffer_AddRef(This)	\
    (This)->lpVtbl -> AddRef(This)

#define INSSBuffer_Release(This)	\
    (This)->lpVtbl -> Release(This)


#define INSSBuffer_GetLength(This,pdwLength)	\
    (This)->lpVtbl -> GetLength(This,pdwLength)

#define INSSBuffer_SetLength(This,dwLength)	\
    (This)->lpVtbl -> SetLength(This,dwLength)

#define INSSBuffer_GetMaxLength(This,pdwLength)	\
    (This)->lpVtbl -> GetMaxLength(This,pdwLength)

#define INSSBuffer_GetBuffer(This,ppdwBuffer)	\
    (This)->lpVtbl -> GetBuffer(This,ppdwBuffer)

#define INSSBuffer_GetBufferAndLength(This,ppdwBuffer,pdwLength)	\
    (This)->lpVtbl -> GetBufferAndLength(This,ppdwBuffer,pdwLength)

#endif /* COBJMACROS */


#endif 	/* C style interface */



HRESULT STDMETHODCALLTYPE INSSBuffer_GetLength_Proxy( 
    INSSBuffer __RPC_FAR * This,
    /* [out] */ DWORD __RPC_FAR *pdwLength);


void __RPC_STUB INSSBuffer_GetLength_Stub(
    IRpcStubBuffer *This,
    IRpcChannelBuffer *_pRpcChannelBuffer,
    PRPC_MESSAGE _pRpcMessage,
    DWORD *_pdwStubPhase);


HRESULT STDMETHODCALLTYPE INSSBuffer_SetLength_Proxy( 
    INSSBuffer __RPC_FAR * This,
    /* [in] */ DWORD dwLength);


void __RPC_STUB INSSBuffer_SetLength_Stub(
    IRpcStubBuffer *This,
    IRpcChannelBuffer *_pRpcChannelBuffer,
    PRPC_MESSAGE _pRpcMessage,
    DWORD *_pdwStubPhase);


HRESULT STDMETHODCALLTYPE INSSBuffer_GetMaxLength_Proxy( 
    INSSBuffer __RPC_FAR * This,
    /* [out] */ DWORD __RPC_FAR *pdwLength);


void __RPC_STUB INSSBuffer_GetMaxLength_Stub(
    IRpcStubBuffer *This,
    IRpcChannelBuffer *_pRpcChannelBuffer,
    PRPC_MESSAGE _pRpcMessage,
    DWORD *_pdwStubPhase);


HRESULT STDMETHODCALLTYPE INSSBuffer_GetBuffer_Proxy( 
    INSSBuffer __RPC_FAR * This,
    /* [out] */ BYTE __RPC_FAR *__RPC_FAR *ppdwBuffer);


void __RPC_STUB INSSBuffer_GetBuffer_Stub(
    IRpcStubBuffer *This,
    IRpcChannelBuffer *_pRpcChannelBuffer,
    PRPC_MESSAGE _pRpcMessage,
    DWORD *_pdwStubPhase);


HRESULT STDMETHODCALLTYPE INSSBuffer_GetBufferAndLength_Proxy( 
    INSSBuffer __RPC_FAR * This,
    /* [out] */ BYTE __RPC_FAR *__RPC_FAR *ppdwBuffer,
    /* [out] */ DWORD __RPC_FAR *pdwLength);


void __RPC_STUB INSSBuffer_GetBufferAndLength_Stub(
    IRpcStubBuffer *This,
    IRpcChannelBuffer *_pRpcChannelBuffer,
    PRPC_MESSAGE _pRpcMessage,
    DWORD *_pdwStubPhase);



#endif 	/* __INSSBuffer_INTERFACE_DEFINED__ */


/* Additional Prototypes for ALL interfaces */

/* end of Additional Prototypes */

#ifdef __cplusplus
}
#endif

#endif
