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

// 

namespace RProducer {

IRMABuildEngine* g_pRMBuildEngine = NULL;
UINT32 g_pTargetAudiences[ENC_NUM_TARGET_AUDIENCES];
IRMAClipProperties* g_pClipProps = NULL;
IRMABasicTargetSettings* g_pBasicSettings = NULL;
IRMABuildClassFactory*  g_pClassFactory=NULL;
IRMAMediaSample* pVidSample=NULL;

BOOL g_bAudio = FALSE;
BOOL g_bVideo = TRUE;
BOOL g_bEvent = FALSE;
BOOL g_bImageMap = FALSE;
IRMAInputPin*   gAudioPin = NULL;
IRMAInputPin*   gVideoPin = NULL;
IRMAInputPin*	gEventPin = NULL;
IRMAInputPin*	gImageMapPin = NULL;
UINT32 g_ulAudioFormat = 0;
UINT32 g_ulVideoQuality = ENC_VIDEO_QUALITY_NORMAL;


void SetDllCategoryPaths();
bool Init();
void SetOutputFilename(const char* szOutputFile);
void Cleanup();
bool Prepare();
void SetVideoInfo(int w,int h,float rate);
void EncodeSample(BYTE *p,int frame,bool isLast);
void DoneEncoding();
bool CreateRMBuildEngine();


STDAPI SetDLLAccessPath(const char* pPathDescriptor);

#define PN_EXEC(f,res) if(FAILED(res)) Log(#f" failed\n");

//****************************************************************************
void Cleanup()
{
	// The PN_RELEASE macro (defined in pntypes.h) calls Release() on the
	// pointer ifit is not NULL and sets the value to NULL.
	PN_RELEASE(g_pClipProps);
	PN_RELEASE(g_pBasicSettings);
	PN_RELEASE(	g_pRMBuildEngine);
	//PN_RELEASE(g_pVideoPreviewSink);
}

/****************************************************************************
* Definitions
*/
char* pBinDir = "C:\\Program Files\\RealSDK\\Producer\\BIN\\";

struct SDllCategoryEntry
{
	const char* pDllCategoryName;
	const char* pDllCategoryPath;
};

void SetDllCategoryPaths()
{		

	// Create a table used to build the DLL category path string
	SDllCategoryEntry dllPathTable[] =
	{
		{"DT_Plugins", pBinDir},
		{"DT_Codecs", pBinDir},
		{"DT_EncSDK", pBinDir},
		{"DT_Common", pBinDir}
	};

	UINT32 ulNumChars = 0;
	UINT32 ulNumEntries = sizeof(dllPathTable) / sizeof(SDllCategoryEntry);

	char szDllPath[2048];   
	memset(szDllPath, 0, 2048);

	// Create a null delimited, double-null terminated string containing
	// DLL category name/path pairs.
	for(UINT32 i=0; i<ulNumEntries; i++)
	{
		if(dllPathTable[i].pDllCategoryPath)
		{
			ulNumChars += sprintf(szDllPath+ulNumChars, "%s=%s", dllPathTable[i].pDllCategoryName,dllPathTable[i].pDllCategoryPath) + 1;
		}
	}
	
	// Set the path used to load RealProducer Core G2 SDK DLL's
	SetDLLAccessPath(szDllPath);
}



/***************************************************************************
* Init
*
* This function creates and initializes the build engine. The engine
* properties, clip properties, and target settings are all set here.
* Also, the pin interfaces for all the pins which are to be used in
* encoding are established in this function.
*/


bool Init()
{
	for (UINT32 i = 0; i < ENC_NUM_TARGET_AUDIENCES; i++) 
	{
		g_pTargetAudiences[i] = FALSE;
	}

	PN_RESULT res = PNR_OK;

	//***************************************************************************
	//
	// Create the RM Build Engine
	//
	//***************************************************************************
	res = RMACreateRMBuildEngine(&g_pRMBuildEngine);
	char sz[256];
	if(res==PNR_NOT_INITIALIZED)
		sprintf(sz,"RMACreateRMBuildEngine failed. Error PNR_NOT_INITIALIZED");
	if(FAILED(res))
		Log(sz);

	if(SUCCEEDED(res))
	{
		//***************************************************************************
		//
		// Get the pin enumerator, and get the pins from the
		// list and available output mime types from each pin.
		//
		//***************************************************************************
		
		IUnknown* tempUnk = NULL;
		IRMAEnumeratorIUnknown* pPinEnum = NULL;
		
		res = g_pRMBuildEngine->GetPinEnumerator(&pPinEnum);
		if(FAILED(res)) return res == PNR_OK;
		
		PN_RESULT resEnum = PNR_OK;
		resEnum = pPinEnum->First(&tempUnk);
		
		char* outputTypeStr = new char[256];
		while(SUCCEEDED(res) && SUCCEEDED(resEnum) && resEnum != PNR_ELEMENT_NOT_FOUND)
		{
			IRMAInputPin* tempPin = NULL;
			res = tempUnk->QueryInterface(IID_IRMAInputPin, (void**)&tempPin);
			PN_RELEASE(tempUnk);

			if(SUCCEEDED(res))
			{
				tempPin->GetOutputMimeType(outputTypeStr, 256);

				if(g_bAudio && strcmp(outputTypeStr, MIME_REALAUDIO) == 0)
				{
					gAudioPin = tempPin;
					gAudioPin->AddRef();
				}
				else if(g_bVideo && strcmp(outputTypeStr, MIME_REALVIDEO) == 0)
				{
					gVideoPin = tempPin;
					gVideoPin->AddRef();
				}
				else if(g_bEvent && strcmp(outputTypeStr, MIME_REALEVENT) == 0)
				{
					gEventPin = tempPin;
					gEventPin->AddRef();
				}

				else if(g_bImageMap && strcmp(outputTypeStr, MIME_REALIMAGEMAP) == 0)
				{
					gImageMapPin = tempPin;
					gImageMapPin->AddRef();
				}

				PN_RELEASE(tempPin);
				resEnum = pPinEnum->Next(&tempUnk);
			} 
			else 
			{
				printf("Cannot query input pin interface.\n");
			}
		} // end while...
		delete [] outputTypeStr;
		
		PN_RELEASE(pPinEnum);
		
		if((!gAudioPin && g_bAudio) || (!gVideoPin && g_bVideo) ||
			(!gEventPin && g_bEvent) || (!gImageMapPin && g_bImageMap) || !SUCCEEDED(res))
		{
			PN_RELEASE(gAudioPin);
			PN_RELEASE(gVideoPin);
			PN_RELEASE(gEventPin);
			PN_RELEASE(gImageMapPin);
			res = PNR_NOINTERFACE;
			printf("No pin interface established...\n");
		}
		
		if(SUCCEEDED(res)) 
		{
			//***************************************************************************
			//
			// Set up all the engine properties on the RM Build Engine
			//
			//***************************************************************************

			// Set to encode only audio and video
			g_pRMBuildEngine->SetDoOutputMimeType(MIME_REALAUDIO, g_bAudio);
			g_pRMBuildEngine->SetDoOutputMimeType(MIME_REALVIDEO, g_bVideo);
			g_pRMBuildEngine->SetDoOutputMimeType(MIME_REALEVENT, g_bEvent);
			g_pRMBuildEngine->SetDoOutputMimeType(MIME_REALIMAGEMAP, g_bImageMap);

			// The generated file is intended to be server from
			// a RealServer (as opposed to HTTP server).
			g_pRMBuildEngine->SetRealTimeEncoding(FALSE);
			g_pRMBuildEngine->SetDoMultiRateEncoding(TRUE);

			//***************************************************************************
			//
			// Set up all the clip properties for the RM Build Engine
			//
			//***************************************************************************

			// Get the Clip Properties object
			PN_EXEC(RMBuildEngine->GetClipProperties,
				(res = g_pRMBuildEngine->GetClipProperties(&g_pClipProps)));
			if(FAILED(res)) return false;

			// default the clip info
			PN_EXEC(SetTitle,g_pClipProps->SetTitle("Untitled"));
			PN_EXEC(SetAuthor,g_pClipProps->SetAuthor("Uknown"));
			PN_EXEC(SetCopyright,g_pClipProps->SetCopyright("(c)1999 Oratrix"));
			PN_EXEC(SetPerfectPlay,g_pClipProps->SetPerfectPlay(TRUE));
			PN_EXEC(SetMobilePlay,g_pClipProps->SetMobilePlay(TRUE));
			PN_EXEC(SetSelectiveRecord,g_pClipProps->SetSelectiveRecord(FALSE));

			// default the destination
			PN_EXEC(SetDoOutputServer,g_pClipProps->SetDoOutputServer(FALSE));
			PN_EXEC(SetDoOutputFile,g_pClipProps->SetDoOutputFile(TRUE));

			//***************************************************************************
			//
			// Set up all the target settings for the RM Build Engine
			//
			//***************************************************************************

			// get the Basic Settings object
			IRMATargetSettings *targSettings;
			res = g_pRMBuildEngine->GetTargetSettings(&targSettings);
			PN_EXEC(RMBuildEngine->GetTargetSettings,res);
			assert(SUCCEEDED(res));

			res = targSettings->QueryInterface(IID_IRMABasicTargetSettings, (void**)&g_pBasicSettings);
			PN_EXEC(QueryInterface_IRMABasicTargetSettings,res);
			assert(SUCCEEDED(res));
			
			PN_RELEASE(targSettings);
			
			PN_RESULT tempRes = PNR_OK;
			
			tempRes = g_pBasicSettings->SetVideoQuality(g_ulVideoQuality);
			
			if(!SUCCEEDED(tempRes))
			{
				printf("Invalid Video Quality. Using default: Normal Video Quality");
			}
			
			/*
			NO AUDIO FOR NOW
			tempRes = g_pBasicSettings->SetAudioContent(g_ulAudioFormat);
			if(!SUCCEEDED(tempRes))
			{
				printf("Invalid Audio Format. Using default: Voice Only");
			}

			// clear target audiences
			g_pBasicSettings->RemoveAllTargetAudiences();
			
			for (UINT32 i = 0; i < ENC_NUM_TARGET_AUDIENCES; i++) 
			{
				if(g_pTargetAudiences[i]) 
				{
					g_pBasicSettings->AddTargetAudience(i);
				}
			}*/
		}
	} 
	else 
	{
		printf("Unable to create build engine.\n");
	}

	return SUCCEEDED(res);
}

void SetOutputFilename(const char* szOutputFile)
	{
	if(g_pClipProps)
		{
		Log(szOutputFile);Log("\n");
		PN_EXEC(SetOutputFilename,g_pClipProps->SetOutputFilename(szOutputFile));
		}
	}

// SetMetaStringValue demonstrates how to set a C string into an IRMAValue
PN_RESULT SetMetaStringValue(IRMAValues* pValues, const char* pName, const char* pValue)
{
	PN_RESULT res = PNR_OK;
	IRMABuildClassFactory*  pClassFactory = NULL;
	IRMABuffer* pString = NULL;
	
	if(!pName || !pValue || !pValues)
	{
		return PNR_POINTER;
	}

	// we need to get the IRMABuildClassFactory in order to create an IRMABuffer
	if(SUCCEEDED(res))
	{
		res = g_pRMBuildEngine->QueryInterface(IID_IRMABuildClassFactory, (void**)&pClassFactory);
	}
	
	// now that we have an IRMACommonClassFactory, we can create an IRMABuffer
	if(SUCCEEDED(res))
	{
		res = pClassFactory->CreateInstance(CLSID_IRMABuffer, NULL, IID_IRMABuffer,(void**)&pString);
	}
	
	// Set the string in the IRMABuffer and add it to the IRMAValues
	if(SUCCEEDED(res))
	{
		pString->Set((UCHAR*)pValue, strlen(pValue) + 1);
		res = pValues->SetPropertyCString(pName, pString);
	}
	
	// clean up
	PN_RELEASE(pString);
	PN_RELEASE(pClassFactory);

	return res;
}

PN_RESULT DoMetaInformation(void)
{
	PN_RESULT res = PNR_OK;
	IRMARMMetaInformation* pRMMetaInfo = NULL;
	IRMAValues* pValues = NULL;
	
	if(!g_pRMBuildEngine)
	{
		res = PNR_NOT_INITIALIZED;
	}
	
	// get the MetaInformation interface
	if(SUCCEEDED(res))
	{
		res = g_pRMBuildEngine->QueryInterface(IID_IRMARMMetaInformation,(void**)&pRMMetaInfo);
	}
	else Log("QueryInterface IRMARMMetaInformation failed\n");
	if(SUCCEEDED(res)) // get the IRMAValues holding the MetaInformation.
	{
		res = pRMMetaInfo->GetMetaInformation(&pValues);
	}

	// set the Generated By string
	if(SUCCEEDED(res))
	{
		res = SetMetaStringValue(pValues,RM_PROPERTY_GENERATOR,"RealProducer G2 Core SDK");
	}
	else Log("SetMetaStringValue failed\n");
	// cleanup
	PN_RELEASE(pRMMetaInfo); 
	PN_RELEASE(pValues); 

	return res;
}


bool Prepare()
	{
	PN_RESULT res = g_pRMBuildEngine->QueryInterface(IID_IRMABuildClassFactory, (void**)&g_pClassFactory);
	// set the MetaInformation for the clip
	if(SUCCEEDED(res))
	{
		res = DoMetaInformation();
	}
	else Log("QueryInterface IRMABuildClassFactory failed");
	return (SUCCEEDED(res)!=FALSE);
	}

void SetVideoInfo(int w,int h,float rate)
	{
	ULONG32 nVideoWidth=w;
	ULONG32 nVideoHeight=h;
	float   fFrameRate=rate;
	IRMAPinProperties* pUnkPinProps;
	PN_RESULT res;
	PN_EXEC(GetPinProperties,gVideoPin->GetPinProperties(&pUnkPinProps));
	IRMAVideoPinProperties* gVideoPinProps;
	PN_EXEC(QueryInterface_IRMAVideoPinProperties,pUnkPinProps->QueryInterface(IID_IRMAVideoPinProperties,(void**)&gVideoPinProps));
	PN_EXEC(SetVideoSize,gVideoPinProps->SetVideoSize(nVideoWidth, nVideoHeight));
	PN_EXEC(SetVideoFormat,gVideoPinProps->SetVideoFormat(ENC_VIDEO_FORMAT_RGB24));
	PN_EXEC(SetCroppingEnabled,gVideoPinProps->SetCroppingEnabled(FALSE));
	PN_EXEC(SetFrameRate,gVideoPinProps->SetFrameRate(fFrameRate));
	PN_RELEASE(gVideoPinProps);
	PN_RELEASE(pUnkPinProps);
	res=g_pRMBuildEngine->PrepareToEncode();
	if(FAILED(res))
		{
		switch(res)
			{
			case PNR_OK: 
			case PNR_ENC_BAD_CHANNELS: Log("incorrect number of audio input channels\n"); break;
			case PNR_ENC_BAD_SAMPRATE: Log("invalid sample rate specified\n");break;
			case PNR_ENC_IMPROPER_STATE: Log("prepare to encode cannot be called during encoding\n");break;
			case PNR_ENC_INVALID_SERVER:Log("specified server is invalid\n"); break;
 			case PNR_ENC_INVALID_TEMP_PATH:Log("current temp directory is invalid\n"); break;
 			case PNR_ENC_NO_OUTPUT_TYPES:Log("no output mime types specified\n"); break;
 			case PNR_ENC_NO_OUTPUT_FILE:Log("no output file or server specified\n"); break;
			case PNR_NOT_INITIALIZED:Log("Build Engine not properly initialized with the necessary objects\n"); break;
			default:Log("Undocumented error\n"); break; 
			}
		}
	PN_EXEC(CreateInstance_IRMAMediaSample,g_pClassFactory->CreateInstance(CLSID_IRMAMediaSample, NULL, IID_IRMAMediaSample, (void **)&pVidSample));
	}

void EncodeSample(BYTE *p,int frame,bool isLast)
	{
	BITMAPINFOHEADER *pbi=(BITMAPINFOHEADER*)p;

	PN_RESULT res=PNR_OK;
	//if(!isLast)
	res = pVidSample->SetBuffer((UCHAR*)(pbi+1), pbi->biSizeImage, frame, 0);
	//else
	//	res = pVidSample->SetBuffer((UCHAR*)(pbi+1), pbi->biSizeImage, frame, MEDIA_SAMPLE_END_OF_STREAM);

	if(SUCCEEDED(res))
		{
		res=gVideoPin->Encode(pVidSample);
		if(SUCCEEDED(res))
			Log("Video sample encoded\n");
		else
			Log("Failed to encode video sample\n");
		}
	else 
		Log("Failed to set VidSample buffer\n");
	}


void DoneEncoding()
	{
	g_pRMBuildEngine->DoneEncoding();
	PN_RELEASE(gVideoPin);
	PN_RELEASE(g_pClassFactory);
	PN_RELEASE(pVidSample);
	}

} // namespace RProducer
