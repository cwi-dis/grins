/****************************************************************************
 * 
 *  $Id$
 *
 *  Copyright (C) 1998-2000 RealNetworks.
 *  All rights reserved.
 *  
 *  http://www.real.com/devzone
 *
 *  This program contains proprietary information of RealNetworks, Inc., 
 *  and is licensed subject to restrictions on use and distribution.
 *
 *
 *  Main interfaces used for the RealProducer G2 Core SDK.
 */

#ifndef _RMBLDENG_H_
#define _RMBLDENG_H_


/*
 * Forward declarations of some interfaces defined here-in.
 */

typedef _INTERFACE IUnknown			IUnknown;
typedef _INTERFACE IRMAEnumeratorIUnknown	IRMAEnumeratorIUnknown;

typedef _INTERFACE IRMABuildEngine		IRMABuildEngine;
typedef _INTERFACE IRMABuildEngine2		IRMABuildEngine2;
typedef _INTERFACE IRMABuildClassFactory	IRMABuildClassFactory;
typedef _INTERFACE IRMAInputPin			IRMAInputPin;
typedef _INTERFACE IRMAAudioInputPin		IRMAAudioInputPin;
typedef _INTERFACE IRMAVideoInputPin		IRMAVideoInputPin;
typedef _INTERFACE IRMAVideoPreviewSinkControl	IRMAVideoPreviewSinkControl;
typedef _INTERFACE IRMAVideoPreviewSink		IRMAVideoPreviewSink;
typedef _INTERFACE IRMAVideoInputPinFeedback	IRMAVideoInputPinFeedback;
typedef _INTERFACE IRMAMediaSample		IRMAMediaSample;
typedef _INTERFACE IRMAEventMediaSample		IRMAEventMediaSample;
typedef _INTERFACE IRMAImageMapMediaSample  	IRMAImageMapMediaSample;

typedef _INTERFACE IRMAClipProperties		IRMAClipProperties;
typedef _INTERFACE IRMABroadcastServerProperties IRMABroadcastServerProperties;
typedef _INTERFACE IRMAPinProperties		IRMAPinProperties;
typedef _INTERFACE IRMAAudioPinProperties	IRMAAudioPinProperties;
typedef _INTERFACE IRMAVideoPinProperties	IRMAVideoPinProperties;	
typedef _INTERFACE IRMAVideoFilters			IRMAVideoFilters;
typedef _INTERFACE IRMAVideoAnalysis		IRMAVideoAnalysis;
typedef _INTERFACE IRMAWallclock			IRMAWallclock;

/****************************************************************************
 *  Function:
 *	RMACreateRMBuildEngine
 *  Purpose:
 *	Creates an instance of a Real Media Build Engine object. This 
 *	object can also be queried for the IRMABuildClassFactory interface. 
 *	The IRMABuildClassFactory::CreateInstance() method can then be 
 *	called to create other objects supported by the RealProducer G2 Core SDK.
 */
STDAPI
RMACreateRMBuildEngine( IRMABuildEngine** ppRMBuildEngine );

typedef PN_RESULT (PNEXPORT_PTR FPRMCREATERMBUILDENGINE)
	(IRMABuildEngine** ppRMBuildEngine );

/****************************************************************************
 * 
 *  Interface:
 * 
 *	IRMABuildClassFactory
 * 
 *  Purpose:
 * 
 *	Provides methods that can be used to create instances of known 
 *	classes used for the RealProducer G2 Core SDK.
 * 
 *  IID_IRMABuildClassFactory:
 * 
 *	{935D1C40-0F6E-11d2-B657-00C0F0312253}
 * 
 */
DEFINE_GUID( IID_IRMABuildClassFactory,
    0x935d1c40, 0xf6e, 0x11d2, 0xb6, 0x57, 0x0, 0xc0, 0xf0, 0x31, 0x22, 0x53);

#undef  INTERFACE
#define INTERFACE   IRMABuildClassFactory

DECLARE_INTERFACE_(IRMABuildClassFactory, IUnknown)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					REFIID riid,
					void** ppvObj) PURE;

    STDMETHOD_(ULONG32,AddRef)		(THIS) PURE;

    STDMETHOD_(ULONG32,Release)		(THIS) PURE;

    /************************************************************************
     *	Method:
     *	    IRMABuildClassFactory::CreateInstance
     *	Purpose:
     *	    Creates instances of classes needed for the Build SDK like
     *	    IRMAClipProperties, IRMAMediaSample, etc.
     *
     *	    This method is similar to Window's CoCreateInstance() in its 
     *	    purpose, except that it only creates objects known to the sytem.
     *	Parameters:
     *	    rclsid - [in] Class identifier (CLSID) of the object
     *	    pUnkOuter - [in] Pointer to whether object is or isn't part 
     *			     of an aggregate. Use NULL if the object will
     *			     not be aggregated.
     *	    riid - [in] Reference to the identifier of the interface desired
     *	    ppv - [out] Address of output variable that receives 
     *                  the interface pointer requested in riid
     *	Returns:
     *	    PNR_OK - if success
     *	    PNR_NOCLASS - Class is not known by the factory.
     *	    PNR_NOINTERFACE - class doesn't support the requested interface
     *	    PNR_CLASS_NOAGGREGATION - class doesn't support being aggregated
     *      PNR_POINTER - ppv is not a valid pointer
     */
    STDMETHOD(CreateInstance)		(THIS_
					REFCLSID    /*IN*/  rclsid,
					IUnknown*   /*IN*/  pUnkOuter,
					REFIID	    /*IN*/  riid,
					void**	    /*OUT*/ ppv ) PURE;
};
 
/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMABuildEngine
 *
 *  Purpose:
 *
 *	Manages the process of encoding N input streams into N output streams
 *	that will be combined into a single RealMedia file that supports ASM.
 *
 *  IID_IRMABuildEngine:
 *
 *	{2012AFC0-B9F9-11d1-9AF8-006097B76F50}
 *	
 *
 */
DEFINE_GUID(IID_IRMABuildEngine, 
	    0x2012afc0, 0xb9f9, 0x11d1, 0x9a, 0xf8, 0x0, 0x60, 0x97, 0xb7, 0x6f, 0x50);

#undef INTERFACE
#define INTERFACE IRMABuildEngine

DECLARE_INTERFACE_(IRMABuildEngine, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					 REFIID riid,
					 void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;

    /***********************************************************************/
    /*
     * IRMABuildEngine methods
     */

    /************************************************************************
     *	Method:
     *	    IRMABuildEngine::GetPinEnumerator
     *	Purpose:
     *	    returns an IUnknown enumerator containing all of the available input pins
     *	    QI each object for IRMAInputPin
     *	Parameters:
     *	    ppPinEnum - [out] address of IRMAEnumeratorIUnknown* for the Pin Enumerator
     */
    STDMETHOD(GetPinEnumerator)		(THIS_
	IRMAEnumeratorIUnknown**    ppPinEnum) PURE;

    /************************************************************************
     *	Method:
     *	    IRMABuildEngine::GetClipProperties/SetClipProperties
     *	Purpose:
     *	    Get/Set the current clip properties on the build engine
     *	    The RMBuildEngine will merely share a pointer to the clip properties object
     *	    so any modifications made after SetClipProperties will be shared with the RM Build Engine
     *	    (RM Build Engine will be created with default Clip Properties)
     *	Parameters:
     *	    pClipProperties - [in/out] pointer to an IRMAClipProperties interface
     */
    STDMETHOD(GetClipProperties)	(THIS_
	IRMAClipProperties** ppClipProperties) PURE;
    STDMETHOD(SetClipProperties)	(THIS_
	IRMAClipProperties* pClipProperties) PURE;

    /************************************************************************
     *	Method:
     *	    IRMABuildEngine::GetTargetSettings/SetTargetSettings
     *	Purpose:
     *	    Get/Set the current target settings on the build engine
     *	    The RMBuildEngine will merely share a pointer to the target settings object
     *	    so any modifications made after SetTargetSettings will be shared with the RM Build Engine
     *	    (RM Build Engine will be created with default Basic Target Settings)
     *	Parameters:
     *	    pTargetSettings - [in/out] pointer to an IRMATargetSettings interface. This object must 
     *	    also support either the IRMABasicTargetSettings or IRMAAdvancedTargetSettings interface
     */
    STDMETHOD(GetTargetSettings)	(THIS_
	IRMATargetSettings** ppTargetSettings) PURE;
    STDMETHOD(SetTargetSettings)	(THIS_
	IRMATargetSettings* pTargetSettings) PURE;

    /************************************************************************
     *	Method:
     *	    IRMABuildEngine::GetRealTimeEncoding/SetRealTimeEncoding
     *	Purpose:
     *	    Get/Set whether or not the encoding must be done in real-time (default: FALSE)
     *	Parameters:
     *	    bRealTimeEncoding - [in/out] whether or not the encoding must be done in 
     *					 real-time
     */
    STDMETHOD(GetRealTimeEncoding)	(THIS_
	BOOL* pbRealTimeEncoding) PURE;
    STDMETHOD(SetRealTimeEncoding)	(THIS_
	BOOL bRealTimeEncoding) PURE;

    /************************************************************************
     *	Method:
     *	    IRMABuildEngine::GetDoMultiRateEncoding/SetDoMultiRateEncoding
     *	Purpose:
     *	    Get/Set whether or not the encoding should be multi-rate or single-rate
     *	Parameters:
     *	    bDoMultiRate - [in/out] whether or not the encoding should be multi-rate 
     *				    or single-rate
     */
    STDMETHOD(GetDoMultiRateEncoding)	(THIS_
	BOOL* pbDoMultiRate) PURE;
    STDMETHOD(SetDoMultiRateEncoding)	(THIS_
	BOOL bDoMultiRate) PURE;

    /************************************************************************
     *	Method:
     *	    IRMABuildEngine::GetDoOutputMimeType/SetDoOutputMimeType
     *	Purpose:
     *	    Get/Set whether or not the build engine should create streams and expect data to be 
     *	    passed to the Pin during encoding for the specified mime type
     *	Parameters:
     *	    szMimeType - [in] mime type 
     *	    bEncode - [in/out] whether or not build engine will be encoding data for this mime 
     *	    type
     */
    STDMETHOD(GetDoOutputMimeType)	(THIS_
	char* szMimeType, BOOL* pbEncode) PURE;
    STDMETHOD(SetDoOutputMimeType)	(THIS_
	char* szMimeType, BOOL bEncode) PURE;

    /************************************************************************
     *	Method:
     *	    IRMABuildEngine::ResetAllOutputMimeTypes
     *	Purpose:
     *	    Reset doing all mime types to FALSE
     */
    STDMETHOD(ResetAllOutputMimeTypes)	(THIS) PURE;

    /************************************************************************
     *	Method:
     *	    IRMABuildEngine::GetTempDirectory/SetTempDirectory
     *	Purpose:
     *	    Get/Set the temp directory which the build engine will use for temporary
     *	    storage during encoding [default: system temp directory]
     *	Parameters:
     *	    szTempDirectory - [in/out] temp directory 
     *	    nMaxLen - [in] max allocated for the string
     */
    STDMETHOD(GetTempDirectory)	(THIS_
	char* szTempDirectory, UINT32 nMaxLen) PURE;
    STDMETHOD(SetTempDirectory)	(THIS_
	const char* szTempDirectory) PURE;

    /************************************************************************
     *	Method:
     *	    IRMABuildEngine::PrepareToEncode
     *	Purpose:
     *	    Notifies the build manager that all engines have been
     *	    initialized and encoding will soon commence.
     *	Returns:
     *	    PNR_OK - if success
     *	    PNR_ENC_BAD_CHANNELS - incorrect number of audio input channels 
     *		specified (must be 2 if stereo music selected)
     *	    PNR_ENC_BAD_SAMPRATE - invalid sample rate specified
     *	    PNR_ENC_IMPROPER_STATE - prepare to encode cannot be called during 
     *		encoding
     *	    PNR_ENC_INVALID_SERVER - specified server is invalid
     *	    PNR_ENC_INVALID_TEMP_PATH - current temp directory is invalid
     *	    PNR_ENC_NO_OUTPUT_TYPES - no output mime types specified
     *	    PNR_ENC_NO_OUTPUT_FILE - no output file or server specified
     *	    PNR_NOT_INITIALIZED - Build Engine not properly initialized with
     *		necessary objects.
     */
    STDMETHOD(PrepareToEncode)		(THIS) PURE;

    /************************************************************************
     *	Method:
     *	    IRMABuildEngine::DoneEncoding
     *	Purpose:
     *	    Completes the encoding process.
     *	Returns:
     *	    PNR_OK - if success
     *	    PNR_MERGE_FAIL - unable to create destination file
     *	    PNR_NO_ENCODED_DATA - no data was encoded
     */
    STDMETHOD(DoneEncoding)		(THIS) PURE;

    /************************************************************************
     *	Method:
     *	    IRMABuildEngine::CancelEncoding
     *	Purpose:
     *	    Aborts the encoding process.
     */
    STDMETHOD(CancelEncoding)		(THIS) PURE;
};


/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMABuildEngine2
 *
 *  Purpose:
 *
 *	Manages the process of encoding N input streams into N output streams
 *	that will be combined into a single RealMedia file that supports ASM.
 *
 *  IID_IRMABuildEngine2:
 *
 *	{46E63160-EDEB-11d2-8746-00C0F031C266}
 *	
 *
 */
DEFINE_GUID(IID_IRMABuildEngine2, 
	    0x46e63160, 0xedeb, 0x11d2, 0x87, 0x46, 0x0, 0xc0, 0xf0, 0x31, 0xc2, 0x66);

#undef INTERFACE
#define INTERFACE IRMABuildEngine2

DECLARE_INTERFACE_(IRMABuildEngine2, IRMABuildEngine)
{

    /************************************************************************
     *	Method:
     *	    IRMABuildEngine2::GetTargetAudienceManager/SetTargetAudienceManager
     *	Purpose:
     *	    Get/Set the target audience manager on the build engine
     *	Parameters:
     *	    pTargetAudienceMgr [out] - pointer to an IRMATargetAudienceManager interface
     */
    STDMETHOD(GetTargetAudienceManager)	(THIS_
	IRMATargetAudienceManager** ppTargetAudienceMgr) PURE;
    STDMETHOD(SetTargetAudienceManager)	(THIS_
	IRMATargetAudienceManager* pTargetAudienceMgr) PURE;
};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAInputPin
 *
 *  Purpose:
 *
 *	Encoding engine that takes an input data of a supported type and 
 *	converts it into a requested output type.
 *
 *  IID_IRMAInputPin:
 *
 *		{42481750-B9F9-11d1-9AF8-006097B76F50}
 *	
 *
 */
DEFINE_GUID(IID_IRMAInputPin, 
0x42481750, 0xb9f9, 0x11d1, 0x9a, 0xf8, 0x0, 0x60, 0x97, 0xb7, 0x6f, 0x50);

#undef INTERFACE
#define INTERFACE IRMAInputPin

DECLARE_INTERFACE_(IRMAInputPin, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					REFIID riid,
					void** ppvObj
					) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;


    /***********************************************************************/
    /*
     * IRMAInputPin methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAInputPin::GetOutputMimeType
     *	Purpose:
     *	    Get the output mime type for this pin
     *	Parameters:
     *	    szMimeType - [out] mime type 
     *	    nMaxLen - [in] max allocated for the string
     */
    STDMETHOD(GetOutputMimeType)	(THIS_
	char* szMimeType, UINT32 nMaxLen) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAInputPin::GetPinProperties/SetPinProperties
     *	Purpose:
     *	    Get/Set the current Pin properties for the Input Pin
     *	    The Input Pin will share a pointer to the Pin properties object
     *	    so any modifications made after SetPinProperties will be shared with the Input Pin
     *	Parameters:
     *	    pPinProperties - [in/out] pointer to an IRMAPinProperties interface
     */
    STDMETHOD(GetPinProperties)	(THIS_
	IRMAPinProperties** ppPinProperties) PURE;
    STDMETHOD(SetPinProperties)	(THIS_
	IRMAPinProperties* pPinProperties) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAInputPin::Encode
     *	Purpose:
     *	    Converts a chunk of input data into requested output type.
     *	Parameters:
     *	    pMediaSample [in] - pointer to an IRMAMediaSample interface
     *			        that contains a sample of input data to
     *				encode
     */
    STDMETHOD(Encode)			(THIS_
					IRMAMediaSample* pMediaSample
					) PURE;
};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAAudioInputPin
 *
 *  Purpose:
 *
 *	Provides specific functionality related to encoding audio
 *
 *  IID_IRMAAudioInputPin:
 *
 *	{FDE92430-C4F7-11d1-9AFD-006097B76F50}
 *	
 *
 */
DEFINE_GUID(IID_IRMAAudioInputPin, 
0xfde92430, 0xc4f7, 0x11d1, 0x9a, 0xfd, 0x0, 0x60, 0x97, 0xb7, 0x6f, 0x50);

#undef INTERFACE
#define INTERFACE IRMAAudioInputPin

DECLARE_INTERFACE_(IRMAAudioInputPin, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					REFIID riid,
					void** ppvObj
					) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;


    /***********************************************************************/
    /*
     * IRMAAudioInputPin methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAAudioInputPin::GetPreferredAudioSourceProperties
     *	Purpose:
     *	    Returns the suggested audio source properties (sample size, sample rate, 
     *	    number of channels), based on the current settings. Only use this function with audio
     *	    sources that can be set dynamically
     *	Parameters:
     *	    pnSamplesPerSec - [out] sample rate (in samples per second)
     *	    pnBitsPerSample - [out] sample size (in bits per sample)
     *	    pnNumChannels - [out] number of channels (1 for mono, 2 for stereo)
     */
    STDMETHOD(GetPreferredAudioSourceProperties)	(THIS_
	UINT32* pnSamplesPerSec, UINT32* pnBitsPerSample, UINT32* pnNumChannels) PURE;


    /************************************************************************
     *	Method:
     *	    IRMAAudioInputPin::GetSuggestedInputSize
     *	Purpose:
     *	    Returns the suggested size of the input data in number of bytes.
     *	Parameters:
     *	    pnInputBytes - [out] number of bytes for suggested input size
     */
    STDMETHOD(GetSuggestedInputSize)	(THIS_
	UINT32* pnInputBytes) PURE;
};


/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAVideoInputPin
 *
 *  Purpose:
 *
 *	Provides specific functionality related to encoding video.
 *
 *  IID_IRMAVideoInputPin:
 *
 *	{0D36B7D0-C2AD-11d1-9AFD-006097B76F50}
 *	
 *
 */
DEFINE_GUID(IID_IRMAVideoInputPin, 
	    0xd36b7d0, 0xc2ad, 0x11d1, 0x9a, 0xfd, 0x0, 0x60, 0x97, 0xb7, 0x6f, 0x50);

#undef INTERFACE
#define INTERFACE IRMAVideoInputPin

DECLARE_INTERFACE_(IRMAVideoInputPin, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					REFIID riid,
					void** ppvObj
					) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;


    /***********************************************************************/
    /*
     * IRMAVideoInputPin methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAVideoInputPin::GetClippingSize
     *	Purpose:
     *	    Returns the clipping values for the video source.
     *	    Clipping occurs for some codecs that are limited by
     *	    a specific modulus.
     *	Parameters:
     *	    pnLeft - [out] left position for the clipped image
     *	    pnTop - [out] top position for the clipped image
     *	    pnWidth - [out] width of the clipped image
     *	    pnHeight - [out] height of the clipped image
     *	Notes:
     *	    Returns the clipping size based on the current settings.
     *	    Clipping can occur on both a cropped and non-cropped image.
     */
    STDMETHOD(GetClippingSize)		(THIS_
	UINT32* pnLeft, UINT32* pnTop, UINT32* pnWidth, UINT32* pnHeight) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAVideoInputPin::GetPreferredInputFrameRate
     *	Purpose:
     *	    Returns the suggested frame rate, based on the current settings. 
     *	    Only use this function with video sources that can have a capture frame rate set dynamically
     *	    Passing in more frames than preferred is fine but will take more CPU time and is not optimal in the real-time encoding case
     *	    Passing in fewer frames than preferred may cause lower quality 
     *	Parameters:
     *	    fFrameRate - [out] frame rate (in frames per second)
     */
    STDMETHOD(GetPreferredInputFrameRate)	(THIS_
	float* pfFrameRate) PURE;
};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAVideoPreviewSinkControl
 *
 *  Purpose:
 *
 *	Sets up a sink to receive encoded video frames
 *
 *  IID_IRMAVideoPreviewSinkControl:
 *
 *  {09D07181-0D45-11d2-89BB-00C0F0177720}
 *	
 *
 */
DEFINE_GUID(IID_IRMAVideoPreviewSinkControl,
	    0x9d07181, 0xd45, 0x11d2, 0x89, 0xbb, 0x0, 0xc0, 0xf0, 0x17, 0x77, 0x20);

#undef INTERFACE
#define INTERFACE IRMAVideoPreviewSinkControl

DECLARE_INTERFACE_(IRMAVideoPreviewSinkControl, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					 REFIID riid,
					 void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;

    /***********************************************************************/
    /*
     * IRMAVideoPreviewSinkControl methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAVideoPreviewSinkControl::AddVideoPreviewSink
     *	Purpose:
     *	    Tells the sink controller to notify the added video preview sink with frames of
     *	    the specified format, encoded for the desired target audience, at the desired interval
     *	Parameters:
     *	    pPreviewSink - [in] pointer to a video preview sink that frames will be passed to
     *	    nFormat - [in] video format (use formats defined in engtypes.h) (currently must use 
     *			   RGB24 or YUV420)
     *	    nInterval - [in] interval between updates (in milliseconds), based on the video 
     *			     timestamps, not real-time. Use 0 to specify that you want update for 
     *			     every frame
     *	    nTarget - [in] target audience for which you want to preview 
     *	Note:	    
     *	    Requesting video formats other than YUV420 will slow the encoding process and is not 
     *	    recommended for real-time encoding
     */
    STDMETHOD(AddVideoPreviewSink)	(THIS_
	IRMAVideoPreviewSink* pPreviewSink, UINT32 nFormat, UINT16 nInterval, UINT32 nTarget) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAVideoPreviewSinkControl::RemoveVideoPreviewSink
     *	Purpose:
     *	    Call this method to remove a video preview sink
     *	Parameters:
     *	    pPreviewSink - [in] pointer to a video preview sink to remove from the list
     */
    STDMETHOD(RemoveVideoPreviewSink)	(THIS_
	IRMAVideoPreviewSink* pPreviewSink) PURE;
};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAVideoPreviewSink
 *
 *  Purpose:
 *
 *	Manages all of the output properties for the clip to be created by the engine
 *	These properties include target destination as well as information to show up in the player
 *
 *  IID_IRMAVideoPreviewSink:
 *
 *  {F6287D11-0D44-11d2-89BB-00C0F0177720}
 *	
 *
 */
DEFINE_GUID(IID_IRMAVideoPreviewSink,
	    0xf6287d11, 0xd44, 0x11d2, 0x89, 0xbb, 0x0, 0xc0, 0xf0, 0x17, 0x77, 0x20);


#undef INTERFACE
#define INTERFACE IRMAVideoPreviewSink

DECLARE_INTERFACE_(IRMAVideoPreviewSink, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					 REFIID riid,
					 void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;

    /***********************************************************************/
    /*
     * IRMAVideoPreviewSink methods
     */
   
    /************************************************************************
     *	Method:
     *	    IRMAVideoPreviewSink::Receive
     *	Purpose:
     *	    After you have registered your video preview sink with an
     *	    IRMAVideoPreviewSinkControl this method will be called every time that 
     *	    a frame has been encoded for the specified target audience and the timestamp 
     *	    is greater than the interval since Receive() was last called
     *
     *	    Receive() will be called during the lifetime of the Encode() call on the Video Input Pin.
     *	    The code calling the video input pin and implementing the video preview sink must be
     *	    re-entrant
     *
     *	    A pointer to the frame will be stored in the IRMAMediaSample. Use GetClippingSize() on 
     *	    the IRMAVideoPin to get the proper height and width of the image. The pointer will ONLY
     *	    be valid for the lifetime of the Receive call. You can copy the frame if you wish, although
     *	    it is noted that because this is during the encode call, more synchronous processing will 
     *	    slow the encoding process and is especially not recommended for real-time encoding
     */
    STDMETHOD(Receive)	(THIS_
	IRMAMediaSample* pVideoFrame) PURE;
};


/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAVideoInputPinFeedback
 *
 *  Purpose:
 *
 *	Enables the caller to get feedback on internal video encoder states during encode
 *
 *  IID_IRMAVideoInputPinFeedback:
 *
 *  {ee8f3950-ebc3-11d2-8546-00c0f01f7817}
 *	
 *
 */
DEFINE_GUID( IID_IRMAVideoInputPinFeedback,
	    0xee8f3950, 0xebc3, 0x11d2, 0x85, 0x46, 0x0, 0xc0, 0xf0, 0x1f, 0x78, 0x17);


#undef INTERFACE
#define INTERFACE IRMAVideoInputPinFeedback

DECLARE_INTERFACE_(IRMAVideoInputPinFeedback, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					 REFIID riid,
					 void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;


    /***********************************************************************/
    /*
     * IRMAVideoInputPinFeedback methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAVideoInputPinFeedback::GetEncodeDecision()
     *	Purpose:
     *	    Tells the caller if a video frame will be encoded or not thus 
     *	    enabling to skip over costly preprocessing
     *	Parameters:
     *	    ulTimestamp - in: timestamp of the next possible frame 
     *	    pbDoEncode - out: pointer to result if the frame should be passed into Encode()
     *	Note:	    
     *	    The timestamp needs to be consistent with the the specified input framerate
     *	    Do not pass in tentative timestamps 
     */
    STDMETHOD(GetEncodeDecision)	(THIS_
	UINT32  ulTimestamp, BOOL*  pbDoEncode) PURE;

};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAVideoFilters
 *
 *  Purpose:
 *
 *	Used to setup filters for pre-processing the video frames prior 
 *	to encoding.
 *
 *  IID_IRMAVideoFilters:
 *
 *
 */
// {4E61EBC1-96BA-11d3-B37B-0050E49EFF27}
DEFINE_GUID(IID_IRMAVideoFilters, 
0x4e61ebc1, 0x96ba, 0x11d3, 0xb3, 0x7b, 0x0, 0x50, 0xe4, 0x9e, 0xff, 0x27);

#undef INTERFACE
#define INTERFACE IRMAVideoFilters

DECLARE_INTERFACE_(IRMAVideoFilters, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					 REFIID riid,
					 void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;


    /***********************************************************************/
    /*
     * IRMAVideoFilters methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAVideoFilters::GetInverseTelecine()
     *	Purpose:
     *	    Used to determine if Inverse-Telecine filter will be used.
     *	Parameters:
     *	    pbInvTel - [out] TRUE if filter is on, FALSE if filter is off
     */
    STDMETHOD(GetInverseTelecine)	(THIS_
		BOOL* pbInvTel) PURE;
    
    /************************************************************************
     *	Method:
     *	    IRMAVideoFilters::SetInverseTelecine()
     *	Purpose:
     *	    Turn on/off use of Inverse-Telecine video filter.
     *	Parameters:
     *	    bInvTel - [in] TRUE to turn on filter, FALSE to turn off filter.
     */
    STDMETHOD(SetInverseTelecine)	(THIS_
		BOOL bInvTel) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAVideoFilters::GetDeinterlace()
     *	Purpose:
     *	    Used to determine if de-interlacing video filter will be used.
     *	Parameters:
     *	    pbDeInterlace - [out] TRUE if filter is on, FALSE if filter is off
     */
    STDMETHOD(GetDeinterlace)	(THIS_
		BOOL* pbDeInt) PURE;
    
    /************************************************************************
     *	Method:
     *	    IRMAVideoFilters::SetDeinterlace()
     *	Purpose:
     *	    Turn on/off use of de-interlacing video filter.
     *	Parameters:
     *	    bDeInterlace - [in] TRUE to turn on filter, FALSE to turn off filter.
     */
    STDMETHOD(SetDeinterlace)	(THIS_
		BOOL bDeInt) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAVideoFilters::GetHQResize()
     *	Purpose:
     *	    Used to determine if High Quality Resize filter will be used.
     *	Parameters:
     *	    pbHQResize - [out] TRUE if filter is on, FALSE if filter is off
     */
    STDMETHOD(GetHQResize)	(THIS_
		BOOL* pbHQResize) PURE;
   
    /************************************************************************
     *	Method:
     *	    IRMAVideoFilters::SetHQResize()
     *	Purpose:
     *	    Turn on/off use of High Quality Resize video filter.
     *	Parameters:
     *	    bHQResize - [in] TRUE to turn on filter, FALSE to turn off filter.
     */
    STDMETHOD(SetHQResize)	(THIS_
		BOOL pHQResize) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAVideoFilters::GetNoiseFilter()
     *	Purpose:
     *	    Used to determine if what type of noise filter will be used.
     *	Parameters:
     *	    pulNoiseFilter - [out]   ENC_VIDEO_NOISE_FILTER_OFF, 
     *				    ENC_VIDEO_NOISE_FILTER_LOW,
     *				    ENC_VIDEO_NOISE_FILTER_HIGH,
     */
    STDMETHOD(GetNoiseFilter)	(THIS_
		UINT32* pulNoiseFilter) PURE;
    
    /************************************************************************
     *	Method:
     *	    IRMAVideoFilters::SetNoiseFilter()
     *	Purpose:
     *	    Turn on/off use of a particular type of noise filter.
     *	Parameters:
     *	    ulNoiseFilter - [in]   ENC_VIDEO_NOISE_FILTER_OFF, 
     *			          ENC_VIDEO_NOISE_FILTER_LOW,
     *			          ENC_VIDEO_NOISE_FILTER_HIGH,
     */
    STDMETHOD(SetNoiseFilter)	(THIS_
		UINT32 ulNoiseFilter) PURE;
};
/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAClipProperties
 *
 *  Purpose:
 *
 *	Manages all of the output properties for the clip to be created by the engine
 *	These properties include target destination as well as information to show up in the player
 *
 *  IID_IRMAClipProperties:
 *
 *  {FF2D8EC1-FFE4-11d1-89B2-00C0F0177720}
 *	
 *
 */
DEFINE_GUID( IID_IRMAClipProperties,
	    0xff2d8ec1, 0xffe4, 0x11d1, 0x89, 0xb2, 0x0, 0xc0, 0xf0, 0x17, 0x77, 0x20);

// {5E7EAD90-0F6C-11d2-B657-00C0F0312253}
DEFINE_GUID( CLSID_IRMAClipProperties,
0x5e7ead90, 0xf6c, 0x11d2, 0xb6, 0x57, 0x0, 0xc0, 0xf0, 0x31, 0x22, 0x53);

#undef INTERFACE
#define INTERFACE IRMAClipProperties

DECLARE_INTERFACE_(IRMAClipProperties, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					 REFIID riid,
					 void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;

    /***********************************************************************/
    /*
     * IRMAClipProperties methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAClipProperties::GetDoOutputFile/SetDoOutputFile
     *	Purpose:
     *	    Get/Set whether or not the engine will create an output file (default: FALSE)
     *	Parameters:
     *	    bDoOutputFile - [in/out] whether or not the engine will create an output file 
     */
    STDMETHOD(GetDoOutputFile)	(THIS_
	BOOL* pbDoOutputFile) PURE;
    STDMETHOD(SetDoOutputFile)	(THIS_
	BOOL bDoOutputFile) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAClipProperties::GetDoOutputServer/SetDoOutputServer
     *	Purpose:
     *	    Get/Set whether or not the engine will create an output stream directly to a server
     *	    This will force the encoding to occur in real-time.
     *	    (default: FALSE)
     *	Parameters:
     *	    bDoOutputServer - [in/out] whether or not the engine will create an output stream 
     *				       to a server 
     */
    STDMETHOD(GetDoOutputServer)	(THIS_
	BOOL* pbDoOutputServer) PURE;
    STDMETHOD(SetDoOutputServer)	(THIS_
	BOOL bDoOutputServer) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAClipProperties::GetOutputFilename/SetOutputFilename
     *	Purpose:
     *	    Get/Set the output filename for the encoding (if bDoOutputFile is TRUE)
     *	Parameters:
     *	    szOutputFile - [in/out] filename
     *	    nMaxLen - [in] max allocated for the string
     */
    STDMETHOD(GetOutputFilename)	(THIS_
	char* szOutputFile, UINT32 nMaxLen) PURE;
    STDMETHOD(SetOutputFilename)	(THIS_
	const char* szOutputFile) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAClipProperties::GetOutputServerInfo/SetOutputServerInfo
     *	Purpose:
     *	    Get/Set the output server info for the encoding (if bDoOutputServer is TRUE)
     *	Parameters:
     *	    szServer - [in/out] name/IP Address of the destination server
     *	    szServerStreamName - [in/out] name of the destination stream on the server
     *	    nPort - [in/out] port of the pn-encoder plugin on the server
     *	    szUsername - [in/out] username for logging in to the server (optional)
     *	    szPassword - [in/out] password for logging in to the server (optional)
     *	    nMaxLen - [in] max allocated for the string
     */
    STDMETHOD(GetOutputServerInfo)	(THIS_
	char* szServer, char* szServerStreamName, UINT32* pnPort,
	char* szUsername, char* szPassword, UINT32 nMaxLen) PURE;
    STDMETHOD(SetOutputServerInfo)	(THIS_
	const char* szServer, const char* szServerStreamName, UINT32 nPort,
	const char* szUsername, const char* szPassword) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAClipProperties::GetTitle/SetTitle
     *	Purpose:
     *	    Get/Set the Title of the clip that will appear in the player clip info 
     *	Parameters:
     *	    szTitle - [in/out] title
     *	    nMaxLen - [in] max allocated for the string
     */
    STDMETHOD(GetTitle)	(THIS_
	char* szTitle, ULONG32 nMaxLen) PURE;
    STDMETHOD(SetTitle)	(THIS_
	const char* szTitle) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAClipProperties::GetAuthor/SetAuthor
     *	Purpose:
     *	    Get/Set the author of the clip that will appear in the player clip info 
     *	Parameters:
     *	    szAuthor - [in/out] author
     *	    nMaxLen - [in] max allocated for the string
     */
    STDMETHOD(GetAuthor)	(THIS_
	char* szAuthor, ULONG32 nMaxLen) PURE;
    STDMETHOD(SetAuthor)	(THIS_
	const char* szAuthor) PURE;
	
    /************************************************************************
     *	Method:
     *	    IRMAClipProperties::GetCopyright/SetCopyright
     *	Purpose:
     *	    Get/Set the copyright of the clip that will appear in the player clip info 
     *	Parameters:
     *	    szCopyright - [in/out] copyright
     *	    nMaxLen - [in] max allocated for the string
     */
    STDMETHOD(GetCopyright)	(THIS_
	char* szCopyright, ULONG32 nMaxLen) PURE;
    STDMETHOD(SetCopyright)	(THIS_
	const char* szCopyright) PURE;
	
    /************************************************************************
     *	Method:
     *	    IRMAClipProperties::GetComment/SetComment
     *	Purpose:
     *	    Get/Set the comment for the clip that will only appear in a dump of the file
     *	Parameters:
     *	    szComment - [in/out] comment
     *	    nMaxLen - [in] max allocated for the string
     */
    STDMETHOD(GetComment)	(THIS_
	char* szComment, ULONG32 nMaxLen) PURE;
    STDMETHOD(SetComment)	(THIS_
	const char* szComment) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAClipProperties::GetSelectiveRecord/SetSelectiveRecord
     *	Purpose:
     *	    Get/Set whether the clip can be recorded by the RealPlayer Plus (default: FALSE)
     *	Parameters:
     *	    bSelectiveRecord - [in/out] whether the clip can be recorded by the RealPlayer 
     *					Plus
     */
    STDMETHOD(GetSelectiveRecord)	(THIS_
	BOOL* pbSelectiveRecord) PURE;
    STDMETHOD(SetSelectiveRecord)	(THIS_
	BOOL bSelectiveRecord) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAClipProperties::GetMobilePlay/SetMobilePlay
     *	Purpose:
     *	    Get/Set whether the clip can be downloaded by mobile players (default: FALSE)
     *	Parameters:
     *	    bMobilePlay - [in/out] whether the clip can be downloaded by mobile players 
     */
    STDMETHOD(GetMobilePlay)	(THIS_
	BOOL* pbMobilePlay) PURE;
    STDMETHOD(SetMobilePlay)	(THIS_
	BOOL bMobilePlay) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAClipProperties::GetPerfectPlay/SetPerfectPlay
     *	Purpose:
     *	    Get/Set whether the player will use perfect play buffering to view this clip
     *	    (all players RealPlayer 4.0 and above automatically use PerfectPlay buffering)
     *	    (default: TRUE)
     *	Parameters:
     *	    bPerfectPlay - [in/out] whether the player will use perfect play buffering to 
     *				    view this clip
     */
    STDMETHOD(GetPerfectPlay)	(THIS_
	BOOL* pbPerfectPlay) PURE;
    STDMETHOD(SetPerfectPlay)	(THIS_
	BOOL bPerfectPlay) PURE;
};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMABroadcastServerProperties
 *
 *  Purpose:
 *
 *	Manages properties of the server to which the RealMedia streams are being broadcast
 *
 *  IID_IRMABroadcastServerProperties:
 *
 *  {C4DC6951-095D-11d3-87CF-00C0F031938B}
 *	
 */
DEFINE_GUID(IID_IRMABroadcastServerProperties, 
	    0xc4dc6951, 0x95d, 0x11d3, 0x87, 0xcf, 0x0, 0xc0, 0xf0, 0x31, 0x93, 0x8b);

#undef INTERFACE
#define INTERFACE IRMABroadcastServerProperties

DECLARE_INTERFACE_(IRMABroadcastServerProperties, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					 REFIID riid,
					 void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;

    /***********************************************************************/
    /*
     * IRMABroadcastServerProperties methods
     */

    /************************************************************************
     *	Method:
     *	    IRMABroadcastServerProperties::GetOutputServerInfo/SetOutputServerInfo
     *	Purpose:
     *	    Get/Set the output server info for the encoding (if bDoOutputServer is TRUE)
     *	Parameters:
     *	    szServer - [in/out] name/IP Address of the destination server
     *	    szServerStreamName - [in/out] name of the destination stream on the server
     *	    nPort - [in/out] port of the pn-encoder plugin on the server
     *	    szUsername - [in/out] username for logging in to the server (optional)
     *	    szPassword - [in/out] password for logging in to the server (optional)
     *	    nMaxLen - [in] max allocated for the string
     */
    STDMETHOD(GetOutputServerInfo)	(THIS_
	char* szServer, char* szServerStreamName, UINT32* pnPort,
	char* szUsername, char* szPassword, UINT32 nMaxLen) PURE;
    STDMETHOD(SetOutputServerInfo)	(THIS_
	const char* szServer, const char* szServerStreamName, UINT32 nPort,
	const char* szUsername, const char* szPassword) PURE;

    /************************************************************************
     *	Method:
     *	    IRMABroadcastServerProperties::GetTransportProtocol/SetTransportProtocol
     *	Purpose:
     *	    Get/Set the transport protocol used to broadcast data to the server
     *	Parameters:
     *	    szTransport [in/out] - transport used to broadcast data to the server
     *	    nMaxLen [in] - max allocated for the string
     */
    STDMETHOD(GetTransportProtocol)	(THIS_
	char* szTransport, UINT32 nMaxLen) PURE;
    STDMETHOD(SetTransportProtocol)	(THIS_
	const char* szTransport) PURE;
};

/****************************************************************************
 * 
 *  Broadcast Server Transport Types:
 *
 *	Used to specify the transport type used between the Producer Core SDK
 *	and the RealServer G2
 *
 *  ENC_TRANSPORTTYPE_UDP:
 *
 *	Recommended Transport mode. 
 *
 *  ENC_TRANSPORTTYPE_TCP:  
 *
 *	Can be used to send data through firewalls to a RealServer G2. This is
 *	only available when connecting to a RealServer G2 6.1
 *
 */
#define ENC_TRANSPORT_PROTOCOL_UDP		"x-real-rdt/udp"
#define ENC_TRANSPORT_PROTOCOL_TCP		"x-pn-tng/tcp"


/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAPinProperties
 *
 *  Purpose:
 *
 *	Manages all of the input properties for the pin. These properties should accurately
 *	describe the source data that will be coming into the pin
 *
 *  IID_IRMAPinProperties:
 *
 *  {F3D20CE1-0611-11d2-89B6-00C0F0177720}
 *	
 *
 */
DEFINE_GUID(IID_IRMAPinProperties,
	    0xf3d20ce1, 0x611, 0x11d2, 0x89, 0xb6, 0x0, 0xc0, 0xf0, 0x17, 0x77, 0x20);

#undef INTERFACE
#define INTERFACE IRMAPinProperties

DECLARE_INTERFACE_(IRMAPinProperties, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					 REFIID riid,
					 void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;

    /***********************************************************************/
    /*
     * IRMAPinProperties methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAPinProperties::GetOutputMimeType
     *	Purpose:
     *	    Get the output mime type for this pin
     *	Parameters:
     *	    szMimeType - [in/out] mime type 
     *	    nMaxLen - [in] max allocated for the string
     */
    STDMETHOD(GetOutputMimeType)	(THIS_
	char* szMimeType, UINT32 nMaxLen) PURE;
};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAAudioPinProperties
 *
 *  Purpose:
 *
 *	Manages all of the input properties for the audio pin. These properties should accurately
 *	describe the source data that will be coming into the pin
 *
 *  IID_IRMAAudioPinProperties:
 *
 *  {F3D20CE2-0611-11d2-89B6-00C0F0177720}
 *	
 *
 */
DEFINE_GUID( IID_IRMAAudioPinProperties, 
	    0xf3d20ce2, 0x611, 0x11d2, 0x89, 0xb6, 0x0, 0xc0, 0xf0, 0x17, 0x77, 0x20);

// {A58E6CC0-0F6C-11d2-B657-00C0F0312253}
DEFINE_GUID( CLSID_IRMAAudioPinProperties,
0xa58e6cc0, 0xf6c, 0x11d2, 0xb6, 0x57, 0x0, 0xc0, 0xf0, 0x31, 0x22, 0x53);

#undef INTERFACE
#define INTERFACE IRMAAudioPinProperties

DECLARE_INTERFACE_(IRMAAudioPinProperties, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					 REFIID riid,
					 void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;

    /***********************************************************************/
    /*
     * IRMAAudioPinProperties methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAAudioPinProperties::GetSampleRate/SetSampleRate
     *	Purpose:
     *	    Get/Set sample rate of the input audio
     *	Parameters:
     *	    nSamplesPerSec - [in/out] sample rate (in samples per second)
     */
    STDMETHOD(GetSampleRate)	(THIS_
	UINT32* pnSamplesPerSec) PURE;
    STDMETHOD(SetSampleRate)	(THIS_
	UINT32 nSamplesPerSec) PURE;   

    /************************************************************************
     *	Method:
     *	    IRMAAudioPinProperties::GetSampleSize/SetSampleSize
     *	Purpose:
     *	    Get/Set sample size of the input audio (must be 8 or 16)
     *	Parameters:
     *	    nBitsPerSample - [in/out] sample size (in bits per sample)
     */
    STDMETHOD(GetSampleSize)	(THIS_
	UINT32* pnBitsPerSample) PURE;
    STDMETHOD(SetSampleSize)	(THIS_
	UINT32 nBitsPerSample) PURE;   

    /************************************************************************
     *	Method:
     *	    IRMAAudioPinProperties::GetNumChannels/SetNumChannels
     *	Purpose:
     *	    Get/Set number of channels in the audio input
     *	Parameters:
     *	    nNumChannels - [in/out] number of channels (1 for mono, 
     *				    2 for stereo)
     */
    STDMETHOD(GetNumChannels)	(THIS_
	UINT32* pnNumChannels) PURE;
    STDMETHOD(SetNumChannels)	(THIS_
	UINT32 nNumChannels) PURE;   
};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAVideoPinProperties
 *
 *  Purpose:
 *
 *	Manages all of the input properties for the video pin. These properties should accurately
 *	describe the source data that will be coming into the pin
 *
 *  IID_IRMAVideoPinProperties:
 *
 *  {F3D20CE3-0611-11d2-89B6-00C0F0177720}
 *	
 *
 */
DEFINE_GUID( IID_IRMAVideoPinProperties,
    0xf3d20ce3, 0x611, 0x11d2, 0x89, 0xb6, 0x0, 0xc0, 0xf0, 0x17, 0x77, 0x20);

// {C0E1F520-0F6C-11d2-B657-00C0F0312253}
DEFINE_GUID( CLSID_IRMAVideoPinProperties,
    0xc0e1f520, 0xf6c, 0x11d2, 0xb6, 0x57, 0x0, 0xc0, 0xf0, 0x31, 0x22, 0x53);

#undef INTERFACE
#define INTERFACE IRMAVideoPinProperties

DECLARE_INTERFACE_(IRMAVideoPinProperties, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					 REFIID riid,
					 void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;

    /************************************************************************
     *
     * IRMAVideoPinProperties methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAVideoPinProperties::GetVideoSize/SetVideoSize
     *	Purpose:
     *	    Get/Set size of the video
     *	Parameters:
     *	    nWidth - [in/out] width of the video
     *	    nHeight - [in/out] height of the video
     */
    STDMETHOD(GetVideoSize)	(THIS_
	UINT32* pnWidth, UINT32* pnHeight) PURE;
    STDMETHOD(SetVideoSize)	(THIS_
	UINT32 nWidth, UINT32 nHeight) PURE;   

    /************************************************************************
     *	Method:
     *	    IRMAVideoPinProperties::GetVideoFormat/SetVideoFormat
     *	Purpose:
     *	    Get/Set format of the input video (must be one of the defined types in engtypes.h)
     *	Parameters:
     *	    nVideoFormat - [in/out] input video format
     */
    STDMETHOD(GetVideoFormat)	(THIS_
	UINT32* pnVideoFormat) PURE;
    STDMETHOD(SetVideoFormat)	(THIS_
	UINT32 nVideoFormat) PURE;   

    /************************************************************************
     *	Method:
     *	    IRMAVideoPinProperties::GetCroppingEnabled/SetCroppingEnabled
     *	Purpose:
     *	    Get/Set whether or not cropping is enabled (default: FALSE) 
     *	Parameters:
     *	    bCropEnabled - [in/out] whether or not to to crop video
     */
    STDMETHOD(GetCroppingEnabled)	(THIS_
	BOOL* pbCropEnabled) PURE;
    STDMETHOD(SetCroppingEnabled)	(THIS_
	BOOL bCropEnabled) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAVideoPinProperties::GetCroppingSize\SetCroppingSize
     *	Purpose:
     *	    Get/Set size of the cropped video image
     *	    (Invalid Settings will cause an error on prepare to encode...)
     *	Parameters:
     *	    nLeft - [in/out] left position for the cropped image
     *	    nTop - [in/out] top position for the cropped image
     *	    nWidth - [in/out] width of the cropped image
     *	    nHeight - [in/out] height of the cropped image
     */
    STDMETHOD(GetCroppingSize)	(THIS_
	UINT32* pnLeft, UINT32* pnTop, UINT32* pnWidth, UINT32* pnHeight) PURE;
    STDMETHOD(SetCroppingSize)	(THIS_
	UINT32 nLeft, UINT32 nTop, UINT32 nWidth, UINT32 nHeight) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAVideoPinProperties::GetFrameRate/SetFrameRate
     *	Purpose:
     *	    Get/Set the desired max frame frame for the video stream
     *	    (default: 15.0)
     *	Parameters:
     *	    fFrameRate - [in/out] max frame rate (in frames per second)
     */    
    STDMETHOD(GetFrameRate)	(THIS_
	float* pfFrameRate) PURE;
    STDMETHOD(SetFrameRate)	(THIS_
	float fFrameRate) PURE;

};


/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAVideoPinProperties2
 *
 *  Purpose:
 *
 *	Manages all of the input properties for the video pin. These properties should accurately
 *	describe the source data that will be coming into the pin
 *
 *  IID_IRMAVideoPinProperties2:
 *
 *  {2EBF90B1-4264-11d4-8728-00D0B7068A6E}
 *	
 *
 */
DEFINE_GUID(IID_IRMAVideoPinProperties2, 
			0x2ebf90b1, 0x4264, 0x11d4, 0x87, 0x28, 0x0, 0xd0, 0xb7, 0x6, 0x8a, 0x6e);


#undef INTERFACE
#define INTERFACE IRMAVideoPinProperties2

DECLARE_INTERFACE_(IRMAVideoPinProperties2, IRMAVideoPinProperties)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					 REFIID riid,
					 void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;

    /************************************************************************
     *
     * IRMAVideoPinProperties2 methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAVideoPinProperties2::GetDisplaySize/SetDisplaySize
     *	Purpose:
     *	    Get/Set the desired display size for the video stream
     *	    If you do not set this, or pass in 0,0, then the input
     *	    size will be used.
     *	    The codec will downsample on encode, or upsample on decode
     *	    depending on the difference between the display size and
     *	    input size
     *	Valid Ranges:
     *	    32 <= width <= 640 
     *	    32 <= height <= 480
     *	    Both width and height must be evenly divisible by 4
     *	    Values that are not valid will be set to the nearest valid number
     *	Parameters:
     *	    nDisplayWidth - [in/out] width to display video
     *	    nDisplayHeight - [in/out] height to display video
     */    
    STDMETHOD(GetDisplaySize)	(THIS_
	UINT32* pnDisplayWidth, UINT32* pnDisplayHeight) PURE;
    STDMETHOD(SetDisplaySize)	(THIS_
	UINT32 nDisplayWidth, UINT32 nDisplayHeight) PURE;

};
  
   
/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAMediaSample
 *
 *  Purpose:
 *
 *	Used to pass timestamped data units from a media source to an input
 *	pin for encoding.
 *
 *  IID_IRMAMediaSample
 *
 *	{DD9A31C0-06F8-11d2-B8B2-006097B76F50}
 *	
 *
 */
DEFINE_GUID( IID_IRMAMediaSample,
0xdd9a31c0, 0x6f8, 0x11d2, 0xb8, 0xb2, 0x0, 0x60, 0x97, 0xb7, 0x6f, 0x50);

DEFINE_GUID( CLSID_IRMAMediaSample, 
0x65ce70c0, 0xf6b, 0x11d2, 0xb6, 0x57, 0x0, 0xc0, 0xf0, 0x31, 0x22, 0x53);

#undef INTERFACE
#define INTERFACE IRMAMediaSample

DECLARE_INTERFACE_(IRMAMediaSample, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					 REFIID riid,
					 void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;

    /***********************************************************************/
    /*
     * IRMAMediaSample methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAMediaSample::SetBuffer
     *	Purpose:
     *	    Sets the media data buffer and timestamp properties in the object.
     *	Parameters:
     *	    pDataBuffer - [in] pointer to media data buffer
     *	    ulBufferSize - [in] size of the buffer in bytes
     *	    ulTimestamp - [in] timestamp value
     *	    unFlags - [in] notes whether this is a sync point
     */
    STDMETHOD(SetBuffer)		(THIS_
					void*	pDataBuffer,
					UINT32	ulBufferSize,
					UINT32	ulTimestamp,
					UINT16	unFlags ) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAMediaSample::GetBuffer
     *	Purpose:
     *	    Get the buffer holding media sample data and related properties.
     *	Parameters:
     *      ppDataBuffer - [out] address of the pointer to media data buffer
     *      pulBufferSize - [out] address of size of the buffer in bytes
     *      pulTimestamp - [out] address of timestamp value
     *      punFlags - [out] address of the flags for the sample
     *	Returns:
     *		PNR_NOT_INITIALIZED if all of the media sample data and related properties have not been set
     */
    STDMETHOD(GetBuffer)		(THIS_
					void**	ppDataBuffer,
					UINT32*	pulBufferSize,
					UINT32*	pulTimestamp,
					UINT16*	punFlags ) PURE;
};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAEventMediaSample
 *
 *  Purpose:
 *
 *	
 *
 *  IID_IRMAEventMediaSample
 *	{AD6BD241-1077-11d2-B5F6-006097B17DCC}
 *		
 *	CLSID_IRMAEventMediaSample
 *	{AD6BD248-1077-11d2-B5F6-006097B17DCC}
 *
 */

DEFINE_GUID(IID_IRMAEventMediaSample, 
0xad6bd241, 0x1077, 0x11d2, 0xb5, 0xf6, 0x0, 0x60, 0x97, 0xb1, 0x7d, 0xcc);
 
DEFINE_GUID(CLSID_IRMAEventMediaSample, 
0xad6bd248, 0x1077, 0x11d2, 0xb5, 0xf6, 0x0, 0x60, 0x97, 0xb1, 0x7d, 0xcc);

#undef INTERFACE
#define INTERFACE IRMAEventMediaSample

DECLARE_INTERFACE_(IRMAEventMediaSample, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					 REFIID riid,
					 void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;

    /***********************************************************************/
    /*
     * IRMAEventMediaSample methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAEventMediaSample::SetTime
     *	Purpose:
     *	    Sets the duration of this event
     *	Parameters:
     *	    nStart - [in] start time of event
     *	    nStop - [in] end time of event
     */
    STDMETHOD(SetTime)(THIS_
			UINT32 nStart,
			UINT32 nStop) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAEventMediaSample::SetAction
     *	Purpose:
     *	    Sets the action of this event. See IRMAEventMediaSample_*
     *	    constants in engtypes.h.
     *	Parameters:
     *	    pString - [in] action of this event
     */
    STDMETHOD(SetAction)(THIS_
    			    UINT16 nType,
			    const char* pString) PURE;
};



/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAImageMapMediaSample
 *
 *  Purpose:
 *
 *	
 *
 *  IID_IRMAImageMapMediaSample
 *	{AD6BD249-1077-11d2-B5F6-006097B17DCC}
 *		
 *	CLSID_IRMAImageMapMediaSample
 *	{AD6BD24A-1077-11d2-B5F6-006097B17DCC}
 *
 */
DEFINE_GUID(IID_IRMAImageMapMediaSample, 
0xad6bd249, 0x1077, 0x11d2, 0xb5, 0xf6, 0x0, 0x60, 0x97, 0xb1, 0x7d, 0xcc);

DEFINE_GUID(CLSID_IRMAImageMapMediaSample, 
0xad6bd24a, 0x1077, 0x11d2, 0xb5, 0xf6, 0x0, 0x60, 0x97, 0xb1, 0x7d, 0xcc);

#undef INTERFACE
#define INTERFACE IRMAImageMapMediaSample

DECLARE_INTERFACE_(IRMAImageMapMediaSample, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)(THIS_
				 REFIID riid,
				 void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)(THIS) PURE;

    STDMETHOD_(UINT32,Release)(THIS) PURE;

    /***********************************************************************/
    /*
     * IRMAImageMapMediaSample methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAImageMapMediaSample::SetMapTime
     *	Purpose:
     *	    Sets the duration of the entire image map. Individual shapes
     *	    may have different durations.
     *	Parameters:
     *	    nStart - [in] start time of image map
     *	    nStop - [in] end time of image map
     */
    STDMETHOD(SetMapTime)(THIS_
			    UINT32 nStart,
			    UINT32 nStop) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAImageMapMediaSample::SetMapSize
     *	Purpose:
     *	    Sets the size of the entire image map. Individual shapes
     *	    will get cropped to this size.
     *	Parameters:
     *	    nLeft - [in] left edge of image map
     *	    nTop - [in] top edge of image map
     *	    nRight - [in] right edge of image map
     *	    nBottom - [in] bottom edge of image map
     */
    STDMETHOD(SetMapSize)(THIS_
			    UINT16 nLeft,
			    UINT16 nTop,
			    UINT16 nRight,
			    UINT16 nBottom) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAImageMapMediaSample::ResetMap
     *	Purpose:
     *	    Reset image map data.
     */

    STDMETHOD(ResetMap)(THIS_) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAImageMapMediaSample::GetShapeHandle
     *	Purpose:
     *	    Returns a shape handle to use when constructing a clickable
     *	    region. This handle is valid as long as the
     *	    IRMAImageMapMediaSample object exists. You can call
     *	    ReleaseShapeHandle to free up these handles if you like, but
     *	    they will all get destroyed along with the main media sample
     *	    object anyway. 
     */
    STDMETHOD_(UINT32,GetShapeHandle)(THIS) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAImageMapMediaSample::ReleaseShapeHandle
     *	Purpose:
     *	    Frees a shape allocated by GetShapeHandle. Most likely not
     *	    needed, but available if there's a need to create a bunch of
     *	    handles for some reason or another and the memory hit is too
     *	    great to wait until the parent IRMAImageMediaSample object goes
     *	    away. 
     *	Parameters:
     *	    nHandle - [in] shape handle
     */
    STDMETHOD(ReleaseShapeHandle)(THIS_
				    UINT32 nHandle) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAImageMapMediaSample::ResetShapeHandle
     *	Purpose:
     *	    Resets a shape to its default state, i.e. wipes out all vertices,
     *	    type info, etc. 
     *	Parameters:
     *	    nHandle - [in] shape handle
     */
    STDMETHOD(ResetShapeHandle)(THIS_
				UINT32 nHandle) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAImageMapMediaSample::SetShapeType
     *	Purpose:
     *	    Sets the type of shape. See IRMAImageMapMediaSample_* constants
     *	    in engtypes.h.
     *	Parameters:
     *	    nHandle - [in] shape handle
     *	    nType - [in] shape type
     */
    STDMETHOD(SetShapeType)(THIS_
			    UINT32 nHandle,
			    UINT16 nType) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAImageMapMediaSample::SetShapeCoordinates
     *	Purpose:
     *	    Sets the coordinates associated with the shape. nArraySize is
     *	    the number of integers stored in pnCoordArray. 
     *	Parameters:
     *	    nHandle - [in] shape handle
     *	    nArraySize - [in] number of integers in array
     *	    pnCoordArray - [in] coordinate array
     */
    STDMETHOD(SetShapeCoordinates)(THIS_
				    UINT32 nHandle,
				    UINT16 nArraySize,
				    UINT16* pnCoordArray) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAImageMapMediaSample::AddShapeCoordinate
     *	Purpose:
     *	    Allows client to construct a coordinate list one element at a
     *	    time instead of assembling all of them into an array.
     *	Parameters:
     *	    nHandle - [in] shape handle
     *	    nCoordinate - [in] coordinate
     */
    STDMETHOD(AddShapeCoordinate)(THIS_
				    UINT32 nHandle,
				    UINT16 nCoordinate) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAImageMapMediaSample::SetShapeActionPlayFile
     *	Purpose:
     *	    Play a new file in the current player. pFile has the URL
     *	    pointing to it.
     *	Parameters:
     *	    nHandle - [in] shape handle
     *	    pFile - [in] name of file
     */
    STDMETHOD(SetShapeActionPlayFile)(THIS_
					UINT32 nHandle,
					const char* pFile) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAImageMapMediaSample::SetShapeActionBrowse
     *	Purpose:
     *	    Send browser to pURL.
     *	Parameters:
     *	    nHandle - [in] shape handle
     *	    pURL - [in] name of URL
     */
    STDMETHOD(SetShapeActionBrowse)(THIS_
				    UINT32 nHandle,
				    const char* pURL) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAImageMapMediaSample::SetShapeActionSeek
     *	Purpose:
     *	    Seek to nSeekTime milliseconds in the currently playing file.
     *	Parameters:
     *	    nHandle - [in] shape handle
     *	    nSeekTime - [in] seek time for action
     */
    STDMETHOD(SetShapeActionSeek)(THIS_
				    UINT32 nHandle,
				    UINT32 nSeekTime) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAImageMapMediaSample::SetShapeAltText
     *	Purpose:
     *	    Sets the text which appears in the status bar when the mouse is
     *	    moved over the hot spot.
     *	Parameters:
     *	    nHandle - [in] shape handle
     *	    pAltText - [in] text for status bar
     */
    STDMETHOD(SetShapeAltText)(THIS_
				UINT32 nHandle,
				const char* pAltText) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAImageMapMediaSample::SetShapeDuration
     *	Purpose:
     *	    sets the start and stop time of the individual shape. This
     *	    duration is clipped to the duration of the overall map.
     *	Parameters:
     *	    nHandle - [in] shape handle
     *	    nStartTime - [in] start time of shape
     *	    nStartTime - [in] end time of shape
     */
    STDMETHOD(SetShapeDuration)(THIS_
				UINT32 nHandle,
				UINT32 nStartTime,
				UINT32 nStopTime) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAImageMapMediaSample::AddShape
     *	Purpose:
     *	    adds a shape to the image map. If the client hasn't set up the
     *	    shape completely (i.e. no action set) or set it up incorrectly
     *	    (i.e. invalid number of coordinates) then an error will occur
     *	    here. 
     *	Parameters:
     *	    nHandle - [in] shape handle
     */
    STDMETHOD(AddShape)(THIS_
			UINT32 nHandle) PURE;
};

typedef enum
{
    ENCODE_NO_ANALYSIS = 0,
    DO_ANALYZE,
    ENCODE_WITH_ANALYSIS
} ENCODE_ANALYSIS_MODE;

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAVideoAnalysis
 *
 *  Purpose:
 *
 *	Manages state for setting the video analysis modes
 *
 *  IID_IRMAVideoAnalysis:
 *
 *  {F67F1261-3C8A-11d3-87F4-00C0F031938B}
 *	
 *
 */
DEFINE_GUID(IID_IRMAVideoAnalysis, 
    0xf67f1261, 0x3c8a, 0x11d3, 0x87, 0xf4, 0x0, 0xc0, 0xf0, 0x31, 0x93, 0x8b);


#undef INTERFACE
#define INTERFACE IRMAVideoAnalysis

DECLARE_INTERFACE_(IRMAVideoAnalysis, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					 REFIID riid,
					 void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;

    /************************************************************************
     *
     * IRMAVideoAnalysis methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAVideoAnalysis::GetAnalysisMode/SetAnalysisMode
     *	Purpose:
     *	    Get/Set the analysis mode for 2-pass video encoding.
     *	Parameters:
     *	    nAnalysisMode - [in/out] encode analysis mode
     *			    ENCODE_NO_ANALYSIS - regular encoding mode
     *			    DO_ANALYZE - perform analysis of video (1st pass)
     *			    ENCODE_WITH_ANALYSIS - encode using results of analysis (2nd pass)
     *	Notes:
     *	    For 2-pass encoding, you must set the analysis mode before 
     *	    each PrepareToEncode() call. For the first pass, in which 
     *	    the video is analyzed, use the DO_ANALYZE mode. For the second pass,
     *	    in which the video is encoded using the results of the analysis,
     *	    use the ENCODE_WITH_ANALYSIS mode. For regular encoding use the 
     *	    ENCODE_NO_ANALYSIS mode to turn off 2-pass encoding.
     *
     *	    2-pass encoding is not supported for real-time encoding. During real-time 
     *	    encoding, this mode will be ignored and ENCODE_NO_ANALYZE will be used.
     */
    STDMETHOD(GetAnalysisMode)	(THIS_
	ENCODE_ANALYSIS_MODE* pnAnalysisMode) PURE;
    STDMETHOD(SetAnalysisMode)	(THIS_
	ENCODE_ANALYSIS_MODE nAnalysisMode) PURE;   
};


/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAWallclock
 *
 *  Purpose:
 *
 *	Enable/disable wallclock.  Wallclock is used to for synchronize live 
 *	broadcasts from different machines within a single SMIL presentation.  Please
 *	see the RealSystem G2 Production Guide for more details on wallclock.
 *
 *  IID_IRMAWallclock:
 *
 *  {{CDB34BB1-3801-11d4-968F-00D0B7068A6E}
 *	
 *
 */
DEFINE_GUID(IID_IRMAWallclock, 
    0xcdb34bb1, 0x3801, 0x11d4, 0x96, 0x8f, 0x0, 0xd0, 0xb7, 0x6, 0x8a, 0x6e);

#undef INTERFACE
#define INTERFACE IRMAWallclock

DECLARE_INTERFACE_(IRMAWallclock, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					 REFIID riid,
					 void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;

    /************************************************************************
     *
     * IRMAWallclock methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAWallclock::GetDoWallclock/SetDoWallclock
     *	Purpose:
     *	    Get/Set whether wallclock is enabled.
     *	Notes:
     *	    Can't be set after calling PrepareToEncode (until DoneEncoding 
	 *		or CancelEncoding are called).  By default, wallclock is
	 *		disabled.
     */
    STDMETHOD(GetDoWallclock)	(THIS_
		BOOL* pbDoWallclock) PURE;
    STDMETHOD(SetDoWallclock)	(THIS_
		BOOL bDoWallclock) PURE;   

    /************************************************************************
     *	Method:
     *	    IRMAWallclock::GetBaseWallclockTime/SetBaseWallclockTime
     *	Purpose:
     *	    Get/Set the base wallclock time.
     *	Notes:
     *	    Can be set before or after PrepareToEncode.  Can only be set 
	 *		once per encoding session.  If wallclock is enabled, all samples 
	 *		passed into the input pins will be discarded until the base
	 *		wallclock time is set.
     */
    STDMETHOD(GetBaseWallclockTime)	(THIS_
		UINT32* pulBaseWallclockTime) PURE;
    STDMETHOD(SetBaseWallclockTime)	(THIS_
		UINT32 ulBaseWallclockTime) PURE;

};


#endif //_RMBLDENG_H_
