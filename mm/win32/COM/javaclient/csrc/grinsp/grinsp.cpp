// grinsp.cpp : Defines the entry point for the DLL application.
//

#include "stdafx.h"

#include "..\..\GRiNSCanvas.h"

#include "jni.h"
#include "jvmdi.h"
#include "jawt.h"

#include "jawt_md.h"

#include <assert.h>

#include "..\..\..\grinscomsvr\idl\IGRiNSPlayerAuto.h"

IGRiNSPlayerAuto* pIGRiNSPlayer=NULL;

extern "C" {


/*
 * Class:     GRiNSCanvas
 * Method:    connect
 * Signature: (Ljava/awt/Graphics;)V
 */
JNIEXPORT void JNICALL Java_GRiNSCanvas_connect(JNIEnv *env, jobject canvas, jobject graphics)
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
	if(pIGRiNSPlayer) return;	
	DWORD dwClsContext = CLSCTX_LOCAL_SERVER;
	HRESULT hr = CoCreateInstance(CLSID_GRiNSPlayerAuto, NULL, dwClsContext, IID_IGRiNSPlayerAuto,(void**)&pIGRiNSPlayer);
 	if(FAILED(hr))
		{
		pIGRiNSPlayer=NULL;
		}
	else
		{
		pIGRiNSPlayer->setWindow(dsi_win->hwnd);
		}
 	//////////////////////////////
	
 	// Free the drawing surface info
 	ds->FreeDrawingSurfaceInfo(dsi);
 
 	// Unlock the drawing surface
 	ds->Unlock(ds);
 
 	// Free the drawing surface
 	awt.FreeDrawingSurface(ds);
	}

/*
 * Class:     GRiNSCanvas
 * Method:    disconnect
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_GRiNSCanvas_disconnect(JNIEnv *env, jobject canvas)
	{
	if(pIGRiNSPlayer)pIGRiNSPlayer->Release();
	pIGRiNSPlayer=NULL;	
	CoUninitialize();	
	}

/*
 * Class:     GRiNSCanvas
 * Method:    open
 * Signature: (Ljava/lang/String;)V
 */
JNIEXPORT void JNICALL Java_GRiNSCanvas_open(JNIEnv *env, jobject canvas, jstring url)
	{
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
JNIEXPORT void JNICALL Java_GRiNSCanvas_close(JNIEnv *env, jobject canvas)
	{
	if(pIGRiNSPlayer)pIGRiNSPlayer->close();	
	}

/*
 * Class:     GRiNSCanvas
 * Method:    play
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_GRiNSCanvas_play(JNIEnv *env, jobject canvas)
	{
	if(pIGRiNSPlayer)pIGRiNSPlayer->play();	
	}

/*
 * Class:     GRiNSCanvas
 * Method:    paint
 * Signature: (Ljava/awt/Graphics;)V
 */
JNIEXPORT void JNICALL Java_GRiNSCanvas_paint(JNIEnv *env, jobject canvas, jobject graphics)
	{
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
	HDC hdc = dsi_win->hdc;
	HWND hwnd = dsi_win->hwnd;
	RECT rc;
	GetClientRect(hwnd, &rc); 
	HBRUSH oldBrush = (HBRUSH)SelectObject(hdc,CreateSolidBrush(RGB(0,255,0)));
	Rectangle(hdc, rc.left, rc.top, rc.right, rc.bottom);
 	//////////////////////////////
	
 	// Free the drawing surface info
 	ds->FreeDrawingSurfaceInfo(dsi);
 
 	// Unlock the drawing surface
 	ds->Unlock(ds);
 
 	// Free the drawing surface
 	awt.FreeDrawingSurface(ds);	
	}

/*
 * Class:     GRiNSCanvas
 * Method:    pause
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_GRiNSCanvas_pause(JNIEnv *env, jobject canvas)
	{
	if(pIGRiNSPlayer)pIGRiNSPlayer->pause();		
	}


/*
 * Class:     GRiNSCanvas
 * Method:    stop
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_GRiNSCanvas_stop(JNIEnv *, jobject)
	 {
	if(pIGRiNSPlayer)pIGRiNSPlayer->stop();		
	 }

} //extern "C"

