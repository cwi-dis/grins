// grinsp.cpp : Defines the entry point for the DLL application.
//

#include "stdafx.h"

#include "..\..\GRiNSViewport.h"

#include "jni.h"
#include "jvmdi.h"
#include "jawt.h"

#include "jawt_md.h"

#include <assert.h>

#include "..\..\..\grinscomsvr\idl\IGRiNSPlayerAuto.h"

inline IGRiNSPlayerAuto* GetIGRiNSPlayer(jint h) {return h?(IGRiNSPlayerAuto*)h:NULL;}

extern "C" {


/*
 * Class:     GRiNSCanvas
 * Method:    connect
 * Signature: (Ljava/awt/Graphics;)V
 */
JNIEXPORT jint JNICALL Java_GRiNSViewport_connect(JNIEnv *env, jobject canvas, jobject graphics)
	{
	CoInitialize(NULL);
	
	// Get the AWT
	JAWT awt;
 	awt.version = JAWT_VERSION_1_3;
 	jboolean result = JAWT_GetAWT(env, &awt);
 	assert(result != JNI_FALSE);
 
 	// Get the drawing surface
 	JAWT_DrawingSurface* ds = awt.GetDrawingSurface(env, canvas);
 	assert(ds != NULL);
 
 	// Lock the drawing surface
 	jint lock = ds->Lock(ds);
 	assert((lock & JAWT_LOCK_ERROR) == 0);
 
 	// Get the drawing surface info
 	JAWT_DrawingSurfaceInfo* dsi = ds->GetDrawingSurfaceInfo(ds);
 
 	// Get the platform-specific drawing info
 	JAWT_Win32DrawingSurfaceInfo *dsi_win = (JAWT_Win32DrawingSurfaceInfo*)dsi->platformInfo;

 	//////////////////////////////
	DWORD dwClsContext = CLSCTX_LOCAL_SERVER;
	IGRiNSPlayerAuto *pIGRiNSPlayer = NULL;
	HRESULT hr = CoCreateInstance(CLSID_GRiNSPlayerAuto, NULL, dwClsContext, IID_IGRiNSPlayerAuto,(void**)&pIGRiNSPlayer);
 	jint hgrins = 0;
	if(SUCCEEDED(hr))
		{
		pIGRiNSPlayer->setWindow(dsi_win->hwnd);
		hgrins = jint(pIGRiNSPlayer);
		}
 	//////////////////////////////
	
 	// Free the drawing surface info
 	ds->FreeDrawingSurfaceInfo(dsi);
 
 	// Unlock the drawing surface
 	ds->Unlock(ds);
 
 	// Free the drawing surface
 	awt.FreeDrawingSurface(ds);

	return hgrins;
	}

/*
 * Class:     GRiNSCanvas
 * Method:    disconnect
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_GRiNSViewport_disconnect(JNIEnv *env, jobject canvas, jint hgrins)
	{
	if(hgrins) 
		{
		IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
		if(pIGRiNSPlayer) pIGRiNSPlayer->Release();
		}
	CoUninitialize();	
	}

/*
 * Class:     GRiNSCanvas
 * Method:    open
 * Signature: (Ljava/lang/String;)V
 */
JNIEXPORT void JNICALL Java_GRiNSViewport_open(JNIEnv *env, jobject canvas, jint hgrins, jstring url)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	if(pIGRiNSPlayer)
		{
		const char *psz = env->GetStringUTFChars(url, NULL);
		WCHAR wPath[MAX_PATH];
		MultiByteToWideChar(CP_ACP,0,LPCTSTR(psz),-1,wPath,MAX_PATH);	
		pIGRiNSPlayer->open(wPath);
		env->ReleaseStringUTFChars(url, psz);
		}	
	}

/*
 * Class:     GRiNSCanvas
 * Method:    close
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_GRiNSViewport_close(JNIEnv *env, jobject canvas, jint hgrins)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	if(pIGRiNSPlayer)pIGRiNSPlayer->close();	
	}

/*
 * Class:     GRiNSCanvas
 * Method:    play
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_GRiNSViewport_play(JNIEnv *env, jobject canvas, jint hgrins)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	if(pIGRiNSPlayer)pIGRiNSPlayer->play();	
	}

/*
 * Class:     GRiNSCanvas
 * Method:    paint
 * Signature: (Ljava/awt/Graphics;)V
 */
JNIEXPORT void JNICALL Java_GRiNSViewport_update(JNIEnv *env, jobject canvas, jint hgrins)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	if(pIGRiNSPlayer)pIGRiNSPlayer->update();		
	}

/*
 * Class:     GRiNSCanvas
 * Method:    pause
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_GRiNSViewport_pause(JNIEnv *env, jobject canvas, jint hgrins)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	if(pIGRiNSPlayer)pIGRiNSPlayer->pause();		
	}


/*
 * Class:     GRiNSCanvas
 * Method:    stop
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_GRiNSViewport_stop(JNIEnv *, jobject, jint hgrins)
	 {
	 IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	 if(pIGRiNSPlayer)pIGRiNSPlayer->stop();		
	 }

} //extern "C"

