// grinsp.cpp : Defines the entry point for the DLL application.
//

#include "stdafx.h"

#include "..\..\grins_GRiNSPlayer.h"
#include "..\..\grins_GRiNSPlayerMonitor.h"

#include "jni.h"
#include "jvmdi.h"
#include "jawt.h"

#include "jawt_md.h"

#include <assert.h>
#include "..\..\..\grinscomsvr\idl\IGRiNSPlayerAuto.h"


inline IGRiNSPlayerAuto* GetIGRiNSPlayer(jint h) {return h?(IGRiNSPlayerAuto*)h:NULL;}


extern "C" {
	
static void ThrowCOMException(JNIEnv *env, const char *funcname, HRESULT hr) {
	char* pszmsg;
	FormatMessage( 
		 FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
		 NULL,
		 hr,
		 MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
		 (LPTSTR) &pszmsg,
		 0,
		 NULL 
		);
	char sz[512];
	sprintf(sz, "Native function %s failed, error = %x, %s", funcname, hr, pszmsg);
	LocalFree(pszmsg);
	env->ThrowNew(env->FindClass("GRiNSInterfaceException"), sz);
	} 
/*
 * Class:     GRiNSPlayer
 * Method:    initializeThreadContext
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_grins_GRiNSPlayer_initializeThreadContext(JNIEnv *env, jobject player)
	{
	HRESULT hr = CoInitialize(NULL);
	if(FAILED(hr))
		ThrowCOMException(env, "CoInitialize", hr);
	}

/*
 * Class:     GRiNSPlayer
 * Method:    uninitializeThreadContext
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_grins_GRiNSPlayer_uninitializeThreadContext(JNIEnv *env, jobject player)
	{
	CoUninitialize();		
	}


/*
 * Class:     GRiNSPlayer
 * Method:    nconnect
 * Signature: ()I
 */
JNIEXPORT jint JNICALL Java_grins_GRiNSPlayer_nconnect(JNIEnv *env, jobject player)
	{
	DWORD dwClsContext = CLSCTX_LOCAL_SERVER;
	IGRiNSPlayerAuto *pIGRiNSPlayer = NULL;
	HRESULT hr = CoCreateInstance(CLSID_GRiNSPlayerAuto, NULL, dwClsContext, IID_IGRiNSPlayerAuto,(void**)&pIGRiNSPlayer);
	if(FAILED(hr))
		{
		ThrowCOMException(env, "CoCreateInstance", hr);
		return 0;
		}
	return jint(pIGRiNSPlayer);
	}

/*
 * Class:     grins_GRiNSPlayer
 * Method:    nsetTopLayoutWindow
 * Signature: (IILjava/awt/Component;)V
 */
JNIEXPORT void JNICALL Java_grins_GRiNSPlayer_nsetTopLayoutWindow(JNIEnv *env, jobject player, jint hgrins, jint index, jobject component)
	{
	// Get the AWT
	JAWT awt;
 	awt.version = JAWT_VERSION_1_3;
 	jboolean result = JAWT_GetAWT(env, &awt);
 	assert(result != JNI_FALSE);
 
 	// Get the drawing surface
 	JAWT_DrawingSurface* ds = awt.GetDrawingSurface(env, component);
 	assert(ds != NULL);
 
 	// Lock the drawing surface
 	jint lock = ds->Lock(ds);
 	assert((lock & JAWT_LOCK_ERROR) == 0);
 
 	// Get the drawing surface info
 	JAWT_DrawingSurfaceInfo* dsi = ds->GetDrawingSurfaceInfo(ds);
 
 	// Get the platform-specific drawing info
 	JAWT_Win32DrawingSurfaceInfo *dsi_win = (JAWT_Win32DrawingSurfaceInfo*)dsi->platformInfo;

 	//////////////////////////////

	HWND hwnd = dsi_win->hwnd;

	//////////////////////////////
	
 	// Free the drawing surface info
 	ds->FreeDrawingSurfaceInfo(dsi);
 
 	// Unlock the drawing surface
 	ds->Unlock(ds);
 
 	// Free the drawing surface
 	awt.FreeDrawingSurface(ds);

	
	//////////////////////////////
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	if(pIGRiNSPlayer && IsWindow(hwnd))
		{
		HRESULT hr = pIGRiNSPlayer->setTopLayoutWindow(int(index), hwnd);
		if(FAILED(hr))
			ThrowCOMException(env, "setTopLayoutWindow", hr);
		}
	
	}


/*
 * Class:     GRiNSPlayer
 * Method:    disconnect
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_grins_GRiNSPlayer_ndisconnect(JNIEnv *env, jobject player, jint hgrins)
	{
	if(hgrins) 
		{
		IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
		if(pIGRiNSPlayer) pIGRiNSPlayer->Release();
		}
	}

/*
 * Class:     GRiNSPlayer
 * Method:    open
 * Signature: (Ljava/lang/String;)V
 */
JNIEXPORT void JNICALL Java_grins_GRiNSPlayer_nopen(JNIEnv *env, jobject player, jint hgrins, jstring url)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	if(pIGRiNSPlayer)
		{
		const char *psz = env->GetStringUTFChars(url, NULL);
		WCHAR wPath[MAX_PATH];
		MultiByteToWideChar(CP_ACP,0,LPCTSTR(psz),-1,wPath,MAX_PATH);	
		HRESULT hr = pIGRiNSPlayer->open(wPath);
		env->ReleaseStringUTFChars(url, psz);
		if(FAILED(hr))
			ThrowCOMException(env, "open", hr);
		}	
	}

/*
 * Class:     GRiNSPlayer
 * Method:    close
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_grins_GRiNSPlayer_nclose(JNIEnv *env, jobject player, jint hgrins)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	if(pIGRiNSPlayer) pIGRiNSPlayer->close();	
	}

/*
 * Class:     grins_GRiNSPlayer
 * Method:    ngetTopLayoutDimensions
 * Signature: (II)Ljava/awt/Dimension;
 */
JNIEXPORT jobject JNICALL Java_grins_GRiNSPlayer_ngetTopLayoutDimensions(JNIEnv *env, jobject player, jint hgrins, jint index)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	jint w=0, h=0;
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->getTopLayoutDimensions(int(index), (int*)&w, (int*)&h);
		if(FAILED(hr))
			ThrowCOMException(env, "getSize", hr);
		}
	jclass clazz = env->FindClass("java/awt/Dimension");
	jmethodID methodID = env->GetMethodID(clazz, "<init>", "(II)V");
	return env->NewObject(clazz, methodID, w, h);
	}

/*
 * Class:     GRiNSPlayer
 * Method:    play
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_grins_GRiNSPlayer_nplay(JNIEnv *env, jobject player, jint hgrins)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->play();	
		if(FAILED(hr))
			ThrowCOMException(env, "play", hr);
		}
	}

/*
 * Class:     GRiNSPlayer
 * Method:    paint
 * Signature: (Ljava/awt/Graphics;)V
 */
JNIEXPORT void JNICALL Java_grins_GRiNSPlayer_nupdate(JNIEnv *env, jobject player, jint hgrins)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	if(pIGRiNSPlayer) pIGRiNSPlayer->update();		
	}

/*
 * Class:     GRiNSPlayer
 * Method:    pause
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_grins_GRiNSPlayer_npause(JNIEnv *env, jobject player, jint hgrins)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->pause();	
		if(FAILED(hr))
			ThrowCOMException(env, "pause", hr);
		}
	}


/*
 * Class:     GRiNSPlayer
 * Method:    stop
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_grins_GRiNSPlayer_nstop(JNIEnv *env, jobject player, jint hgrins)
	 {
	 IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	 if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->stop();	
		if(FAILED(hr))
			ThrowCOMException(env, "stop", hr);
		}
	 }

/*
 * Class:     GRiNSPlayer
 * Method:    ngetDuration
 * Signature: (I)D
 */
JNIEXPORT jdouble JNICALL Java_grins_GRiNSPlayer_ngetDuration(JNIEnv *env, jobject player, jint hgrins)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	double dur = 0;
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->getDuration(&dur);	
		if(FAILED(hr))
			ThrowCOMException(env, "getDuration", hr);
		}
	return jdouble(dur);
	}

/*
 * Class:     GRiNSPlayer
 * Method:    ngetSpeed
 * Signature: (I)D
 */
JNIEXPORT jdouble JNICALL Java_grins_GRiNSPlayer_ngetSpeed(JNIEnv *env, jobject player, jint hgrins)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	double speed = 1;
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->getSpeed(&speed);	
		if(FAILED(hr))
			ThrowCOMException(env, "getSpeed", hr);
		}
	return jdouble(speed);
	}

/*
 * Class:     GRiNSPlayer
 * Method:    ngetState
 * Signature: (I)I
 */
JNIEXPORT jint JNICALL Java_grins_GRiNSPlayer_ngetState(JNIEnv *env, jobject player, jint hgrins)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	int plstate = 0;
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->getState(&plstate);	
		if(FAILED(hr))
			ThrowCOMException(env, "getState", hr);
		}
	return jint(plstate);
	}

/*
 * Class:     GRiNSPlayer
 * Method:    ngetTime
 * Signature: (I)D
 */
JNIEXPORT jdouble JNICALL Java_grins_GRiNSPlayer_ngetTime(JNIEnv *env, jobject player, jint hgrins)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	double t = 0;
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->getTime(&t);	
		if(FAILED(hr))
			ThrowCOMException(env, "getTime", hr);
		}
	return jdouble(t);
	}

/*
 * Class:     GRiNSPlayer
 * Method:    nsetSpeed
 * Signature: (ID)V
 */
JNIEXPORT void JNICALL Java_grins_GRiNSPlayer_nsetSpeed(JNIEnv *env, jobject player, jint hgrins, jdouble speed)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->setSpeed(speed);	
		if(FAILED(hr))
			ThrowCOMException(env, "setSpeed", hr);
		}
	}


/*
 * Class:     GRiNSPlayer
 * Method:    nsetTime
 * Signature: (ID)V
 */
JNIEXPORT void JNICALL Java_grins_GRiNSPlayer_nsetTime(JNIEnv *env, jobject player, jint hgrins, jdouble t)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->setTime(t);	
		if(FAILED(hr))
			ThrowCOMException(env, "setTime", hr);
		}
	}

/*
 * Class:     grins_GRiNSPlayer
 * Method:    ngetTopLayoutCount
 * Signature: (I)I
 */
JNIEXPORT jint JNICALL Java_grins_GRiNSPlayer_ngetTopLayoutCount(JNIEnv *env, jobject player, jint hgrins)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	int nl = 1;
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->getTopLayoutCount(&nl);	
		if(FAILED(hr))
			ThrowCOMException(env, "getTopLayoutCount", hr);
		}
	return jint(nl);
	}

/*
 * Class:     grins_GRiNSPlayer
 * Method:    ngetTopLayoutState
 * Signature: (II)I
 */
JNIEXPORT jint JNICALL Java_grins_GRiNSPlayer_ngetTopLayoutState(JNIEnv *env, jobject player, jint hgrins, jint index)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	int wndstate = 1;
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->getTopLayoutState(int(index), &wndstate);	
		if(FAILED(hr))
			ThrowCOMException(env, "getTopLayoutState", hr);
		}
	return jint(wndstate);
	}

/*
 * Class:     grins_GRiNSPlayer
 * Method:    ngetTopLayoutTitle
 * Signature: (II)Ljava/lang/String;
 */
JNIEXPORT jstring JNICALL Java_grins_GRiNSPlayer_ngetTopLayoutTitle(JNIEnv *env, jobject player, jint hgrins, jint index)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	char szTitle[256] = "";
	if(pIGRiNSPlayer)
		{
		wchar_t* wszTitle = NULL;
		HRESULT hr = pIGRiNSPlayer->getTopLayoutTitle(int(index), &wszTitle);
		if(FAILED(hr))
			ThrowCOMException(env, "getTopLayoutTitle", hr);
		else 
			{
			WideCharToMultiByte(CP_ACP, 0, wszTitle, -1, szTitle, 256, NULL, NULL);
			::CoTaskMemFree(wszTitle);
			}
		}
	jstring  jstr = env->NewStringUTF(szTitle);
	return jstr;
	}

/*
 * Class:     grins_GRiNSPlayer
 * Method:    nmouseClicked
 * Signature: (IIII)V
 */
JNIEXPORT void JNICALL Java_grins_GRiNSPlayer_nmouseClicked(JNIEnv *env, jobject player, jint hgrins, jint index, jint x, jint y)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->mouseClicked(int(index), int(x), int(y));	
		if(FAILED(hr))
			ThrowCOMException(env, "mouseClicked", hr);
		}
	}

/*
 * Class:     grins_GRiNSPlayer
 * Method:    nmouseMoved
 * Signature: (IIII)Z
 */
JNIEXPORT jboolean JNICALL Java_grins_GRiNSPlayer_nmouseMoved(JNIEnv *env, jobject player, jint hgrins, jint index, jint x, jint y)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	BOOL bIsHot = FALSE;
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->mouseMoved(int(index), int(x), int(y), &bIsHot);	
		if(FAILED(hr))
			ThrowCOMException(env, "mouseMoved", hr);
		}
	return bIsHot?jboolean(JNI_TRUE):jboolean(JNI_FALSE);
	}

/*
 * Class:     grins_GRiNSPlayer
 * Method:    ngetCookie
 * Signature: (I)I
 */
JNIEXPORT jint JNICALL Java_grins_GRiNSPlayer_ngetCookie(JNIEnv *env, jobject player, jint hgrins)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	long cookie = 0;
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->getCookie(&cookie);	
		if(FAILED(hr))
			ThrowCOMException(env, "getCookie", hr);
		}
	return jint(cookie);	
	}

/*
 * Class:     grins_GRiNSPlayer
 * Method:    ngetFrameRate
 * Signature: (I)I
 */
JNIEXPORT jint JNICALL Java_grins_GRiNSPlayer_ngetFrameRate(JNIEnv *env, jobject player, jint hgrins)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	long fr = 10;
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->getFrameRate(&fr);	
		if(FAILED(hr))
			ThrowCOMException(env, "getFrameRate", hr);
		}
	return jint(fr);	
	}

/////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////

/*
 * Class:     grins_GRiNSPlayerMonitor
 * Method:    initializeThreadContext
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_grins_GRiNSPlayerMonitor_initializeThreadContext(JNIEnv *env, jobject monitor)
	{
	HRESULT hr = CoInitialize(NULL);
	if(FAILED(hr))
		ThrowCOMException(env, "CoInitialize", hr);
	}

/*
 * Class:     grins_GRiNSPlayerMonitor
 * Method:    uninitializeThreadContext
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_grins_GRiNSPlayerMonitor_uninitializeThreadContext(JNIEnv *env, jobject monitor)
	{
	CoUninitialize();		
	}


/*
 * Class:     grins_GRiNSPlayerMonitor
 * Method:    nconnect
 * Signature: (I)I
 */
JNIEXPORT jint JNICALL Java_grins_GRiNSPlayerMonitor_nconnect(JNIEnv *env, jobject monitor, jint cookie)
	{
	DWORD dwClsContext = CLSCTX_LOCAL_SERVER;
	IGRiNSPlayerMoniker *pIGRiNSPlayerMoniker = NULL;
	HRESULT hr = CoCreateInstance(CLSID_GRiNSPlayerMoniker, NULL, dwClsContext, IID_IGRiNSPlayerMoniker,(void**)&pIGRiNSPlayerMoniker);
	if(FAILED(hr))
		{
		ThrowCOMException(env, "CoCreateInstance", hr);
		return 0;
		}
	IGRiNSPlayerAuto *pIGRiNSPlayer = NULL;
	hr = pIGRiNSPlayerMoniker->getGRiNSPlayerAuto(long(cookie),&pIGRiNSPlayer);
	if(FAILED(hr))
		{
		pIGRiNSPlayerMoniker->Release();
		ThrowCOMException(env, "getGRiNSPlayerAuto", hr);
		return 0;
		}
	pIGRiNSPlayerMoniker->Release();
	return jint(pIGRiNSPlayer);
	}
/*
 * Class:     grins_GRiNSPlayerMonitor
 * Method:    ndisconnect
 * Signature: (I)V
 */
JNIEXPORT void JNICALL Java_grins_GRiNSPlayerMonitor_ndisconnect(JNIEnv *env, jobject monitor, jint hgrins)
	{
	if(hgrins) 
		{
		IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
		if(pIGRiNSPlayer) pIGRiNSPlayer->Release();
		}	
	}
/*
 * Class:     grins_GRiNSPlayerMonitor
 * Method:    ngetState
 * Signature: (I)I
 */
JNIEXPORT jint JNICALL Java_grins_GRiNSPlayerMonitor_ngetState(JNIEnv *env, jobject monitor, jint hgrins)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	int plstate = 0;
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->getState(&plstate);	
		if(FAILED(hr))
			ThrowCOMException(env, "getState", hr);
		}
	return jint(plstate);	
	}

/*
 * Class:     grins_GRiNSPlayerMonitor
 * Method:    ngetTime
 * Signature: (I)D
 */
JNIEXPORT jdouble JNICALL Java_grins_GRiNSPlayerMonitor_ngetTime(JNIEnv *env, jobject monitor, jint hgrins)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	double t = 0;
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->getTime(&t);	
		if(FAILED(hr))
			ThrowCOMException(env, "getTime", hr);
		}
	return jdouble(t);	
	}

/*
 * Class:     grins_GRiNSPlayerMonitor
 * Method:    ngetTopLayoutCount
 * Signature: (I)I
 */
JNIEXPORT jint JNICALL Java_grins_GRiNSPlayerMonitor_ngetTopLayoutCount(JNIEnv *env, jobject player, jint hgrins)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	int nl = 1;
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->getTopLayoutCount(&nl);	
		if(FAILED(hr))
			ThrowCOMException(env, "getTopLayoutCount", hr);
		}
	return jint(nl);
	}

/*
 * Class:     grins_GRiNSPlayerMonitor
 * Method:    ngetTopLayoutState
 * Signature: (II)I
 */
JNIEXPORT jint JNICALL Java_grins_GRiNSPlayerMonitor_ngetTopLayoutState(JNIEnv *env, jobject player, jint hgrins, jint index)
	{
	IGRiNSPlayerAuto *pIGRiNSPlayer = GetIGRiNSPlayer(hgrins);
	int wndstate = 1;
	if(pIGRiNSPlayer)
		{
		HRESULT hr = pIGRiNSPlayer->getTopLayoutState(int(index), &wndstate);	
		if(FAILED(hr))
			ThrowCOMException(env, "getTopLayoutState", hr);
		}
	return jint(wndstate);
	}




} //extern "C"

