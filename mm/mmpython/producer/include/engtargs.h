/****************************************************************************
 * 
 *  $Id$
 *
 *  engtargs.h
 *
 *  Copyright ©1998-2000 RealNetworks.
 *  All rights reserved.
 *
 *  http://www.real.com/devzone
 *
 *  This program contains proprietary information of RealNetworks, Inc., 
 *  and is licensed subject to restrictions on use and distribution.
 *
 *
 *  Definition of the interfaces for the target audience settings.
 *
 */

#ifndef _ENGTARGS_H_
#define _ENGTARGS_H_

typedef _INTERFACE IUnknown			IUnknown;
typedef _INTERFACE IRMATargetSettings		IRMATargetSettings;
typedef _INTERFACE IRMABasicTargetSettings	IRMABasicTargetSettings;
typedef _INTERFACE IRMATargetAudienceInfo	IRMATargetAudienceInfo;
typedef _INTERFACE IRMATargetAudienceInfo2	IRMATargetAudienceInfo2;
typedef _INTERFACE IRMATargetAudienceManager	IRMATargetAudienceManager;

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMATargetSettings
 *
 *  Purpose:
 *
 *	Base interface for the target settings objects
 *	Use this to figure out if target settings is basic or advanced
 *
 *  IRMATargetSettings
 *
 *	{FF8DA4C1-00BC-11d2-89B3-00C0F0177720}
 *
 */
DEFINE_GUID(IID_IRMATargetSettings,
	    0xff8da4c1, 0xbc, 0x11d2, 0x89, 0xb3, 0x0, 0xc0, 0xf0, 0x17, 0x77, 0x20);

#undef  INTERFACE
#define INTERFACE   IRMATargetSettings

DECLARE_INTERFACE_(IRMATargetSettings, IUnknown)
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
     * IRMATargetSettings methods
     */

    /************************************************************************
     *	Method:
     *	    IRMATargetSettings::GetType
     *	Purpose:
     *	    Returns the type of this target settings object, defined in engtypes.h
     *	Parameters:
     *	    pnType - [out] type of this target settings object
     */
    STDMETHOD(GetType)		(THIS_
	UINT32* pnType) PURE;
};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMABasicTargetSettings
 *
 *  Purpose:
 *
 *	Base interface for the target settings objects
 *	Use this to figure out if target settings is basic or advanced
 *
 *  IRMABasicTargetSettings
 *
 *  {FF8DA4C2-00BC-11d2-89B3-00C0F0177720}
 *
 */
DEFINE_GUID(IID_IRMABasicTargetSettings,
	    0xff8da4c2, 0xbc, 0x11d2, 0x89, 0xb3, 0x0, 0xc0, 0xf0, 0x17, 0x77, 0x20);

// {C0E1F521-0F6C-11d2-B657-00C0F0312253}
DEFINE_GUID( CLSID_IRMABasicTargetSettings,
    0xc0e1f521, 0xf6c, 0x11d2, 0xb6, 0x57, 0x0, 0xc0, 0xf0, 0x31, 0x22, 0x53);

#undef  INTERFACE
#define INTERFACE   IRMABasicTargetSettings

DECLARE_INTERFACE_(IRMABasicTargetSettings, IUnknown)
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
     * IRMABasicTargetSettings methods
     */

    /************************************************************************
     *	Method:
     *	    IRMABasicTargetSettings::AddTargetAudience/RemoveTargetAudience
     *	Purpose:
     *	    Add/remove target audience IDs from list the currently selected 
     *	    target audiences (default: ENC_TARGET_28_MODEM, ENC_TARGET_56_MODEM)
     *	Parameters:
     *	    nTargetAudienceID - [in] ID of the target audience to add or remove.
     */
    STDMETHOD(AddTargetAudience)	(THIS_
	UINT32 nTargetAudienceID) PURE;
    STDMETHOD(RemoveTargetAudience)	(THIS_
	UINT32 nTargetAudienceID) PURE;

    /************************************************************************
     *	Method:
     *	    IRMABasicTargetSettings::RemoveAllTargetAudiences
     *	Purpose:
     *	    Remove all target audiences from the currently selected list
     */
    STDMETHOD(RemoveAllTargetAudiences)	(THIS) PURE;

    /************************************************************************
     *	Method:
     *	    IRMABasicTargetSettings::GetTargetAudienceCount
     *	Purpose:
     *	    Get the number of currently selected target audiences
     *	Parameters:
     *	    pnCountTargetAudiences - [in] number of currently selected 
     *					  target audiences
     */
    STDMETHOD(GetTargetAudienceCount)	(THIS_
	UINT32* pnCountTargetAudiences) PURE;

    /************************************************************************
     *	Method:
     *	    IRMABasicTargetSettings::GetNthTargetAudience
     *	Purpose:
     *	    get the Nth target audience in the list
     *	Parameters:
     *	    index - [in] the position in the list you want the target 
     *			 audience for (should be between 0 and 
     *			 (GetCount()-1))
     *	    pnTargetAudienceID - [out] the ID for that position
     */
    STDMETHOD(GetNthTargetAudience)	(THIS_
	UINT32 index, UINT32* pnTargetAudienceID) PURE;

    /************************************************************************
     *	Method:
     *	    IRMABasicTargetSettings::GetAudioContent/SetAudioContent
     *	Purpose:
     *	    Get/Set selected audio content type (default: ENC_AUDIO_CONTENT_VOICE)
     *	Parameters:
     *	    nAudioContent - [in/out] selected audio content type
     */
    STDMETHOD(GetAudioContent)	(THIS_
	UINT32* pnAudioContent) PURE;
    STDMETHOD(SetAudioContent)	(THIS_
	UINT32 nAudioContent) PURE;   
	
    /************************************************************************
     *	Method:
     *	    IRMABasicTargetSettings::GetVideoQuality/SetVideoQuality
     *	Purpose:
     *	    Get/Set selected video quality setting (default: ENC_VIDEO_QUALITY_NORMAL)
     *	Parameters:
     *	    nVideoQuality - [in/out] selected video quality setting
     */
    STDMETHOD(GetVideoQuality)	(THIS_
	UINT32* pnVideoQuality) PURE;
    STDMETHOD(SetVideoQuality)	(THIS_
	UINT32 nVideoQuality) PURE;   
	
    /************************************************************************
     *	Method:
     *	    IRMABasicTargetSettings::GetPlayerCompatibility/SetPlayerCompatibility
     *	Purpose:
     *	    Get/Set oldest desired player version to support with the encoding 
     *	    range: (2 = RealAudio Player 2.0, 6 = G2 RealPlayer) (default: G2 RealPlayer)
     *	Parameters:
     *	    nPlayerVer - [in/out] oldest desired player version
     */
    STDMETHOD(GetPlayerCompatibility)	(THIS_
	UINT32* pnPlayerVer) PURE;
    STDMETHOD(SetPlayerCompatibility)	(THIS_
	UINT32 nPlayerVer) PURE;   

    /************************************************************************
     *	Method:
     *	    IRMABasicTargetSettings::GetEmphasizeAudio/SetEmphasizeAudio
     *	Purpose:
     *	    Get/Set the emphasis for switching down when under duress conditions, if 
     *	    Emphasize Audio is true, client players will switch to a lower video quality before
     *	    switching to a lower audio quality (default: TRUE) 
     *	Parameters:
     *	    bEmphasizeAudio - [in/out] whether or not to emphasize audio while switching
     */
    STDMETHOD(GetEmphasizeAudio)	(THIS_
	BOOL* pbEmphasizeAudio) PURE;
    STDMETHOD(SetEmphasizeAudio)	(THIS_
	BOOL bEmphasizeAudio) PURE;

    /************************************************************************
     *	Method:
     *	    IRMABasicTargetSettings::GetDoAudioOnlyMultimedia/SetDoAudioOnlyMultimedia
     *	Purpose:
     *	    Get/Set whether or not settings manager uses the audio only settings or multimedia 
     *	    settings to select the audio codecs for Audio Only files. The Audio Only settings should 
     *	    be set to audio codecs which will maximize the available bandwidth for the target 
     *	    audience. The multimedia settings allow the user to specify codecs that do not maximize 
     *	    the available bandwidth for the target audience so that the audio files can be played in 
     *	    conjunction with RealPix or RealFlash which will use the rest of the bandwidth for the 
     *	    target audience. (default: FALSE)
     *	Parameters:
     *	    bDoMultimedia - [in/out] whether or not to use multimedia settings for audio only clips
     */
    STDMETHOD(GetDoAudioOnlyMultimedia)	(THIS_
	BOOL* pbDoMultimedia) PURE;
    STDMETHOD(SetDoAudioOnlyMultimedia)	(THIS_
	BOOL bDoMultimedia) PURE;
};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMATargetAudienceInfo
 *
 *  Purpose:
 *
 *	Properties interface for an individual target audience.
 *
 *  Notes:
 *
 *	To access the object that supports this interface, call
 *	IRMATargetAudienceManager::GetTargetAudienceInfo().
 *
 *  IRMATargetAudienceInfo
 *
 *  {FF8DA4C3-00BC-11d2-89B3-00C0F0177720}
 *
 */
DEFINE_GUID(IID_IRMATargetAudienceInfo,
	    0xff8da4c3, 0xbc, 0x11d2, 0x89, 0xb3, 0x0, 0xc0, 0xf0, 0x17, 0x77, 0x20);

#undef  INTERFACE
#define INTERFACE   IRMATargetAudienceInfo

DECLARE_INTERFACE_(IRMATargetAudienceInfo, IUnknown)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
	REFIID riid,
	void** ppvObj) PURE;
    
    STDMETHOD_(UINT32,AddRef)	(THIS) PURE;
    
    STDMETHOD_(UINT32,Release)	(THIS) PURE;
    
    /*********************************************
     *
     *	IRMATargetAudienceInfo methods
     */

    /************************************************************************
     *	Method:
     *	    IRMATargetAudienceInfo::GetTargetAudienceID
     *	Purpose:
     *	    Get target audience ID of this object
     *	Parameters:
     *	    ulID - [out] target audience ID
     */
    STDMETHOD(GetTargetAudienceID)	(THIS_
	REF(UINT32) ulID) PURE;

    /************************************************************************
     *	Method:
     *	    IRMATargetAudienceInfo::GetTargetAudienceName
     *	Purpose:
     *	    Get screen name of this target audience object.
     *	Parameters:
     *	    szName - [out] char buffer to hold the target audience name
     *	    nMaxLen - [in] length of char buffer szName
     */
    STDMETHOD(GetTargetAudienceName)	(THIS_
	char* szName, UINT32 nMaxLen) PURE;
    
    /************************************************************************
     *	Method:
     *	    IRMATargetAudienceInfo::GetTargetBitrate/SetTargetBitrate
     *	Purpose:
     *	    Get/Set target bitrate of this object
     *	Parameters:
     *	    fBitrate - [in/out] target audience bitrate
     *	Note:
     *	    Max supported bitrate is 1000 Kbps
     */
    STDMETHOD(GetTargetBitrate)	(THIS_
	REF(float) fBitrate) PURE;
    STDMETHOD(SetTargetBitrate)	(THIS_
	float fBitrate) PURE;
    
    /************************************************************************
     *	Method:
     *	    IRMATargetAudienceInfo::GetAudioCodec/SetAudioCodec
     *	Purpose:
     *	    Get/Set audio codec cookie for the specified target audience 
     *	    content and the specified audio content.
     *	Parameters:
     *	    encContentDescr - [in] target audience content descriptor 
     *				   (audio, video, or multimedia)
     *	    encAudioContent - [in] audio content type
     *	    ccAudioCodec - [in/out] audio codec cookie for the specified 
     *				    target settings type and the specified 
     *				    audio content
     */
    STDMETHOD(GetAudioCodec)	(THIS_
	UINT32 encContentDescr, UINT32 encAudioContent, REF(PNCODECCOOKIE) ccAudioCodec) PURE;
    STDMETHOD(SetAudioCodec)	(THIS_
	UINT32 encContentDescr, UINT32 encAudioContent, PNCODECCOOKIE ccAudioCodec) PURE;
    
    /************************************************************************
     *	Method:
     *	    IRMATargetAudienceInfo::GetVideoCodec/SetVideoCodec
     *	Purpose:
     *	    Get/Set video codec.
     *	Notes:
     *	    Unlike audio, only one video codec/flavor may be set for all 
     *		non backward-compatible SureStream targets (calling this once for a single 
     *		target audience will actually set the video codec for all target audiences).
     *	Parameters:
     *	    ccVideoCodec - [in/out] video codec
     */
    STDMETHOD(GetVideoCodec)	(THIS_
	REF(PNCODECCOOKIE) ccVideoCodec) PURE;
    STDMETHOD(SetVideoCodec)	(THIS_
	PNCODECCOOKIE ccVideoCodec) PURE;
    
    /************************************************************************
     *	Method:
     *	    IRMATargetAudienceInfo::GetMaxFrameRate/SetMaxFrameRate
     *	Purpose:
     *	    Get/Set the max frame rate for this audience object.
     *	Parameters:
     *	    fMaxFrameRate - [in/out] max frame rate
     */
    STDMETHOD(GetMaxFrameRate)	(THIS_
	REF(float) fMaxFrameRate) PURE;
    STDMETHOD(SetMaxFrameRate)	(THIS_
	float fMaxFrameRate) PURE;
};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMATargetAudienceInfo2
 *
 *  Purpose:
 *
 *	Extended properties interface for an individual target audience.
 *
 *  Notes:
 *
 *	To access the object that support this interface, call
 *	IRMATargetAudienceManager::GetTargetAudienceInfo(), then
 *	QI the returned interface for IRMATargetAudienceInfo2.
 *
 *  IRMATargetAudienceInfo2
 *
 *  {1FB16E20-D566-11d3-86A3-C40E92000000}
 *
 */
DEFINE_GUID(IID_IRMATargetAudienceInfo2,
	    0x1fb16e20, 0xd566, 0x11d3, 0x86, 0xa3, 0xc4, 0xe, 0x92, 0x0, 0x0, 0x0);

#undef  INTERFACE
#define INTERFACE   IRMATargetAudienceInfo2

DECLARE_INTERFACE_(IRMATargetAudienceInfo2, IRMATargetAudienceInfo)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
	REFIID riid,
	void** ppvObj) PURE;
    
    STDMETHOD_(UINT32,AddRef)	(THIS) PURE;
    
    STDMETHOD_(UINT32,Release)	(THIS) PURE;
    
    /*********************************************
     *
     *	IRMATargetAudienceInfo2 methods
     */
    
    /************************************************************************
     *	Method:
     *	    IRMATargetAudienceInfo2::GetVariableBitRateEncoding()
     *	Purpose:
     *	    Determine if Variable Bit Rate (VBR) video encoding is on or off.
     *	Parameters:
     *	    pbVBR - [out] TRUE if VBR is on, FALSE if VBR is off
     */
    STDMETHOD(GetVariableBitRateEncoding) (THIS_
	BOOL* pbVBR) PURE;
    
    /************************************************************************
     *	Method:
     *	    IRMATargetAudienceInfo2::SetVariableBitRateEncoding()
     *	Purpose:
     *	    Turn on/off Variable Bit Rate (VBR) video encoding.
     *	Parameters:
     *	    bVBR - [in] TRUE = VBR on, FALSE = VBR off
     */
    STDMETHOD(SetVariableBitRateEncoding) (THIS_
	BOOL bVBR) PURE;
    
    /************************************************************************
     *	Method:
     *	    IRMATargetAudienceInfo2::GetLossProtection()
     *	Purpose:
     *	    Determine if Loss Protection mode of video encoding is on or off.
     *	Parameters:
     *	    pbLoss - [out] TRUE if loss protection is on, FALSE if loss protection is off
     */
    STDMETHOD(GetLossProtection) (THIS_
	BOOL* pbLoss) PURE;

    /************************************************************************
     *	Method:
     *	    IRMATargetAudienceInfo2::SetLossProtection()
     *	Purpose:
     *	    Turn on/off additional loss protection in video codec.
     *	Parameters:
     *	    bLoss - [in] TRUE = on, FALSE = off
     */
    STDMETHOD(SetLossProtection) (THIS_
	BOOL bLoss) PURE;
    
    /************************************************************************
     *	Method:
     *	    IRMATargetAudienceInfo2::GetMaxTimeBetweenKeyframes()
     *	Purpose:
     *	    Gets the current setting for maximum time interval between 
     *	    keyframes in the video stream.
     *	Parameters:
     *	    pulMaxTimeBetweenKeyframes - [out] max time between keyframes in milleseconds
     */
    STDMETHOD(GetMaxTimeBetweenKeyframes) (THIS_
	UINT32* pulMaxTimeBetweenKeyframes) PURE;
    
    /************************************************************************
     *	Method:
     *	    IRMATargetAudienceInfo2::SetMaxTimeBetweenKeyframes()
     *	Purpose:
     *	    Set the maximum time interval between keyframes in the 
     *	    video stream.
     *	Parameters:
     *	    ulMaxTimeBetweenKeyframes - [in] max time between keyframes in milleseconds
     */
    STDMETHOD(SetMaxTimeBetweenKeyframes) (THIS_
	UINT32 ulMaxTimeBetweenKeyframes) PURE;
      
    /************************************************************************
     *	Method:
     *	    IRMATargetAudienceInfo2::GetVBRLatency()
     *	Purpose:
     *	    Gets the current setting for maximum latency (or preroll) of 
     *	    Variable Bit Rate video streams.
     *	Parameters:
     *	    pulVBRLatency - [out] maximum VBR Latency in milliseconds
     *	Notes:
     *	    VBR Latency is only used when Variable Bit Rate encoding is set
     *	    to TRUE.
     */
    STDMETHOD(GetVBRLatency) (THIS_
	UINT32* pulVBRLatency) PURE;

    /************************************************************************
     *	Method:
     *	    IRMATargetAudienceInfo2::SetVBRLatency()
     *	Purpose:
     *	    Set the maximum latency (or preroll) for Variable Bit Rate streams.
     *	Parameters:
     *	    ulVBRLatency - [out] maximum VBR Latency in milliseconds
     *	Notes:
     *	    VBR Latency is only used when Variable Bit Rate encoding is set
     *	    to TRUE.
     */
    STDMETHOD(SetVBRLatency) (THIS_
	UINT32 ulVBRLatency) PURE;

};

 
/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMATargetAudienceManager
 *
 *  Purpose:
 *
 *	Manager of the target audiences which are used to create the 
 *	audio and video physical stream templates.
 *
 *  IID_IRMATargetAudienceManager:
 *
 *	{FF8DA4C4-00BC-11d2-89B3-00C0F0177720}
 *
 */
DEFINE_GUID(IID_IRMATargetAudienceManager, 
	    0xff8da4c4, 0xbc, 0x11d2, 0x89, 0xb3, 0x0, 0xc0, 0xf0, 0x17, 0x77, 0x20);

/*
 *  You access objects that support this interface from the IRMAEncEngineProperties object 
 */
#define CLSID_IRMATargetAudienceManager IID_IRMATargetAudienceManager

#undef  INTERFACE
#define INTERFACE   IRMATargetAudienceManager

DECLARE_INTERFACE_(IRMATargetAudienceManager, IUnknown)
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
     *	IRMATargetAudienceManager methods
     */

    /************************************************************************
     *	Method:
     *	    IRMATargetAudienceManager::GetTargetAudienceInfo
     *	Purpose:
     *	    Get the target audience info object for the requested ID.
     *	Parameters:
     *	    nTarget - [in] target audience connection type, i.e. ENC_TARGET_28_MODEM
     *	    pTargetAudienceInfo - [out] target audience info object
     */
    STDMETHOD(GetTargetAudienceInfo)	(THIS_
	UINT32 nTarget, REF(IRMATargetAudienceInfo*) pTargetAudienceInfo) PURE;
    
    /************************************************************************
     *	Method:
     *	    IRMATargetAudienceManager::DisplayTargetAudienceSettings
     *	Purpose:
     *	    Display the target audience settings dialog for the
     *	    requested target audience content type.
     *	Parameters:
     *	    encContentDescr - [in] target audience content descriptor 
     *				   (audio, video, or multimedia)
     *	    parent - [in] parent dialog of the target audience settings dialog
     *	    pBasicTargetSettings - [in] basic target settings to get/set the 
     *				   audio only vs. multimedia mode
     *	    szHelpPath - [in] path of help file which will be launched if Help 
     *			 button is pressed. No help button will be shown if 
     *			 NULL or "" is passed in
     */
    STDMETHOD(DisplayTargetAudienceSettings)   (THIS_
	UINT32 encContentDescr, REF(PNxWindow) parent, 
	IRMABasicTargetSettings* pBasicSettings = NULL,
	const char* szHelpPath = NULL) PURE;

    /************************************************************************
     *	Method:
     *	    IRMATargetAudienceManager::RestoreDefaults
     *	Purpose:
     *	    Restore the default settings for the requested target 
     *	    audience content type.
     *	Parameters:
     *	    encContentDescr - [in] target audience content descriptor 
     *				   (audio, video, or multimedia)
     */
    STDMETHOD(RestoreDefaults)	(THIS_
	UINT32 encContentDescr) PURE;
};

#endif _ENGTARGS_H_
