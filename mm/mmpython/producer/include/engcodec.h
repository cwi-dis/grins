/****************************************************************************
 * 
 *  $Id$
 *
 *  engcodec.h
 *
 *  Copyright ©1998 RealNetworks.
 *  All rights reserved.
 *
 *  http://www.real.com/devzone
 *
 *  This program contains proprietary information of RealNetworks, Inc., 
 *  and is licensed subject to restrictions on use and distribution.
 *
 *
 *  Definition of the interfaces for the Codec Manager. Use these interfaces
 *  to access information about the codecs.
 *
 */

#ifndef _ENGCODEC_H_
#define _ENGCODEC_H_

typedef _INTERFACE IUnknown			IUnknown;
typedef _INTERFACE IRMACodecInfo		IRMACodecInfo;
typedef _INTERFACE IRMACodecInfo2		IRMACodecInfo2;
typedef _INTERFACE IRMAAudioCodecInfo		IRMAAudioCodecInfo;
typedef _INTERFACE IRMAVideoCodecInfo		IRMAVideoCodecInfo;
typedef _INTERFACE IRMACodecInfoManager		IRMACodecInfoManager;

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMACodecInfo
 *
 *  Purpose:
 *
 *	Provides information about a specific codec.
 *	Query for the IRMAAudioCodecInfo and IRMAVideoCodecInfo interfaces if you need 
 *	datatype-specific information.
 *
 *  IRMACodecInfo:
 *
 *	{6E174651-EB89-11d1-899B-00C0F0177720}
 *
 */
DEFINE_GUID(IID_IRMACodecInfo, 
	    0x6e174651, 0xeb89, 0x11d1, 0x89, 0x9b, 0x0, 0xc0, 0xf0, 0x17, 0x77, 0x20);

/*
 *  You access objects that support this interface from the IRMACodecInfoManager object
 *  Either by requesting the audio or video codec info arrays or by using the 
 *  GetCodecInfo function with a codec cookie
 */
#define CLSID_IRMACodecInfo IID_IRMACodecInfo

#undef  INTERFACE
#define INTERFACE   IRMACodecInfo

DECLARE_INTERFACE_(IRMACodecInfo, IUnknown)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)	(THIS) PURE;

    STDMETHOD_(UINT32,Release)	(THIS) PURE;

    /***************************************
     *
     *	IRMACodecInfo methods
     */

    /************************************************************************
     *	Method:
     *	    IRMACodecInfo::GetCodecCookie
     *	Purpose:
     *	    Get the codec cookie for this codec.
     *	Parameters:
     *	    ccCodec - [out] codec cookie
     */
    STDMETHOD(GetCodecCookie)	(THIS_
				REF(PNCODECCOOKIE) ccCodec) PURE;
    
    /************************************************************************
     *	Method:
     *	    IRMACodecInfo::GetCodecName
     *	Purpose:
     *	    Get the name of the codec.
     *	Parameters:
     *	    szName - [out] char buffer to hold the codec name
     *	    nMaxLen - [in] length of char buffer szName
     */
    STDMETHOD(GetCodecName)	(THIS_
				char* szName, UINT32 nMaxLen) PURE;

    /************************************************************************
     *	Method:
     *	    IRMACodecInfo::GetOldestCompatiblePlayer
     *	Purpose:
     *	    Get the oldest player version which supports this codec.
     *	Parameters:
     *	    uiPlayerVer - [out] player version
     */
    STDMETHOD(GetOldestCompatiblePlayer)	(THIS_
				REF(UINT32) uiPlayerVer) PURE;

    /************************************************************************
     *	Method:
     *	    IRMACodecInfo::GetCodecForVersion
     *	Purpose:
     *	    Get a codec cookie for a comparable codec which supports the
     *	    requested player version (should be lower than a version which
     *	    this coded supports).
     *	Parameters:
     *	    uiPlayerVer - [in] player version
     *	    ccCodec - [out] codec cookie
     */
    STDMETHOD(GetCodecForVersion)	(THIS_
				UINT32 uiPlayerVer, REF(PNCODECCOOKIE) ccCodec) PURE;

};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMACodecInfo2
 *
 *  Purpose:
 *
 *	Provides information about a specific codec.
 *	Query for the IRMAAudioCodecInfo and IRMAVideoCodecInfo interfaces if you need 
 *	datatype-specific information.
 *
 *  IRMACodecInfo2:
 *
 *  {1178DDC1-FE75-11d2-87CB-00C0F031938B}
 *
 */
DEFINE_GUID(IID_IRMACodecInfo2, 
	    0x1178ddc1, 0xfe75, 0x11d2, 0x87, 0xcb, 0x0, 0xc0, 0xf0, 0x31, 0x93, 0x8b);
/*
 *  You access objects that support this interface from the IRMACodecInfoManager object
 *  Either by requesting the audio or video codec info arrays or by using the 
 *  GetCodecInfo function with a codec cookie
 */
#define CLSID_IRMACodecInfo2 IID_IRMACodecInfo2

#undef  INTERFACE
#define INTERFACE   IRMACodecInfo2

DECLARE_INTERFACE_(IRMACodecInfo2, IRMACodecInfo)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)	(THIS) PURE;

    STDMETHOD_(UINT32,Release)	(THIS) PURE;

    /***************************************
     *
     *	IRMACodecInfo2 methods
     */

    /************************************************************************
     *	Method:
     *	    IRMACodecInfo22::GetDescription
     *	Purpose:
     *	    Get the text description of the video codec
     *	Parameters:
     *	    szName - [out] char buffer to hold the description
     *	    nMaxLen - [in] length of char buffer szName
     */
    STDMETHOD(GetDescription)	(THIS_
				char* szDescription, UINT32 nMaxLen) PURE;
};


/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAAudioCodecInfo
 *
 *  Purpose:
 *
 *	information about a specific audio codec 
 *
 *  IRMAAudioCodecInfo
 *
 *  {2CE09851-F03F-11d1-89A1-00C0F0177720}
 *
 */
DEFINE_GUID(IID_IRMAAudioCodecInfo,
	    0x2ce09851, 0xf03f, 0x11d1, 0x89, 0xa1, 0x0, 0xc0, 0xf0, 0x17, 0x77, 0x20);


/*
 *  You access objects that support this interface from the IRMACodecInfoManager object
 *  Either by requesting the audio codec info array or by using the 
 *  GetCodecInfo function with a codec cookie
 */
#define CLSID_IRMAAudioCodecInfo IID_IRMAAudioCodecInfo

#undef  INTERFACE
#define INTERFACE   IRMAAudioCodecInfo

DECLARE_INTERFACE_(IRMAAudioCodecInfo, IUnknown)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)	(THIS) PURE;

    STDMETHOD_(UINT32,Release)	(THIS) PURE;

    /****************************************
     *
     *	IRMAAudioCodecInfo methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAAudioCodecInfo::GetBitrate
     *	Purpose:
     *	    Get the bitrate of the audio codec (in bits per second).
     *	Parameters:
     *	    uiBitrate - [out] bitrate
     */
    STDMETHOD(GetBitrate)	(THIS_
				REF(UINT32) uiBitrate) PURE;
    
    /************************************************************************
     *	Method:
     *	    IRMAAudioCodecInfo::GetNumChannels
     *	Purpose:
     *	    Get the number of channels for the audio codec (1 for mono, 
     *	    2 for stereo). (note: if stereo, then two channels in the
     *	    audio input are required.)
     *	Parameters:
     *	    uiNumChannels - [out] number of channels
     */
    STDMETHOD(GetNumChannels)	(THIS_
				REF(UINT32) uiNumChannels) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAAudioCodecInfo::GetSampleRate
     *	Purpose:
     *	    Get the sample rate of the audio codec (in samples per 
     *	    second)
     *	Parameters:
     *	    uiSamplesPerSec - [out] sample rate
     */
    STDMETHOD(GetSampleRate)	(THIS_
				REF(UINT32) uiSamplesPerSec) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAAudioCodecInfo::GetSampleSize
     *	Purpose:
     *	    Get the sample size of the audio codec (either 8 or 16)
     *	Parameters:
     *	    uiBitsPerSample - [out] sample size
     */
    STDMETHOD(GetSampleSize)	(THIS_
				REF(UINT32) uiBitsPerSample) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAAudioCodecInfo::GetDescription
     *	Purpose:
     *	    Get the text description of the audio codec
     *	Parameters:
     *	    szName - [out] char buffer to hold the description
     *	    nMaxLen - [in] length of char buffer szName
     */
    STDMETHOD(GetDescription)	(THIS_
				char* szDescription, UINT32 nMaxLen) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAAudioCodecInfo::GetFrequencyResponse
     *	Purpose:
     *	    Get the frequency response of the audio codec (in Hertz)
     *	Parameters:
     *	    nFrequencyResponse - [out] frequency response (in Hertz)
     */
    STDMETHOD(GetFrequencyResponse)	(THIS_
				REF(UINT32) nFrequencyResponse) PURE;
};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAVideoCodecInfo
 *
 *  Purpose:
 *
 *	information about a specific video codec 
 *
 *  IRMAVideoCodecInfo
 *
 *  {2CE09852-F03F-11d1-89A1-00C0F0177720}
 *
 */
DEFINE_GUID(IID_IRMAVideoCodecInfo,
	    0x2ce09852, 0xf03f, 0x11d1, 0x89, 0xa1, 0x0, 0xc0, 0xf0, 0x17, 0x77, 0x20);


/*
 *  You access objects that support this interface from the IRMACodecInfoManager object
 *  Either by requesting the video codec info array or by using the 
 *  GetCodecInfo function with a codec cookie
 */
#define CLSID_IRMAVideoCodecInfo IID_IRMAVideoCodecInfo

#undef  INTERFACE
#define INTERFACE   IRMAVideoCodecInfo

DECLARE_INTERFACE_(IRMAVideoCodecInfo, IUnknown)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)	(THIS) PURE;

    STDMETHOD_(UINT32,Release)	(THIS) PURE;

    /********************************************
     *
     *	IRMAVideoCodecInfo methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAVideoCodecInfo::GetCodecModulus
     *	Purpose:
     *	    Get the height and width modulo by which the height and width 
     *	    must be evenly divisible (the build engine will properly clip
     *	    the input if necessary).
     *	Parameters:
     *	    uiWidthModulus - [out] width
     *	    uiWidthModulus - [out] height
     */
    STDMETHOD(GetCodecModulus)	(THIS_
				REF(UINT32) uiWidthModulus, 
				REF(UINT32) uiHeightModulus) PURE;    
};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMACodecInfoManager
 *
 *  Purpose:
 *
 *  manager of the codec information which is used to display and select codecs for various target
 *  audiences or templates
 *
 *  IRMACodecInfoManager
 *
 *  {2212A761-E466-11d1-909C-C449BB028852}
 *
 */
DEFINE_GUID(IID_IRMACodecInfoManager, 
    0x2212a761, 0xe466, 0x11d1, 0x90, 0x9c, 0xc4, 0x49, 0xbb, 0x2, 0x88, 0x52);

// {C0E1F522-0F6C-11d2-B657-00C0F0312253}
DEFINE_GUID( CLSID_IRMACodecInfoManager,
    0xc0e1f522, 0xf6c, 0x11d2, 0xb6, 0x57, 0x0, 0xc0, 0xf0, 0x31, 0x22, 0x53);

#undef  INTERFACE
#define INTERFACE   IRMACodecInfoManager

DECLARE_INTERFACE_(IRMACodecInfoManager, IUnknown)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)	(THIS) PURE;

    STDMETHOD_(UINT32,Release)	(THIS) PURE;

    /*************************************************
     *
     *	IRMACodecInfoManager methods
     */

    /************************************************************************
     *	Method:
     *	    IRMACodecInfoManager::GetAudioCodecEnum
     *	Purpose:
     *	    Get an IUnknown enumerator of all of the audio codecs
     *	    (IRMAAudioCodecInfo).
     *	Parameters:
     *	    pAudioCodecEnum - [out] audio codecs enumerator
     */
    STDMETHOD(GetAudioCodecEnum)    (THIS_
				REF(IUnknown*) pAudioCodecEnum) PURE;

    /************************************************************************
     *	Method:
     *	    IRMACodecInfoManager::GetVideoCodecEnum
     *	Purpose:
     *	    Get an IUnknown enumerator of all of the video codecs
     *	    (IRMAVideoCodecInfo).
     *	Parameters:
     *	    pVideoCodecEnum - [out] video codecs enumerator
     */
    STDMETHOD(GetVideoCodecEnum)    (THIS_
				REF(IUnknown*) pVideoCodecEnum) PURE;

    /************************************************************************
     *	Method:
     *	    IRMACodecInfoManager::GetCodecInfo
     *	Purpose:
     *	    Get the IRMACodecInfo for the specified codec cookie.
     *	Parameters:
     *	    ccCodec - [in] codec cookie
     *	    pCodecInfo - [out] info for the specified codec cookie
     */
    STDMETHOD(GetCodecInfo)	(THIS_
				PNCODECCOOKIE ccCodec, REF(IRMACodecInfo*) pCodecInfo) PURE;
};

#endif // _ENGCODEC_H_
