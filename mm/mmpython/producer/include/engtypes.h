/****************************************************************************
 * 
 *  $Id$
 *
 *  engtypes.h
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
 *  Definition of types and constants for use with the RealProducer G2 Core SDK.
 *
 */

#ifndef _ENGTYPES_H_
#define _ENGTYPES_H_

/****************************************************************************
 * 
 *  PNCodecCookie:
 *
 *	Codec identifier. Contains both codec and flavor information for 
 *	audio and video codecs.
 *
 */
typedef UINT32	PNCodecID;
typedef UINT32	PNFlavorID;

typedef struct _tagPNCodecCookie
{
    PNCodecID	codecID;
    PNFlavorID	flavorID;
} PNCODECCOOKIE;

#define PNWIDTHBYTES(i) ((UINT32)((i+31)&(~31))/8)

// output mime types
#define MIME_REALAUDIO		"audio/x-pn-realaudio"
#define MIME_REALVIDEO		"video/x-pn-realvideo"
#define MIME_REALEVENT		"application/x-pn-realevent"
#define MIME_REALIMAGEMAP	"application/x-pn-imagemap"
#define MIME_REALPIX		"application/x-pn-realpix"

// connection types
enum
{
    ENC_TARGET_28_MODEM = 0,
    ENC_TARGET_56_MODEM,
    ENC_TARGET_SINGLE_ISDN,
    ENC_TARGET_DUAL_ISDN,  
    ENC_TARGET_LAN_LOW,		// Deprecated
    ENC_TARGET_LAN_HIGH,  
    ENC_TARGET_256_DSL_CABLE,
    ENC_TARGET_384_DSL_CABLE,
    ENC_TARGET_512_DSL_CABLE,
    ENC_NUM_TARGET_AUDIENCES
};

// audio content type
enum 
{
    ENC_AUDIO_CONTENT_VOICE = 0,
    ENC_AUDIO_CONTENT_VOICE_BACKGROUND,
    ENC_AUDIO_CONTENT_MUSIC,
    ENC_AUDIO_CONTENT_MUSIC_STEREO,
    ENC_NUM_AUDIO_CONTENTS
};

// video quality selection
enum 
{
    ENC_VIDEO_QUALITY_NORMAL = 0,
    ENC_VIDEO_QUALITY_SMOOTH_MOTION,
    ENC_VIDEO_QUALITY_SHARP_IMAGE,
    ENC_VIDEO_QUALITY_SLIDESHOW,
    ENC_NUM_VIDEO_QUALITYS
};

// video formats
enum
{
    ENC_VIDEO_FORMAT_RGB24 = 0,

    ENC_VIDEO_FORMAT_RGB32,
    ENC_VIDEO_FORMAT_RGB32_NONINVERTED,
    ENC_VIDEO_FORMAT_BGR32,
    ENC_VIDEO_FORMAT_BGR32_NONINVERTED,

    // planar yuv formats
    ENC_VIDEO_FORMAT_I420,			// the codec's format -- planar 4:2:0 (covers fourCC 'IYUV' as well)
    ENC_VIDEO_FORMAT_YV12,			// same as I420, but with UV planes swapped

	ENC_VIDEO_FORMAT_YVU9,			// planar 16:2:0 format

	// packed YUV formats
    ENC_VIDEO_FORMAT_YUY2,			// packed 4:2:2 format
    ENC_VIDEO_FORMAT_YUY2_INVERTED, // packed 4:2:2 format, inverted (Winnov Videum)
    ENC_VIDEO_FORMAT_UYVY,			// packed 4:2:2 format, different ordering

    ENC_NUM_VIDEO_FORMATS    
};

// noise filter options for video
enum
{
	ENC_VIDEO_NOISE_FILTER_OFF = 0,
	ENC_VIDEO_NOISE_FILTER_LOW,
	ENC_VIDEO_NOISE_FILTER_HIGH,
	ENC_NUM_NOISE_FILTER_SETTINGS
};

/****************************************************************************
 * 
 *  Target Audience Content Descriptors:
 *
 *	Used to identify different types of content for a target audience. 
 *	For each type of content the RM Build Engine will select different
 *	codec combinations.
 *
 *	Also used to specify which tab to show in the Target Audience Settings 
 *	dialog via IRMATargetAudienceManager::DisplayTargetAudienceSettings().
 *
 *  ENC_TARGET_AUDIENCES_AUDIO:
 *
 *	Use for producing AUDIO ONLY clips that maximize available bandwidth.
 *
 *  ENC_TARGET_AUDIENCES_VIDEO:  
 *
 *	Use for producing clips with AUDIO & VIDEO.
 *
 *  ENC_TARGET_AUDIENCES_MULTIMEDIA: 
 *
 *	Used for producing AUDIO ONLY clips that are meant to be combined 
 *	with other streaming media (typically via a SMIL presentation).
 */
enum 
{
    ENC_TARGET_AUDIENCES_AUDIO = 0,
    ENC_TARGET_AUDIENCES_VIDEO,
    ENC_TARGET_AUDIENCES_MULTIMEDIA,
    ENC_NUM_TARGET_AUDIENCES_OPTIONS
};

// target settings types - types for the target settings managers
enum
{
    ENC_TARGET_SETTINGS_BASIC = 0,
    ENC_NUM_TARGET_SETTINGS_TYPES
};

/****************************************************************************
 * 
 *  Constant: ENC_MAX_STR
 *
 *	Use this constant as the maximum string length for any 
 *	strings that you want to get from the Clip Properties including 
 *	title, author, copyright, filenames, server name, etc.
 */
const ULONG32 ENC_MAX_STR = 255;

/****************************************************************************
 * 
 *  Constant: ENC_MAX_META_DESCRIPTION_STR
 *
 *	Use this constant as the maximum string length for the  
 *	Meta Description field.
 */
const ULONG32 ENC_MAX_META_DESCRIPTION_STR = 1024;

/****************************************************************************
 * 
 *  IRMAMediaSample BitFlags:
 *
 *	MEDIA_SAMPLE_SYNCH_POINT
 *	    Used to mark a media sample of importance. For example, a
 *	    video encoding pin may use this flag to force the codec 
 *	    to mark the frame as a keyframe.
 *
 *	MEDIA_SAMPLE_END_OF_STREAM
 *	    Notifies the input pin that no more samples will be sent
 *	    the input data stream.
 */
#define MEDIA_SAMPLE_SYNCH_POINT   0x0001
#define MEDIA_SAMPLE_END_OF_STREAM 0x0002

// Types of events
enum
{
    IRMAEventMediaSample_URL,
    IRMAEventMediaSample_Title,
    IRMAEventMediaSample_Author,
    IRMAEventMediaSample_Copyright
};

// Region shapes used in image maps
enum
{
    IRMAImageMapMediaSample_SHAPE_NONE = 0,
    IRMAImageMapMediaSample_SHAPE_RECTANGLE = 1,
    IRMAImageMapMediaSample_SHAPE_CIRCLE = 2,
    IRMAImageMapMediaSample_SHAPE_POLYGON = 3
};

// Actions resulting from clicking on an image map
enum
{
    IRMAImageMapMediaSample_ACTION_NONE = 0,
    IRMAImageMapMediaSample_ACTION_BROWSER_URL = 1,
    IRMAImageMapMediaSample_ACTION_PLAYER_URL = 2,
    IRMAImageMapMediaSample_ACTION_PLAYER_SEEK = 3
};


/****************************************************************************
 * 
 *  Statistics Registry Key Names:
 *
 *	These will be the key names of the composite properties in the Registry
 *	that will be used to organize the stream lists. 
 *
 *  ENC_STATS_TARGET_STREAMS:
 *
 *	Contains a list of all target streams. The only properties of a target
 *	stream are the target audience, and the registry key name of the audio
 *	and/or video streams
 *
 *  ENC_STATS_TARGET_AUDIO:  
 *
 *	Contains a list of all audio streams and stream properties. 
 *
 *  ENC_STATS_TARGET_VIDEO: 
 *
 *	Contains a list of all video streams and stream properties. 
 */
#define ENC_STATS_TARGET_STREAMS "TargetStreams"
#define ENC_STATS_AUDIO_STREAMS "AudioStreams"
#define ENC_STATS_VIDEO_STREAMS "VideoStreams"

#endif // _ENGTYPES_H_
