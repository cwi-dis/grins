#define INITGUID
#define _WINDOWS

// begin real
#include "pntypes.h"
#include <windows.h>
#include "pnwintyp.h"
#include "pnresult.h"
#include "pncom.h"

#include "rmaenum.h"
#include "engtypes.h"
#include "engtargs.h"
#include "engcodec.h"
#include "rmbldeng.h"
#include "rmmetain.h"
#include "rmapckts.h"
#include "progsink.h"
// end real


#include <stdio.h>
#include <assert.h>

extern void Log(const char *psz);

namespace RProducer {

// passed in
IRMABuildEngine* g_pRMBuildEngine = NULL;
IRMAInputPin*   gVideoPin = NULL;

// created 
IRMAMediaSample* gpVidSample=NULL;

bool HasEngine();
bool SetEngine(IUnknown *p);
bool SetInputPin(IUnknown *p);
bool CreateMediaSample();
bool SetVideoInfo(int w,int h,float rate);
bool EncodeSample(BYTE *p,DWORD size,DWORD msec,bool isSync,bool isLast);
void DoneEncoding();
void Release();



#define PN_CHECK(f,res) if(FAILED(res)) Log(#f" failed\n");
bool HasEngine(){return g_pRMBuildEngine!=NULL;}
bool SetEngine(IUnknown *p)
{
	PN_RELEASE(g_pRMBuildEngine);
	PN_RESULT res=p->QueryInterface(IID_IRMABuildEngine,(void**)&g_pRMBuildEngine);
	PN_CHECK(QueryInterface_IRMABuildEngine,res);
	return SUCCEEDED(res)!=FALSE;
}

bool SetInputPin(IUnknown *p)
{
	PN_RELEASE(gVideoPin);
	PN_RESULT res=p->QueryInterface(IID_IRMAInputPin,(void**)&gVideoPin);
	PN_CHECK(QueryInterface_IRMAInputPin,res);
	return SUCCEEDED(res)!=FALSE;
}

bool CreateMediaSample()
{
	PN_RESULT res;
	IRMABuildClassFactory *clfac;
	res = g_pRMBuildEngine->QueryInterface(IID_IRMABuildClassFactory, (void**) &clfac);

	if (!SUCCEEDED(res)) {
		Log("Query IRMABuildClassFactory failed");
		return false;
	}
	res = clfac->CreateInstance(CLSID_IRMAMediaSample, NULL, IID_IRMAMediaSample, (void **) &gpVidSample);
	PN_RELEASE(clfac);
	if (!SUCCEEDED(res)) {
		Log("CreateInstance RMAMediaSample failed");
		gpVidSample = NULL;
		return false;
	}
	return true;
}

// always encodes in RGB24
bool SetVideoInfo(int w,int h,float rate)
	{
	if(!gVideoPin) return false;
	PN_RESULT res=PNR_OK;
	IRMAPinProperties* pUnkPinProps;
	IRMAVideoPinProperties* gVideoPinProps;
	PN_CHECK(GetPinProperties,gVideoPin->GetPinProperties(&pUnkPinProps));
	PN_CHECK(QueryInterface_IRMAVideoPinProperties,pUnkPinProps->QueryInterface(IID_IRMAVideoPinProperties,(void**)&gVideoPinProps));
	PN_CHECK(SetVideoSize,gVideoPinProps->SetVideoSize(w, h));
	PN_CHECK(SetVideoFormat,gVideoPinProps->SetVideoFormat(ENC_VIDEO_FORMAT_RGB24));
	PN_CHECK(SetCroppingEnabled,gVideoPinProps->SetCroppingEnabled(FALSE));
	PN_CHECK(SetFrameRate,gVideoPinProps->SetFrameRate(rate));
	PN_RELEASE(gVideoPinProps);
	PN_RELEASE(pUnkPinProps);

	CreateMediaSample();

	res=g_pRMBuildEngine->PrepareToEncode();
	if(FAILED(res))
		{
		char sz[120];
		switch(res)
			{
			case PNR_ENC_BAD_CHANNELS: Log("incorrect number of audio input channels\n"); break;
			case PNR_ENC_BAD_SAMPRATE: Log("invalid sample rate specified\n");break;
			case PNR_ENC_IMPROPER_STATE: Log("prepare to encode cannot be called during encoding\n");break;
			case PNR_ENC_INVALID_SERVER:Log("specified server is invalid\n"); break;
 			case PNR_ENC_INVALID_TEMP_PATH:Log("current temp directory is invalid\n"); break;
 			case PNR_ENC_NO_OUTPUT_TYPES:Log("no output mime types specified\n"); break;
 			case PNR_ENC_NO_OUTPUT_FILE:Log("no output file or server specified\n"); break;
			case PNR_NOT_INITIALIZED:Log("Build Engine not properly initialized with the necessary objects\n"); break;
			default:
				sprintf(sz,"Undocumented error 0x%X\n",res);
				Log(sz); 
				break; 
			}
		}
	return SUCCEEDED(res)!=FALSE;
	}


// same arguments as SetBuffer but indirect flags
// the bits are in in RGB24
bool EncodeSample(BYTE *p,DWORD size,DWORD msec,bool isSync,bool isLast)
	{
	if(!gpVidSample) return false;

	UINT16	unFlags=0;
	//if(isSync)unFlags|=MEDIA_SAMPLE_SYNCH_POINT;
	if(isLast)unFlags|=MEDIA_SAMPLE_END_OF_STREAM;
	PN_RESULT res=PNR_OK;
	res = gpVidSample->SetBuffer(p,size,msec,unFlags);
	if(SUCCEEDED(res))
		{
		res=gVideoPin->Encode(gpVidSample);
		if(SUCCEEDED(res))
			Log("Video sample encoded\n");
		else
			Log("Failed to encode video sample\n");
		}
	else 
		Log("Failed to set VidSample buffer\n");
	return SUCCEEDED(res)!=FALSE;
	}

void Release()
	{
	PN_RELEASE(gVideoPin);
	PN_RELEASE(gpVidSample);
	PN_RELEASE(g_pRMBuildEngine);
	}

void DoneEncoding()
	{
	g_pRMBuildEngine->DoneEncoding();
	Release();
	}


} // namespace RProducer


