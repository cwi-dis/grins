#ifndef INC_MPEG2CON
#define INC_MPEG2CON

#define MPEG2_FLOAT32 float
#define MPEG2_INT16   short int
#define MPEG2_INT32   int
#define MPEG2_INT64   long

#define MPEG2_ERROR (-1)

#define MPEG2_TOC_PREFIX                 0x544f4356
#define MPEG2_TOC_PREFIXLOWER            0x746f6376
#define MPEG2_ID3_PREFIX                 0x494433
#define MPEG2_RIFF_CODE                  0x52494646
#define MPEG2_TS_PACKET_SIZE             188
#define MPEG2_DVD_PACKET_SIZE            0x800
#define MPEG2_SYNC_BYTE                  0x47
#define MPEG2_PACK_START_CODE            0x000001ba
#define MPEG2_SEQUENCE_START_CODE        0x000001b3
#define MPEG2_SEQUENCE_END_CODE          0x000001b7
#define MPEG2_SYSTEM_START_CODE          0x000001bb
#define MPEG2_STRLEN                     512
#define MPEG2_PIDMAX                     20 // Maximum number of PIDs in one stream
#define MPEG2_PROGRAM_ASSOCIATION_TABLE  0x00
#define MPEG2_CONDITIONAL_ACCESS_TABLE   0x01
#define MPEG2_PACKET_START_CODE_PREFIX   0x000001
#define MPEG2_PRIVATE_STREAM_2           0xbf
#define MPEG2_PADDING_STREAM             0xbe
#define MPEG2_GOP_START_CODE             0x000001b8
#define MPEG2_PICTURE_START_CODE         0x00000100
#define MPEG2_EXT_START_CODE             0x000001b5
#define MPEG2_USER_START_CODE            0x000001b2
#define MPEG2_SLICE_START_CODE_MIN       0x00000101
#define MPEG2_SLICE_START_CODE_MAX       0x000001af
#define MPEG2_AC3_START_CODE             0x0b77
#define MPEG2_PCM_START_CODE             0x0180
#define MPEG2_MAX_CPUS                   256
#define MPEG2_MAX_STREAMS                2 // 256
#define MPEG2_MAX_PACKSIZE               262144
#define MPEG2_CONTIGUOUS_THRESHOLD       10  // Positive difference before declaring timecodes discontinuous 
#define MPEG2_PROGRAM_THRESHOLD          5   // Minimum number of seconds before interleaving programs 
#define MPEG2_SEEK_THRESHOLD             16  // Number of frames difference before absolute seeking 

#define MPEG2_EXTENSION_START_CODE	  0x1B5 // MPEG2_EXT_START_CODE
#define MPEG2_GROUP_START_CODE        0x1B8 // MPEG2_GOP_START_CODE
#define MPEG2_USER_DATA_START_CODE    0x1B2

#define MPEG2_SEQUENCE_ERROR_CODE	  0x1B4
#define MPEG2_SYSTEM_START_CODE_MIN   0x1B9
#define MPEG2_SYSTEM_START_CODE_MAX   0x1FF
#define ISO_END_CODE				  0x1B9
#define VIDEO_ELEMENTARY_STREAM 0x1e0

// Values for audio format
#define AUDIO_UNKNOWN 0
#define AUDIO_MPEG 1
#define AUDIO_AC3  2
#define AUDIO_PCM  3
#define AUDIO_AAC  4
#define AUDIO_JESUS  5

// extension start code IDs

#define SEQUENCE_EXTENSION_ID                    1
#define SEQUENCE_DISPLAY_EXTENSION_ID            2
#define QUANT_MATRIX_EXTENSION_ID                3
#define COPYRIGHT_EXTENSION_ID                   4
#define SEQUENCE_SCALABLE_EXTENSION_ID           5
#define PICTURE_DISPLAY_EXTENSION_ID             7
#define PICTURE_CODING_EXTENSION_ID              8
#define PICTURE_SPATIAL_SCALABLE_EXTENSION_ID    9
#define PICTURE_TEMPORAL_SCALABLE_EXTENSION_ID  10

#define ZIG_ZAG                                  0

#define PROFILE_422                             (128+5)
#define MAIN_LEVEL                              8

// Layers: used by Verbose_Flag, Verifier_Flag, Stats_Flag, and Trace_Flag
#define NO_LAYER                                0
#define SEQUENCE_LAYER                          1
#define PICTURE_LAYER                           2
#define SLICE_LAYER                             3    
#define MACROBLOCK_LAYER                        4    
#define BLOCK_LAYER                             5
#define EVENT_LAYER                             6
#define ALL_LAYERS                              7

/* scalable_mode */
#define SC_NONE 0
#define SC_DP   1
#define SC_SPAT 2
#define SC_SNR  3
#define SC_TEMP 4

/* picture coding type */
#define I_TYPE 1
#define P_TYPE 2
#define B_TYPE 3
#define D_TYPE 4

/* picture structure */
#define TOP_FIELD     1
#define BOTTOM_FIELD  2
#define FRAME_PICTURE 3

/* macroblock type */
#define MACROBLOCK_INTRA                        1
#define MACROBLOCK_PATTERN                      2
#define MACROBLOCK_MOTION_BACKWARD              4
#define MACROBLOCK_MOTION_FORWARD               8
#define MACROBLOCK_QUANT                        16
#define SPATIAL_TEMPORAL_WEIGHT_CODE_FLAG       32
#define PERMITTED_SPATIAL_TEMPORAL_WEIGHT_CLASS 64


/* motion_type */
#define MC_FIELD 1
#define MC_FRAME 2
#define MC_16X8  2
#define MC_DMV   3

/* mv_format */
#define MV_FIELD 0
#define MV_FRAME 1

/* chroma_format */
#define CHROMA420 1
#define CHROMA422 2
#define CHROMA444 3

#define MB_WEIGHT 32
#define MB_CLASS4 64


#ifndef _INC_TCHAR
#include <tchar.h>
#endif

#ifndef TEXT

#ifdef UNICODE
#define __TEXT(quote) L##quote 
#else 
#define __TEXT(quote) quote
#endif
  
#define TEXT(quote) __TEXT(quote)

#endif // TEXT


#endif // MPEG2CON
