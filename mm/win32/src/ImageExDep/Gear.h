/***************************************************************************/
/*                                                                         */
/* MODULE:  Gear.h - Master AccuSoft ImageGear include file                */
/*                                                                         */
/*                                                                         */
/* DATE CREATED:  01/30/1996                                               */ 
/*                                                                         */
/* $Date$                                                */
/* $Revision$                                                      */
/*                                                                         */
/* Copyright (c) 1996, AccuSoft Corporation.  All rights reserved.         */
/*                                                                         */
/***************************************************************************/

#ifndef __GEAR_H__
#define __GEAR_H__

#ifdef __cplusplus
extern "C" {
#endif


/***************************************************************************/
/* Compile time version macros                                             */
/***************************************************************************/

#define GEAR_REV_MAJOR  6
#define GEAR_REV_MINOR  0
#define GEAR_REV_UPDATE 35


/***************************************************************************/
/* AccuSoft standard include files                                         */
/***************************************************************************/

#ifndef RC_INVOKED

#include "accuosd.h"    /* AccuSoft OS function and type declarators       */
#include "accustd.h"    /* AccuSoft standard types and macros              */
#include "accuimg.h"    /* AccuSoft imaging types and macros               */

/* #ifndef RC_INVOKED */
#endif


/***************************************************************************/
/* AccuSoft ImageGear specific includes                                    */
/***************************************************************************/

#include "gearerrs.h"   /* ImageGear error codes                           */
#include "geartags.h"   /* Image tag callback macros                       */


/***************************************************************************/
/* ImageGear preprocessor macros                                           */
/***************************************************************************/

/* bitmapped color components                                              */ 
#define  IG_COLOR_COMP_R            0x0001
#define  IG_COLOR_COMP_G            0x0002
#define  IG_COLOR_COMP_B            0x0004
#define  IG_COLOR_COMP_RGB          (IG_COLOR_COMP_R | IG_COLOR_COMP_G | IG_COLOR_COMP_B)
#define  IG_COLOR_COMP_I            0x0010  /* used when the ave of RGB is to be used*/


/* biCompression field of AT_DIB                                           */ 
#define  IG_BI_RGB                  0L    /*Standard DIB                   */
#define  IG_BI_RLE                  500L  /*AccuSoft DIB extension: RunEnds*/
#define  IG_BI_CMYK                 501L  /*AccuSoft DIB extension: CMYK   */
#define  IG_BI_ABIC                 502L  /*AccuSoft DIB extension: ABIC   */


/* values for nAspectMethod parameter of IG_display_adjust_aspect          */ 
#define  IG_ASPECT_NONE             0  
#define  IG_ASPECT_DEFAULT          1  
#define  IG_ASPECT_HORIZONTAL       2
#define  IG_ASPECT_VERTICAL         3  
#define	IG_ASPECT_MAXDIMENSION		4
#define	IG_ASPECT_MINDIMENSION		1


/* values for altering the contrast of an image                            */ 
#define  IG_CONTRAST_PALETTE        0     /* Alter the palette only        */
#define  IG_CONTRAST_PIXEL          1     /* Alter the pixel values        */


/* values for nFitMethod parameter of IG_display_fit_method                */
#define IG_DISPLAY_FIT_TO_WINDOW    0     
#define IG_DISPLAY_FIT_TO_WIDTH     1
#define IG_DISPLAY_FIT_TO_HEIGHT    2     
#define IG_DISPLAY_FIT_1_TO_1       3     


/* values for nPriority parameter of IG_display_handle_palette             */ 
#define IG_PALETTE_PRIORITY_DEFAULT 0
#define IG_PALETTE_PRIORITY_HIGH    1     
#define IG_PALETTE_PRIORITY_LOW     2  


/* values for nDitherMode parameter of IG_display_dither_mode_set          */ 
#define IG_DITHER_MODE_DEFAULT      0  
#define IG_DITHER_MODE_NONE         1  
#define IG_DITHER_MODE_BAYER        2  


/* values for direction parameter of IG_IP_flip function                   */
#define IG_FLIP_HORIZONTAL          0  
#define IG_FLIP_VERTICAL            1  


/* values for IG_IP_rotate_ function                                       */ 
#define IG_ROTATE_CLIP              0  
#define IG_ROTATE_EXPAND            1  

#define IG_ROTATE_0                 0
#define IG_ROTATE_90                1  
#define IG_ROTATE_180               2  
#define IG_ROTATE_270               3  


/* values for PROMOTE function                                             */
#define IG_PROMOTE_TO_4             1  
#define IG_PROMOTE_TO_8             2  
#define IG_PROMOTE_TO_24            3  


/* General purpose compass directions                                      */
#define IG_COMPASS_N                1  
#define IG_COMPASS_NE               2  
#define IG_COMPASS_E                3  
#define IG_COMPASS_SE               4  
#define IG_COMPASS_S                5  
#define IG_COMPASS_SW               6  
#define IG_COMPASS_W                7  
#define IG_COMPASS_NW               8  
      

#define IG_INTERPOLATION_NONE       0              
/*#define IG_INTERPOLATION_AVERAGE  1  !! not in use yet*/
/*#define IG_INTERPOLATION_BILINEAR 2  !! not in use yet*/
   

/* IG_load_color()                                                         */
#define IG_LOAD_COLOR_DEFAULT       0     
#define IG_LOAD_COLOR_1             1  
#define IG_LOAD_COLOR_4             2  
#define IG_LOAD_COLOR_8             3  


/* IG_palette_save()                                                       */ 
#define IG_PALETTE_FORMAT_INVALID   0  /* returned when file could not be read   */
#define IG_PALETTE_FORMAT_RAW_BGR   1  /* This is the raw DIB format BGR         */
#define IG_PALETTE_FORMAT_RAW_BGRQ  2  /* This is the raw DIB format BGRQ        */
#define IG_PALETTE_FORMAT_RAW_RGB   3  /* This is the raw DIB format RGB         */
#define IG_PALETTE_FORMAT_RAW_RGBQ  4  /* This is the raw DIB format RGBQ        */
#define IG_PALETTE_FORMAT_TEXT      5  /* ASCII text file (details in manual)    */
#define IG_PALETTE_FORMAT_HALO_CUT  6  /* Dr Halo .PAL file for use with a .CUT  */


/* IG_FX_twist()  type parameter                                           */ 
#define IG_TWIST_90                 1
#define IG_TWIST_180                2
#define IG_TWIST_270                3
#define IG_TWIST_RANDOM             4


/* values for nAliasType parameter of IG_display_alias_set()               */
#define IG_DISPLAY_ALIAS_NONE             0
#define IG_DISPLAY_ALIAS_PRESERVE_BLACK   1
#define IG_DISPLAY_ALIAS_SCALE_TO_GRAY    2


/* types of edge maps                                                      */
#define IG_EDGE_OP_PREWITT          1
#define IG_EDGE_OP_ROBERTS          2
#define IG_EDGE_OP_SOBEL            3
#define IG_EDGE_OP_LAPLACIAN        4
#define IG_EDGE_OP_HORIZONTAL			5
#define IG_EDGE_OP_VERTICAL			6
#define IG_EDGE_OP_DIAG_POS_45		7
#define IG_EDGE_OP_DIAG_NEG_45		8


/* Types of structuring Elements and Convolution kernels                   */
#define IG_MAX_KERN_HEIGHT          16
#define IG_MAX_KERN_WIDTH           16


/* Types of convolution data output formats                                */
#define IG_CONV_RESULT_RAW             0
#define IG_CONV_RESULT_ABS             1
#define IG_CONV_RESULT_8BIT_SIGNED     2
#define IG_CONV_RESULT_SIGN_CENTERED   3


/* Types of 24 bit convolution data inputs                                 */
#define IG_CONV_24_INTENSITY        0
#define IG_CONV_24_RGB              1
#define IG_CONV_24_R                2
#define IG_CONV_24_G                3
#define IG_CONV_24_B                4


/* values for nFillOrder parameter of IG_load_CCITT_FD()                   */
#define IG_FILL_MSB                 0
#define IG_FILL_LSB                 1


/* IG_IP_arithmetic                                                        */
#define IG_ARITH_ADD                1  /* Add   Img1 = Img1 + Img2         */
#define IG_ARITH_SUB                2  /* Sub   Img1 = Img1 - Img2         */
#define IG_ARITH_MULTI              3  /* Multi Img1 = Img1 * Img2         */
#define IG_ARITH_DIVIDE             4  /* Div   Img1 = Img1 / Img2         */
#define IG_ARITH_AND                5  /* AND   Img1 = Img1 & Img2         */
#define IG_ARITH_OR                 6  /* OR    Img1 = Img1 | Img2         */
#define IG_ARITH_XOR                7  /* XOR   Img1 = Img1 ^ Img2         */
#define IG_ARITH_ADD_SIGN_CENTERED  8  /* NOT   Img1 = Img1 + SC_Img2      */
#define IG_ARITH_NOT                9  /* NOT   Img1 = ~Img1               */


/* Types of image blending modes                               */
#define IG_BLEND_ON_INTENSITY       0
#define IG_BLEND_ON_IMAGE           1
#define IG_BLEND_ON_HUE             2


/* Encryption mode                                                         */
#define IG_ENCRYPT_METHOD_A         0  /* Method A                         */
#define IG_ENCRYPT_METHOD_B         1  /* Method B                         */
#define IG_ENCRYPT_METHOD_C         2  /* Method C                         */


/* Color spaces                                                            */
#define IG_COLOR_SPACE_RGB          0  /* RGB                              */
#define IG_COLOR_SPACE_I            1  /* Intensity                        */
#define IG_COLOR_SPACE_IHS          2  /* IHS                              */
#define IG_COLOR_SPACE_HSL          3  /* HSL                              */
#define IG_COLOR_SPACE_Lab          4  /* Lab                              */
#define IG_COLOR_SPACE_YIQ          5  /* YIQ                              */
#define IG_COLOR_SPACE_CMY          6  /* CMY                              */
#define IG_COLOR_SPACE_CMYK         7  /* CMYK                             */
#define IG_COLOR_SPACE_YCrCb        8  /* YCrCb                            */
#define IG_COLOR_SPACE_YUV          9  /* YUV                              */


/* IG_FX_pixelate                                                          */
#define IG_PIXELATE_CENTER          0  /* Sample center of each block      */
#define IG_PIXELATE_AVERAGE         1  /* Compute the average of each block*/

/* nWipeStyle of IG_display_image_wipe() 												*/
#define IG_WIPE_LEFTTORIGHT         0  /* left edge to right edge				*/
#define IG_WIPE_RIGHTTOLEFT         1  /* right edge to left edge				*/
#define IG_WIPE_SPARKLE             2  /* replace random regions 				*/
#define IG_WIPE_ULTOLRDIAG          3  /* upper left to lower right			*/


/* Data types for use with tag callbacks  											*/
#define IG_TAG_TYPE_NULL          0    /* no data -- end of tags                           */
#define IG_TAG_TYPE_BYTE          1    /* data is a 8 bit unsigned int                     */
#define IG_TAG_TYPE_ASCII         2    /* data is a 8 bit, NULL-term String                */
#define IG_TAG_TYPE_SHORT         3    /* data is a 16 bit,unsigned int                    */
#define IG_TAG_TYPE_LONG          4    /* data is a 32 bit, unsigned int                   */
#define IG_TAG_TYPE_RATIONAL      5    /* data is a two 32-bit unsigned integers           */
#define IG_TAG_TYPE_SBYTE         6    /* data is a 8 bit signed int                       */
#define IG_TAG_TYPE_UNDEFINED     7    /* data is a 8 bit byte                             */
#define IG_TAG_TYPE_SSHORT        8    /* data is a 16-bit signed int                      */
#define IG_TAG_TYPE_SLONG         9    /* data is a 32-bit signed int                      */
#define IG_TAG_TYPE_SRATIONAL    10    /* data is a two 32-bit signed int                  */
#define IG_TAG_TYPE_FLOAT        11    /* data is a 4-byte single-prec IEEE floating point */
#define IG_TAG_TYPE_DOUBLE       12    /* data is a 8-byte double-prec IEEE floating point */
#define IG_TAG_TYPE_RAWBYTES     13    /* data is a series of raw data bytes               */
#define IG_TAG_TYPE_LONGARRAY    14    /* data is an array of 32-bit signed ints           */


/* FX Blur constants                   											*/
#define  IG_BLUR_3               1     /* Blurs using a 3x3 kernel*/
#define  IG_BLUR_5               2     /* Blurs using a 5x5 kernel*/


/* FX resample constants   															*/
#define  IG_RESAMPLE_IN_AVE      0
#define  IG_RESAMPLE_IN_MIN      1
#define  IG_RESAMPLE_IN_MAX      2
#define  IG_RESAMPLE_IN_CENTER   3
#define  IG_RESAMPLE_OUT_SQUARE  0
#define  IG_RESAMPLE_OUT_CIRCLE  1


/* FX noise constants																	*/
#define  IG_NOISE_LINEAR         0
#define  IG_NOISE_GAUSSIAN       1


/* Multi Page Append image flag  													*/
#define IG_APPEND_PAGE 				0


/* Deskew constants					       											*/
#define	IG_SPEED_OVER_MEMORY		0
#define	IG_MEMORY_OVER_SPEED		1 


/* Draw Contrast Ramp Constants														*/
#define	IG_RAMP_HORIZONTAL   	0
#define	IG_RAMP_VERTICAL			1
#define	IG_RAMP_PYRAMID			2
#define	IG_RAMP_FORWARD			0
#define	IG_RAMP_REVERSE      	1


/* nPrintSize parameter of IG_print_page() 										*/
#define	IG_PRINT_FULL_PAGE				0
#define	IG_PRINT_THREE_QUARTER_PAGE	1
#define	IG_PRINT_HALF_PAGE				2
#define	IG_PRINT_QUARTER_PAGE			3
#define	IG_PRINT_EIGHTH_PAGE				4
#define	IG_PRINT_SIXTEENTH_PAGE			5

/* nHorzPos and nVertPos parameters of IG_print_page() 						*/
#define	IG_PRINT_ALIGN_LEFT		0
#define	IG_PRINT_ALIGN_TOP		0
#define	IG_PRINT_ALIGN_CENTER	1
#define	IG_PRINT_ALIGN_RIGHT		2
#define	IG_PRINT_ALIGN_BOTTOM	2

/* nAttributeID parameter of IG_GUI_window_attribute_set()					*/
#define	IG_GUI_WINDOW_PAINT		0


/* Pixel Access data format															*/
#define	IG_PIXEL_PACKED			1
#define	IG_PIXEL_UNPACKED			2
#define	IG_PIXEL_RLE				3

/* IG_DIB_area_get/set                                                  */
#define	IG_DIB_AREA_RAW         0  /* all pixels as they are found     */
#define	IG_DIB_AREA_DIB         1  /* pads rows to long boundries      */
#define	IG_DIB_AREA_UNPACKED    2  /* 1 pixel per byte or 3 bytes (24) */


/* ImageGear extension constants														*/
#define	IG_EXTENTION_LZW			0
#define	IG_EXTENTION_MEDICAL		1
#define	IG_EXTENTION_ABIC			2

/* Area access functions																*/
#define	IG_DIB_AREA_INFO_MIN		1
#define	IG_DIB_AREA_INFO_MAX		2
#define	IG_DIB_AREA_INFO_AVE		3
#define	IG_DIB_AREA_INFO_CENTER	4

/* Draw frame functions																	*/
#define	IG_DRAW_FRAME_EXPAND		1
#define	IG_DRAW_FRAME_OVERWRITE	2

/* Image Resolution Units																*/
#define	IG_RESOLUTION_NO_ABS				1	/* No Absolute Units						*/
#define	IG_RESOLUTION_METERS				2	/* Pels (Pixels) Per Meter				*/
#define	IG_RESOLUTION_INCHES				3	/* Dots (Pixels) Per Inch				*/
#define	IG_RESOLUTION_CENTIMETERS		4	/* Pixles Per CentiMeter				*/


/***************************************************************************/
/* ImageGear types                                                         */
/***************************************************************************/

typedef DWORD        HIGEAR;		/* Handle to an ImageGear image           */
typedef HIGEAR FAR	*LPHIGEAR;	/* Far pointer to HIGEAR                  */

typedef struct  tagKERN
   {
   AT_DIMENSION   width;
   AT_DIMENSION   height;
   AT_PIXPOS      start_x;
   AT_PIXPOS      start_y;
   AT_PIXPOS      end_x;
   AT_PIXPOS      end_y;
   DOUBLE      	normalizer;    /* value that is divided into matrix sum  */
   AT_MODE     	result_form;   /* IG_CONV_RESULT_                        */
   INT         	kern[IG_MAX_KERN_HEIGHT][IG_MAX_KERN_WIDTH];
   }
   AT_KERN;
typedef AT_KERN FAR	*LPAT_KERN;


/***************************************************************************/
/* Low level I/O type definitions                                          */
/***************************************************************************/

typedef LONG (ACCUAPI *LPFNIG_SEEK)(

   LONG     fd,      /* Descriptor ID, from open   */ 
   LONG     lOffset, /* Offset into file           */
   INT      nFlag    /* From start, end or current */
   );

typedef LONG (ACCUAPI *LPFNIG_READ)(

   LONG     fd,         /* Descriptor ID, from open   */ 
   LPBYTE   lpBuffer,   /* Data read into this buffer */
   LONG     lSize       /* Amount to read in bytes    */
   );

typedef LONG (ACCUAPI *LPFNIG_WRITE)(

   LONG           fd,         /* Descriptor ID, from open   */ 
   const LPBYTE   lpBuffer,   /* Data written from here     */
   LONG           lSize       /* Amount to write in bytes   */
   );


/***************************************************************************/
/* Image file tags header callback function definitions                    */
/***************************************************************************/

typedef BOOL (ACCUAPI *LPFNIG_TAG_GET)(

   LPVOID         lpPrivate,     /* Private data passed in        */
   AT_MODE        nIGTag,        /* Tag ID from geartags.h        */
   LPAT_MODE      lpType,        /* Type of data lpTag points to  */
   LPVOID         lpTag,         /* Pointer to tag data           */
   DWORD          dwSize         /* Size of tag data (bytes)      */
   );

typedef BOOL (ACCUAPI *LPFNIG_TAG_SET)(

   LPVOID         lpPrivate,     /* Private data passed in        */
   AT_MODE        nIGTag,        /* Tag ID from geartags.h        */
   AT_MODE        nType,         /* Type of data in lpTag         */
   const LPVOID   lpTag,         /* Pointer to tag data           */
   DWORD          dwSize         /* Size of tag data (bytes)      */
   );

typedef BOOL (ACCUAPI *LPFNIG_TAG_USER_GET)(

   LPVOID         lpPrivate,     /* Private data passed in        */
   LPAT_MODE		lpIGTag,       /* Tag ID from geartags.h        */
   LPAT_MODE		lpType,        /* Type of data lpTag points to  */
   LPVOID FAR     *lpTag,        /* Pointer to tag data           */
   LPDWORD        lpSize         /* Size of tag data (bytes)      */
   );


/***************************************************************************/
/* DIB create callback function definition                                 */
/***************************************************************************/

typedef AT_ERRCOUNT (ACCUAPI *LPFNIG_DIB_CREATE)( 

   LPVOID               lpPrivate,     /* Private data passed in        */
   const LPAT_DIB       lpDIB,         /* Header of new DIB             */
   const LPAT_RGBQUAD   lpRGB          /* Palette of new DIB            */
   );

typedef AT_ERRCOUNT (ACCUAPI *LPFNIG_DIB_GET)( 

   LPVOID         lpPrivate,           /* Private data passed in        */
   LPAT_DIB       lpDIB,               /* DIB header to be set          */ 
   LPAT_RGBQUAD   lpRGB                /* DIB palette to be set         */
   );


/***************************************************************************/
/* Raster line set and get callback function definitions                   */
/***************************************************************************/

typedef AT_ERRCOUNT  (ACCUAPI *LPFNIG_RASTER_SET)( 

   LPVOID         	lpPrivate,     /* Private data passed in        */
   const LPAT_PIXEL  lpRast,        /* Raster line to set            */ 
   AT_PIXPOS         cyPos,         /* Y position in the image       */
   DWORD          	cRasterSize    /* Size of the raster line       */
   );

typedef AT_ERRCOUNT  (ACCUAPI *LPFNIG_RASTER_GET)(

   LPVOID   	lpPrivate,           /* Private data passed in        */
   LPAT_PIXEL  lpRast,              /* Raster line to get            */ 
   AT_PIXPOS   cyPos,               /* Y position in the image       */
   DWORD    	cRasterSize          /* Size of the raster line       */
   );


/***************************************************************************/
/* Status bar callback function definition                                 */
/***************************************************************************/

typedef BOOL (ACCUAPI *LPFNIG_STATUS_BAR)( 

   LPVOID      	lpPrivate,     /* Private data passed in        */
   AT_PIXPOS      cyPos,         /* Y position in the image       */
   AT_DIMENSION   dwHeight       /* Height of the image           */
   );


/***************************************************************************/
/* Print document callback function definition                             */
/***************************************************************************/

typedef BOOL (ACCUAPI *LPFNIG_IMAGESPOOLED)(

   LPVOID      lpPrivate,		/* Private data passed in					  */
   UINT			nImageNumber,	/* Current image being spooled (1 based) */
	UINT			nPageNumber		/* Current page number being spooled	  */
   );


/***************************************************************************/
/* Load/display callback function definition                               */
/***************************************************************************/

typedef VOID (ACCUAPI *LPFNIG_LOAD_DISP)( 

   LPVOID      lpPrivate,     /* Private data passed in        */
   HIGEAR      hIGear
   );


/***************************************************************************/
/* ImageGear GUI callback definitions                                      */
/***************************************************************************/

#ifdef _WINDOWS

typedef BOOL (ACCUAPI *LPFNIG_GUIPALETTE)(

   LPVOID         lpPrivate,        /* Private data passed in        */
   UINT           nPaletteIndex,    /* Palette index that changed    */
   LPAT_RGBQUAD   lpRGB             /* RGB components of index       */
   );

typedef VOID (ACCUAPI *LPFNIG_GUISELECT)(

   LPVOID            lpPrivate,     /* Private data passed in        */
   const LPAT_RECT   lprcSelect     /* Selection rectangle           */
   );

typedef VOID (ACCUAPI *LPFNIG_GUIWINDESTROY)(

   LPVOID            lpPrivate,     /* Private data passed in        */
   HIGEAR            hIGear,        /* ImageGear image handle        */
   HWND              hwndImage      /* ImageGear GUI window handle   */
   );

typedef VOID (ACCUAPI *LPFNIG_GUITHUMBSELECT)(

   LPVOID            lpPrivate,     /* Private data passed in        */
   HWND              hwndThumbnail, /* Thumbnail window handle       */
   const LPSTR       lpszFileName,  /* File name of selected icon    */
   const LPAT_DIB    lpDIB,         /* AT_DIB filled with image info */
   UINT					nPageNumber		/* Page number in image file		*/
   );

typedef INT (ACCUAPI *LPFNIG_GUITHUMBCOMP)(

   LPVOID            lpPrivate,     /* Private data passed in        */
   HWND              hwndThumbnail, /* Thumbnail window handle       */
   const LPSTR       lpszFileName1, /* First thumbnail file name     */
   const LPSTR       lpszFileName2, /* Second thumbnail file name    */
   const LPAT_DIB    lpDIB1,        /* First thumbnail image info    */
   const LPAT_DIB    lpDIB2         /* Second thumbnail image info   */
   );


/* #ifdef _WINDOWS */
#endif


/***************************************************************************/
/* ImageGear macros for all supported file formats.                        */
/*                                                                         */
/* Keep list sorted and do not change numbering.A  dd new formats between  */
/* existing ones                                                           */
/*                                                                         */
/***************************************************************************/

#define IG_FORMAT_UNKNOWN         0  
#define IG_FORMAT_ATT             1
#define IG_FORMAT_BMP             2
#define IG_FORMAT_BRK             3
#define IG_FORMAT_CAL             4
#define IG_FORMAT_CLP             5
#define IG_FORMAT_CIF             6
#define IG_FORMAT_CUT             7
#define IG_FORMAT_DCX             8
#define IG_FORMAT_DIB             9
#define IG_FORMAT_EPS            10
#define IG_FORMAT_G3     	      11
#define IG_FORMAT_G4             12
#define IG_FORMAT_GEM            13
#define IG_FORMAT_GIF            14
#define IG_FORMAT_GX2            15
#define IG_FORMAT_ICA            16
#define IG_FORMAT_ICO            17
#define IG_FORMAT_IFF            18
#define IG_FORMAT_IGF            19
#define IG_FORMAT_IMT            20
#define IG_FORMAT_JPG            21
#define IG_FORMAT_KFX            22
#define IG_FORMAT_LV             23
#define IG_FORMAT_MAC            24
#define IG_FORMAT_MSP            25
#define IG_FORMAT_MOD            26
#define IG_FORMAT_NCR            27
#define IG_FORMAT_PBM            28
#define IG_FORMAT_PCD            29
#define IG_FORMAT_PCT            30
#define IG_FORMAT_PCX            31
#define IG_FORMAT_PGM            32
#define IG_FORMAT_PNG            33
#define IG_FORMAT_PNM            34
#define IG_FORMAT_PPM            35
#define IG_FORMAT_PSD            36
#define IG_FORMAT_RAS            37
#define IG_FORMAT_SGI            38
#define IG_FORMAT_TGA            39
#define IG_FORMAT_TIF            40
#define IG_FORMAT_TXT            41
#define IG_FORMAT_WPG            42
#define IG_FORMAT_XBM            43
#define IG_FORMAT_WMF            44
#define IG_FORMAT_XPM            45
#define IG_FORMAT_XRX            46
#define IG_FORMAT_XWD            47
#define IG_FORMAT_DCM            48


/***************************************************************************/
/* ImageGear macros for all compression types.                             */
/***************************************************************************/

#define IG_COMPRESSION_NONE         0     /* No compression                */    
#define IG_COMPRESSION_PACKED_BITS  1     /* Packed bits compression       */
#define IG_COMPRESSION_HUFFMAN      2     /* Huffman encoding              */
#define IG_COMPRESSION_CCITT_G3     3     /* CCITT Group 3                 */
#define IG_COMPRESSION_CCITT_G4     4     /* CCITT Group 4                 */
#define IG_COMPRESSION_CCITT_G32D   5     /* CCITT Group 3 2D              */
#define IG_COMPRESSION_JPEG         6     /* JPEG compression              */
#define IG_COMPRESSION_RLE          7     /* Run length encoding           */

/* The following compression algorithms require special licensing          */ 
#define IG_COMPRESSION_LZW          8     /* LZW compression               */
#define IG_COMPRESSION_ABIC_BW      9     /* IBM ABIC compression          */
#define IG_COMPRESSION_ABIC_GRAY    10    /* IBM ABIC compression          */
#define IG_COMPRESSION_JBIG         11    /* IBM JBIG compression          */


/***************************************************************************/
/* Format types used for saving image files                                */
/***************************************************************************/

#define IG_SAVE_UNKNOWN          (IG_FORMAT_UNKNOWN)
#define IG_SAVE_BMP_UNCOMP       (IG_FORMAT_BMP|((AT_LMODE)IG_COMPRESSION_NONE << 16))
#define IG_SAVE_BMP_RLE          (IG_FORMAT_BMP|((AT_LMODE)IG_COMPRESSION_RLE << 16))
#define IG_SAVE_BRK_G3           (IG_FORMAT_BRK|((AT_LMODE)IG_COMPRESSION_CCITT_G3 << 16))
#define IG_SAVE_BRK_G3_2D        (IG_FORMAT_BRK|((AT_LMODE)IG_COMPRESSION_CCITT_G32D << 16))
#define IG_SAVE_CAL              (IG_FORMAT_CAL)
#define IG_SAVE_CLP              (IG_FORMAT_CLP)
#define IG_SAVE_DCX              (IG_FORMAT_DCX)
#define IG_SAVE_EPS              (IG_FORMAT_EPS)
#define IG_SAVE_GIF              (IG_FORMAT_GIF)
#define IG_SAVE_ICA_G3           (IG_FORMAT_ICA|((AT_LMODE)IG_COMPRESSION_CCITT_G3 << 16))
#define IG_SAVE_ICA_G4           (IG_FORMAT_ICA|((AT_LMODE)IG_COMPRESSION_CCITT_G4 << 16))
#define IG_SAVE_ICA_ABIC         (IG_FORMAT_ICA|((AT_LMODE)IG_COMPRESSION_ABIC << 16))
#define IG_SAVE_ICO              (IG_FORMAT_ICO)
#define IG_SAVE_IMT              (IG_FORMAT_IMT)
#define IG_SAVE_IFF              (IG_FORMAT_IFF)
#define IG_SAVE_JPG              (IG_FORMAT_JPG)
#define IG_SAVE_PCT              (IG_FORMAT_PCT)
#define IG_SAVE_PCX              (IG_FORMAT_PCX)
#define IG_SAVE_PNG              (IG_FORMAT_PNG)
#define IG_SAVE_PSD              (IG_FORMAT_PSD)
#define IG_SAVE_RAS              (IG_FORMAT_RAS)
#define IG_SAVE_RAW_G3           (IG_FORMAT_UNKNOWN|((AT_LMODE)IG_COMPRESSION_CCITT_G3 << 16))
#define IG_SAVE_RAW_G4           (IG_FORMAT_UNKNOWN|((AT_LMODE)IG_COMPRESSION_CCITT_G4 << 16))
#define IG_SAVE_RAW_G32D         (IG_FORMAT_UNKNOWN|((AT_LMODE)IG_COMPRESSION_CCITT_G32D << 16))
#define IG_SAVE_RAW_JPG          (IG_FORMAT_UNKNOWN|((AT_LMODE)IG_COMPRESSION_JPG << 16))
#define IG_SAVE_RAW_LZW          (IG_FORMAT_UNKNOWN|((AT_LMODE)IG_COMPRESSION_LZW << 16))
#define IG_SAVE_RAW_RLE          (IG_FORMAT_UNKNOWN|((AT_LMODE)IG_COMPRESSION_RLE << 16))
#define IG_SAVE_SGI              (IG_FORMAT_SGI)
#define IG_SAVE_TGA              (IG_FORMAT_TGA)
#define IG_SAVE_TIF_ABIC         (IG_FORMAT_TIF|((AT_LMODE)IG_COMPRESSION_ABIC << 16))
#define IG_SAVE_TIF_UNCOMP       (IG_FORMAT_TIF|((AT_LMODE)IG_COMPRESSION_NONE << 16))
#define IG_SAVE_TIF_G3           (IG_FORMAT_TIF|((AT_LMODE)IG_COMPRESSION_CCITT_G3 << 16))
#define IG_SAVE_TIF_G3_2D        (IG_FORMAT_TIF|((AT_LMODE)IG_COMPRESSION_CCITT_G32D << 16))
#define IG_SAVE_TIF_G4           (IG_FORMAT_TIF|((AT_LMODE)IG_COMPRESSION_CCITT_G4 << 16))
#define IG_SAVE_TIF_HUFFMAN      (IG_FORMAT_TIF|((AT_LMODE)IG_COMPRESSION_HUFFMAN << 16))
#define IG_SAVE_TIF_JPG          (IG_FORMAT_TIF|((AT_LMODE)IG_COMPRESSION_JPEG << 16))
#define IG_SAVE_TIF_LZW          (IG_FORMAT_TIF|((AT_LMODE)IG_COMPRESSION_LZW << 16))
#define IG_SAVE_TIF_PACKED       (IG_FORMAT_TIF|((AT_LMODE)IG_COMPRESSION_PACKED_BITS << 16))
#define IG_SAVE_XBM              (IG_FORMAT_XBM)
#define IG_SAVE_XPM              (IG_FORMAT_XPM)
#define IG_SAVE_XWD              (IG_FORMAT_XWD)


/************************************************************************************/
/* ImageGear image control option IDs                                               */
/************************************************************************************/
/*      Option ID                            Format        | Opt #    lpData type   */
/*      --------------------------------     ---------------------    ------------- */

#define IG_CONTROL_JPG_QUALITY               (IG_FORMAT_JPG|0x0100)  /* UINT        */ 
#define IG_CONTROL_JPG_DECIMATION_TYPE       (IG_FORMAT_JPG|0x0200)  /* DWORD       */ 
#define IG_CONTROL_JPG_SAVE_THUMBNAIL        (IG_FORMAT_JPG|0x0300)  /* BOOL        */ 
#define IG_CONTROL_JPG_THUMBNAIL_WIDTH       (IG_FORMAT_JPG|0x0400)  /* UINT        */ 
#define IG_CONTROL_JPG_THUMBNAIL_HEIGHT      (IG_FORMAT_JPG|0x0500)  /* UINT        */ 

#define IG_CONTROL_TXT_XDPI                  (IG_FORMAT_TXT|0x0100)  /* UINT        */ 
#define IG_CONTROL_TXT_YDPI                  (IG_FORMAT_TXT|0x0200)  /* UINT        */ 
#define IG_CONTROL_TXT_MARGIN_LEFT           (IG_FORMAT_TXT|0x0300)  /* AT_DIMENSION   */ 
#define IG_CONTROL_TXT_MARGIN_TOP            (IG_FORMAT_TXT|0x0400)  /* AT_DIMENSION   */ 
#define IG_CONTROL_TXT_MARGIN_RIGHT          (IG_FORMAT_TXT|0x0500)  /* AT_DIMENSION   */ 
#define IG_CONTROL_TXT_MARGIN_BOTTOM         (IG_FORMAT_TXT|0x0600)  /* AT_DIMENSION   */ 
#define IG_CONTROL_TXT_PAGE_WIDTH            (IG_FORMAT_TXT|0x0700)  /* AT_DIMENSION   */ 
#define IG_CONTROL_TXT_PAGE_HEIGHT           (IG_FORMAT_TXT|0x0800)  /* AT_DIMENSION   */ 
#define IG_CONTROL_TXT_POINT_SIZE            (IG_FORMAT_TXT|0x0900)  /* INT         */ 
#define IG_CONTROL_TXT_WEIGHT                (IG_FORMAT_TXT|0x0A00)  /* BOOL        */ 
#define IG_CONTROL_TXT_ITALIC                (IG_FORMAT_TXT|0x0B00)  /* BOOL        */ 
#define IG_CONTROL_TXT_TAB_STOP              (IG_FORMAT_TXT|0x0C00)  /* UINT        */ 
#define IG_CONTROL_TXT_TYPEFACE              (IG_FORMAT_TXT|0x0D00)  /* CHAR[32]    */ 

#define IG_CONTROL_BMP_TYPE                  (IG_FORMAT_BMP|0x0100)  /* UINT        */ 
#define IG_CONTROL_BMP_UPSIDEDOWN            (IG_FORMAT_BMP|0x0200)  /* BOOL        */ 

#define IG_CONTROL_TIF_FILENAME_LEN          (IG_FORMAT_TIF|0x0100)  /* UINT        */ 
#define IG_CONTROL_TIF_FILENAME              (IG_FORMAT_TIF|0x0200)  /* LPSTR       */ 
#define IG_CONTROL_TIF_FILEDATE_LEN          (IG_FORMAT_TIF|0x0300)  /* UINT        */ 
#define IG_CONTROL_TIF_FILEDATE              (IG_FORMAT_TIF|0x0400)  /* LPSTR       */ 


/***************************************************************************/
/* ImageGear API function prototypes                                       */
/***************************************************************************/

AT_ERRCOUNT ACCUAPI IG_load_file(

   const LPSTR lpszFileName,  /* File name of image to load */
   LPHIGEAR    lphIGear       /* ImageGear handle           */
   );

AT_ERRCOUNT ACCUAPI IG_display_image(

   HIGEAR      hIGear,        /* ImageGear handle           */
   HDC         hDC            /* Display context            */
   );

AT_ERRCOUNT ACCUAPI IG_print_image(

   HIGEAR   hIGear,           /* ImageGear handle            */
   HDC      hDC,              /* Device context of printer   */
   BOOL     fDirectToDriver   /* TRUE - driver does the work */
   );

AT_ERRCOUNT ACCUAPI IG_print_page(

   HIGEAR   			hIGear,     /* ImageGear handle            */
   HDC      			hDC,        /* Device context of printer   */
   AT_MODE				nPrintSize,	/* Amount of paper to fill		 */
   AT_MODE				nHorzPos,	/* Horizontal positioning		 */
   AT_MODE				nVertPos		/* Vertical positioning		 	 */
   );

AT_ERRCOUNT ACCUAPI IG_print_document(

   LPHIGEAR   				lphIGear,    	  	/* Array of ImageGear handles  */
   UINT						nImageCount, 	  	/* Images count in lphIGear	 */
   HDC      				hDC,         	  	/* Device context of printer   */
   AT_MODE					nPrintSize,	 	  	/* Amount of paper to fill	  	 */
   BOOL						bTile,				/* Tile images on a page		 */
   LPFNIG_IMAGESPOOLED	lpfnImageSpooled, /* Gets called for each image  */
   LPVOID					lpPrivateData	  	/* Private callback data		 */
   );

AT_ERRCOUNT ACCUAPI IG_image_dimensions_get(

   HIGEAR      	hIGear,        /* Image handle            */ 
   LPAT_DIMENSION lpWidth,       /* Width of the image      */
   LPAT_DIMENSION lpHeight,      /* Height of the image     */
   LPUINT      	lpBitsPerPixel /* Depth of the image      */
   );

AT_ERRCOUNT ACCUAPI IG_image_delete(

   HIGEAR      hIGear         /* ImageGear handle        */
   );

AT_ERRCOUNT ACCUAPI IG_version_numbers(

   LPINT    lpVersionMajor,   /* Major version number    */
   LPINT    lpVersionMinor,   /* Minor version number    */
   LPINT    lpVersionUpdate   /* Update (bug fix) number */
   );

AT_ERRCOUNT ACCUAPI IG_version_is_eval(

   LPBOOL   lpVersionIsEval,  /* TRUE if DLL is a EVAL version, FALSE otherwise  */
   LPINT    lpDaysTilWarning, /* If EVAL, days until warning starts              */
   LPINT    lpDaysTilTimeOut  /* If EVAL, days until it times out (stops working)*/
   );

LPSTR ACCUAPI IG_version_compile_date(

   VOID
   );

AT_ERRCOUNT ACCUAPI IG_file_IO_register(

   LPFNIG_READ    lpfnReadFunc,     /* Replacement read, or NULL  */
   LPFNIG_WRITE   lpfnWriteFunc,    /* Replacement write, or NULL */
   LPFNIG_SEEK    lpfnSeekFunc      /* Replacement seek, or NULL  */
   );

AT_ERRCOUNT ACCUAPI IG_status_bar_CB_register(

   LPFNIG_STATUS_BAR lpfnStatusBar, /* Statusbar callback         */
   LPVOID            lpPrivate      /* Callback private data      */
   );

AT_ERRCOUNT ACCUAPI IG_load_file_display(

   const LPSTR       lpszFileName,  /* File name of image to load */
   HDC               HDC,           /* Device to display image    */
   LPFNIG_LOAD_DISP  lpfnLoadDisp,  /* Called with valid IG hndle */
   LPVOID            lpPrivate,     /* Private callback data      */
   LPHIGEAR          lphIGear       /* Image handle return        */
   );

AT_ERRCOUNT ACCUAPI IG_load_FD(

   INT         fd,            /* File descriptor            */
   LONG        lOffset,       /* Offset to image            */ 
   UINT        nPage,         /* Page number to load        */
   UINT        nReserved,     /* Always set to 0 (for now)  */
   LPHIGEAR    lphIGear       /* Image handle return        */
   );

AT_ERRCOUNT ACCUAPI IG_load_FD_CB(

   INT               fd,            /* File descriptor               */
   LONG              lOffset,       /* Offset to image               */ 
   UINT              nPage,         /* Page number to load           */
   UINT              nReserved,     /* Always set to 0 (for now)     */
   LPFNIG_RASTER_SET lpfnRasterSet, /* Called for each raster line   */
   LPFNIG_DIB_CREATE lpfnDIBCreate, /* Called after header is read   */
   LPVOID            lpPrivateData  /* Callback data                 */
   );

AT_ERRCOUNT ACCUAPI IG_load_CCITT_FD(

   INT         	fd,         /* File descriptor         */
   AT_DIMENSION   nWidth,     /* Width of merged image   */
   AT_DIMENSION   nHeight,    /* Height of merged image  */
   AT_MODE     	nType,      /* Type: G3 or G4          */
   AT_MODE     	nFillOrder, /* Fill order: LSB or MSB  */
   LPHIGEAR    	lphIGear    /* Image handle return     */
   );

AT_ERRCOUNT ACCUAPI IG_load_CCITT_mem(

   LPVOID      	lpImage,     /* Address of image in memory */
   DWORD       	dwImageSize, /* Size of image in memory    */ 
   AT_DIMENSION   nWidth,      /* Width of merged image      */
   AT_DIMENSION   nHeight,     /* Height of merged image     */
   AT_MODE     	nType,       /* Type: G3 or G4             */
   AT_MODE     	nFillOrder,  /* Fill order: LSB or MSB     */
   LPHIGEAR    	lphIGear     /* Image handle return        */
   );

AT_ERRCOUNT ACCUAPI IG_load_mem(

   LPVOID   lpImage,       /* Address of image in memory */
   DWORD    dwImageSize,	/* Size of image in memory    */ 
   UINT     nPage,         /* Page number to read        */
   UINT     nReserved,     /* Always set to 0 (for now)  */
   LPHIGEAR lphIGear       /* Image handle return        */
   );

AT_ERRCOUNT ACCUAPI IG_load_mem_CB(

   LPVOID            lpImage,       /* Address of image in memory    */
   DWORD             dwImageSize,   /* Size of image in memory       */ 
   UINT              nPage,         /* Page number to load           */
   UINT              nReserved,     /* Always set to 0 (for now)     */
   LPFNIG_RASTER_SET lpfnRasterSet, /* Called for each raster line   */
   LPFNIG_DIB_CREATE lpfnDIBCreate, /* Called after header is read   */
   LPVOID            lpPrivateData  /* Callback data                 */
   );

AT_ERRCOUNT ACCUAPI IG_load_thumbnail(

   const LPSTR lpszFileName,  /* File name of image to load */
   LPHIGEAR    lphIGear       /* ImageGear handle           */
   );

AT_ERRCOUNT ACCUAPI IG_load_thumbnail_FD(

   INT      fd,               /* File descriptor         */
   LONG     lOffset,          /* Offset to image         */ 
   LPHIGEAR lphIGear          /* ImageGear handle        */
   );

AT_ERRCOUNT ACCUAPI IG_load_thumbnail_mem(

   LPVOID   lpImage,     /* Address of image in memory */
   DWORD    dwImageSize, /* Size of image in memory    */ 
   LPHIGEAR lphIGear     /* ImageGear handle           */
   );

AT_ERRCOUNT ACCUAPI IG_info_get(

   const LPSTR lpszFileName,  /* File name of image            */ 
   LPAT_MODE   lpFileType,    /* File type return              */
   LPAT_MODE   lpCompression, /* Compression algorithm ret.    */
   LPAT_DIB    lpDIB          /* Image info return             */
   );

AT_ERRCOUNT ACCUAPI IG_info_get_FD(

   INT         fd,            /*F   ile descriptor             */
   LONG        lOffset,       /* Offset to image               */ 
   UINT        nPage,         /* Page number to get info       */
   LPAT_MODE   lpFileType,    /* File type return              */
   LPAT_MODE   lpCompression, /* Compression algorithm ret.    */
   LPAT_DIB    lpDIB          /* Image info return             */
   );

AT_ERRCOUNT ACCUAPI IG_info_get_mem(

   LPVOID      lpImage,       /* Address of image in memory */
   DWORD       dwImageSize,	/* Size of image in memory    */ 
   UINT        nPage,         /* Page number to get info    */
   LPAT_MODE   lpFileType,    /* File type return           */
   LPAT_MODE   lpCompression, /* Compression algorithm ret. */
   LPAT_DIB    lpDIB          /* Image info return          */
   );

AT_ERRCOUNT ACCUAPI IG_page_count_get(

   const LPSTR lpszFileName,     /* File name of image            */ 
   LPUINT      lpPageCount       /* Number of pages in an image   */
   );

AT_ERRCOUNT ACCUAPI IG_page_count_get_FD(

   INT         fd,         /* File descriptor            */
   LONG        lOffset,    /* Offset to image            */ 
   LPUINT      lpPageCount /* Number of pages in an image*/
   );

AT_ERRCOUNT ACCUAPI IG_page_count_get_mem(

   LPVOID      lpImage,     /* Address of image in memory    */
   DWORD       dwImageSize, /* Size of image in memory       */ 
   LPUINT      lpPageCount  /* Number of pages in an image   */
   );

AT_ERRCOUNT ACCUAPI IG_tile_count_get(

   const LPSTR       lpszFileName,     /* File name of image            */
   UINT              PageNumber,       /* Page to get tile number for   */
   LPUINT            lpTileRows,       /* Number of Tile in a row       */
   LPUINT            lpTileCols        /* Number of Tile in a col       */
   );

AT_ERRCOUNT ACCUAPI IG_tile_count_get_FD(

   INT               fd,               /* File descriptor               */
   LONG              lOffset,          /* Offset to image               */
   UINT              PageNumber,       /* Page to get tile number for   */
   LPUINT            lpTileRows,       /* Number of Tile in a row       */
   LPUINT            lpTileCols        /* Number of Tile in a col       */
   );

AT_ERRCOUNT ACCUAPI IG_tile_count_get_mem(

   LPVOID            lpImage,          /* Address of image in memory    */
   DWORD             dwImageSize,		/* Size of image in memory       */
   UINT              PageNumber,       /* Page to get tile number for   */
   LPUINT            lpTileRows,       /* Number of Tile in a row       */
   LPUINT            lpTileCols        /* Number of Tile in a col       */
   );

AT_ERRCOUNT ACCUAPI IG_load_size_set(

   AT_DIMENSION    nWidth,       /* Width of image, after load    */
   AT_DIMENSION    nHeight       /* Height of image, after load   */
   );

AT_ERRCOUNT ACCUAPI IG_load_size_get(

   LPAT_DIMENSION lpWidth,       /* Width of image, after load    */
   LPAT_DIMENSION lpHeight       /* Height of image, after load   */
   );

AT_ERRCOUNT ACCUAPI IG_load_color_reduction_set(

   UINT        nBitsPerPixel  /* Depth of image, after load    */
   );

AT_ERRCOUNT ACCUAPI IG_load_color_reduction_get(

   LPUINT   lpBitsPerPixel    /* Depth of image, after load    */
   );

AT_ERRCOUNT ACCUAPI IG_load_rect_set(

   AT_PIXPOS      x,             /* X Coordinate of rectangle     */
   AT_PIXPOS      y,             /* Y Coordinate of rectangle     */
   AT_DIMENSION   nWidth,        /* Width of rectangle            */ 
   AT_DIMENSION   nHeight        /* Height of rectangle           */
   );

AT_ERRCOUNT ACCUAPI IG_load_rect_get(

   LPAT_PIXPOS    lpX,           /*X    Coordinate of rectangle   */
   LPAT_PIXPOS    lpY,           /*Y    Coordinate of rectangle   */
   LPAT_DIMENSION lpWidth,       /* Width of rectangle            */
   LPAT_DIMENSION lpHeight       /* Height of rectangle           */
   );

AT_ERRCOUNT ACCUAPI IG_load_auto_detect_set(

   AT_MODE  nType,            /* Type of image to toggle       */
   BOOL     bToggle           /* TRUE - enable auto detect     */
   );

AT_ERRCOUNT ACCUAPI IG_load_auto_detect_get(

   AT_MODE  nType,            /* Type of image to toggle       */
   LPBOOL   lpToggle          /* TRUE - enable auto detect     */
   );

AT_ERRCOUNT ACCUAPI IG_load_tag_CB_register(

   LPFNIG_TAG_SET lpfnTagGet, /* Tag Get callback              */
   LPVOID         lpPrivate   /* Callback private data         */
   );

AT_ERRCOUNT ACCUAPI IG_save_file(

   HIGEAR      hIGear,        /* Image handle to save          */
   const LPSTR lpszFileName,  /* File name of image to load    */
   AT_LMODE    lFormatType    /* File format to save as        */
   );

AT_ERRCOUNT ACCUAPI IG_save_mem(

   HIGEAR   hIGear,             /* Image handle to save         */
   LPVOID   lpImage,            /* Address to save image        */
   DWORD		dwImageSize,		  /* Size of image (if exists)	 */
   DWORD    dwBufferSize,       /* Size of memory block         */
   UINT     nPage,              /* Page number to save as       */
   UINT     nReserved,          /* Always set to 0 (for now)    */
   AT_LMODE lFormatType,        /* File format to save as       */
   LPDWORD	lpActualSize		  /* Size of new file in memory	 */
   );

AT_ERRCOUNT ACCUAPI IG_save_FD(

   HIGEAR   hIGear,        /* Image handle to save      */
   INT      fd,            /* File descriptor           */
   UINT     nPage,         /* Page number to save as    */
   UINT     nReserved,     /* Always set to 0 (for now) */
   AT_LMODE lFormatType    /* File format to save as    */
   );

AT_ERRCOUNT ACCUAPI IG_save_FD_CB(

   INT               fd,            /* File descriptor               */
   UINT              nPage,         /* Page number to save as        */
   UINT              nReserved,     /* Always set to 0 (for now)     */
   AT_LMODE          lFormatType,   /* File format to save as        */
   LPFNIG_RASTER_GET lpfnRasterGet, /* Called for each raster line   */
   LPFNIG_DIB_GET    lpfnDIBGet,    /* Called when header is saved   */
   LPVOID            lpPrivateData  /* Callback data                 */
   );

AT_ERRCOUNT ACCUAPI IG_save_mem_CB(

   LPVOID            lpImage,       /* Address to save image         */
   DWORD					dwImageSize,	/* Size of image (if exists)		*/
   DWORD    			dwBufferSize,  /* Size of memory block				*/
   UINT              nPage,         /* Page number to save as        */
   UINT              nReserved,     /* Always set to 0 (for now)     */
   AT_LMODE          lFormatType,   /* File format to save as        */
   LPFNIG_RASTER_GET lpfnRasterGet, /* Called for each raster line   */
   LPFNIG_DIB_GET    lpfnDIBGet,    /* Called when header is saved   */
   LPVOID            lpPrivateData, /* Callback data                 */
   LPDWORD				lpActualSize	/* Size of new file in memory		*/
   );

AT_ERRCOUNT ACCUAPI IG_save_tag_CB_register(

   LPFNIG_TAG_GET       lpfnTagGet,       /* Tag Set callback            */
   LPFNIG_TAG_USER_GET  lpfnTagUserGet,   /* Tag User Get callback       */
   LPVOID               lpPrivate         /* Callback private data       */
   );

AT_ERRCOUNT ACCUAPI IG_save_thumbnail_set(

   BOOL        	bToggle,    /* TRUE - enable thumbnails   */
   AT_DIMENSION   nWidth,     /* Width of rectangle         */ 
   AT_DIMENSION   nHeight     /* Height of rectangle        */
   );

AT_ERRCOUNT ACCUAPI IG_save_file_size_calc(

   HIGEAR      hIGear,        /* Image handle to save          */
   AT_LMODE    lFormatType,   /* File format to save as        */
   LPLONG      file_size      /* Returned worst case file size */
   );

AT_ERRCOUNT ACCUAPI IG_display_LUT_set(

   HIGEAR         	hIGear,     /* Image handle            */ 
   const LPAT_PIXEL  lpRLUT,     /* Red component of table  */
   const LPAT_PIXEL  lpGLUT,     /* Green component of table*/ 
   const LPAT_PIXEL  lpBLUT      /* Blue component of table */
   );

AT_ERRCOUNT ACCUAPI IG_display_LUT_get( 

   HIGEAR   	hIGear,     /* Image handle            */ 
   LPAT_PIXEL  lpRLUT,     /* Red component of table  */
   LPAT_PIXEL  lpGLUT,     /* Green component of table*/ 
   LPAT_PIXEL  lpBLUT      /* Blue component of table */
   );

AT_ERRCOUNT ACCUAPI IG_display_angle_set(

   HIGEAR   hIGear,     /* Image handle               */ 
   AT_MODE  nAngle      /* 0, 90, 180 or 270 degrees  */
   );

AT_ERRCOUNT ACCUAPI IG_display_angle_get( 

   HIGEAR         hIGear,  /* Image handle               */ 
   LPAT_MODE      lpAngle  /* 0, 90, 180 or 270 degrees  */
   );

AT_ERRCOUNT ACCUAPI IG_display_contrast_set(

   HIGEAR   hIGear,           /* Image handle                  */ 
   DOUBLE   dblContrast,      /* normal is 1.0, <0 is invert   */
   DOUBLE   dblBrightness,    /* normal is 0.0, <0 is darken   */
   DOUBLE   dblGamma          /* values are > 0.0              */
   );

AT_ERRCOUNT ACCUAPI IG_display_dither_mode_set(

   HIGEAR   hIGear,           /* Image handle         */ 
   AT_MODE  nDitherMode       /* Bayer or none        */
   );

AT_ERRCOUNT ACCUAPI IG_display_dither_mode_get( 

   HIGEAR      hIGear,        /* Image handle      */ 
   LPAT_MODE   lpDitherMode   /* Bayer or none  .  */ 
   );

AT_ERRCOUNT ACCUAPI IG_display_alias_set(

   HIGEAR      hIGear,        /* Image handle               */ 
   AT_MODE     nAliasType,    /* Anti-alias method          */
   UINT        nThreshold,    /* Anti-alias threshold       */
   BOOL        bSubSample     /* TRUE - use subsampling     */
   );

AT_ERRCOUNT ACCUAPI IG_display_alias_get(

   HIGEAR      hIGear,        /* Image handle               */ 
   LPAT_MODE   lpAliasType,   /* Anti-alias method          */
   LPUINT      lpThreshold,   /* Anti-alias threshold       */
   LPBOOL      lpSubSample    /* TRUE - use subsampling     */
   );

AT_ERRCOUNT ACCUAPI IG_display_ROP_set(

   HIGEAR      hIGear,        /* Image handle               */ 
   AT_LMODE    lROP           /* Raster operation           */
   );

AT_ERRCOUNT ACCUAPI IG_display_ROP_get(

   HIGEAR      hIGear,        /* Image handle               */ 
   LPAT_LMODE  lpROP          /* Raster operation           */
   );

AT_ERRCOUNT ACCUAPI IG_display_scrollbar_set(

   HIGEAR         hIGear,        /* Image handle              */ 
   BOOL           bEnable        /* TRUE - enable scrollbars  */
   );

AT_ERRCOUNT ACCUAPI IG_display_scrollbar_get(

   HIGEAR          hIGear,        /* Image handle               */ 
   LPBOOL          lpEnable       /* TRUE - scrollbars enabled  */
   );

AT_ERRCOUNT ACCUAPI IG_display_transparent_set(

   HIGEAR         hIGear,        /* Image handle               */ 
   const LPAT_RGB lpRGB,         /* Transparent color          */
   BOOL           bEnable        /* TRUE - enable transparency */
   );

AT_ERRCOUNT ACCUAPI IG_display_transparent_get(

   HIGEAR         hIGear,        /* Image handle               */ 
   LPAT_RGB       lpRGB,         /* Transparent color return   */
   LPBOOL         lpEnabled      /* TRUE - transparncy enabled */
   );

AT_ERRCOUNT ACCUAPI IG_display_animation_delay_set(

   HIGEAR         hIGear,        /* Image handle                     */
   UINT           nDelay         /* Animation delay in milli secs    */
   );

AT_ERRCOUNT ACCUAPI IG_display_animation_delay_get(

   HIGEAR         hIGear,        /* Image handle               */ 
   LPUINT         lpDelay        /* Animation delay return     */
   );

AT_ERRCOUNT ACCUAPI IG_display_LUT_clear(

   HIGEAR      hIGear         /* Image handle               */
   );

AT_ERRCOUNT ACCUAPI IG_device_rect_get(

   HIGEAR      hIGear,        /* Image handle               */ 
   LPAT_RECT   lpRect         /* Current display rectangle  */
   );

AT_ERRCOUNT ACCUAPI IG_device_rect_set(

   HIGEAR            hIGear,  /* Image handle               */ 
   const LPAT_RECT   lpRect   /* Current display rectangle  */
   );

AT_ERRCOUNT ACCUAPI IG_image_rect_get(

   HIGEAR            hIGear,  /* Image handle               */ 
   LPAT_RECT         lpRect   /* Current viewport rectangle */
   );

AT_ERRCOUNT ACCUAPI IG_image_rect_set(

   HIGEAR            hIGear,  /* Image handle               */ 
   const LPAT_RECT   lpRect   /* Current viewport rectangle */
   );

AT_ERRCOUNT ACCUAPI IG_display_zoom_set(

   HIGEAR            hIGear,        /* Image handle                  */ 
   HWND              hWnd,          /* Display window handle         */
   UINT              nZoomLevel,    /* Zoom level                    */
   const LPAT_RECT   lprcReference  /* Reference rectangle to zoom   */
   );

AT_ERRCOUNT ACCUAPI IG_display_zoom_rect_set(

   HIGEAR            hIGear,        /* Image handle                  */ 
   HWND              HWND,          /* Display window handle         */
   const LPAT_RECT   lprcZoom,      /* Screen rect. to zoom in on    */
   LPUINT            lpZoomLevel,   /* New zoom level                */ 
   LPAT_RECT         lprcReference  /* New reference rectangle       */
   );

AT_ERRCOUNT ACCUAPI IG_display_handle_resize(

   HIGEAR         hIGear,           /* Image handle                  */ 
   HWND           HWND,             /* Display window handle         */
   LPAT_RECT      lprcReference,    /* New reference rectangle       */ 
   LPUINT         lpZoomLevel       /* New zoom level                */ 
   );

AT_ERRCOUNT ACCUAPI IG_display_handle_palette(

   HIGEAR      hIGear,     /* Image handle                  */ 
   HWND        HWND,       /* Display window handle         */
   AT_MODE     nPriority,  /* Palette priority              */
   LPBOOL      lpRealized  /* TRUE - palette was realized   */
   );

AT_ERRCOUNT ACCUAPI IG_display_palette_state_get(

   HIGEAR      hIGear,           /* Image handle               */ 
   LPBOOL      lpPaletteChanged  /* TRUE - palette was changed */
   );

AT_ERRCOUNT ACCUAPI IG_display_centered_get(
         
   HIGEAR      hIGear,     /* Image handle                  */ 
   LPBOOL      lpCenter    /* Center image in window flag   */
   );

AT_ERRCOUNT ACCUAPI IG_display_centered_set(
         
   HIGEAR      hIGear,     /* Image handle                  */ 
   HWND        HWND,       /* Display window handle         */
   BOOL        fCenter     /*C   enter image in window flag */
   );

AT_ERRCOUNT ACCUAPI IG_display_stretch_get(

   HIGEAR      hIGear,     /* Image handle                  */
   LPBOOL      lpStretch   /* Stretch image on resize       */
   );

AT_ERRCOUNT ACCUAPI IG_display_stretch_set(

   HIGEAR      hIGear,     /* Image handle                  */
   BOOL        fStretch    /* Stretch image on resize       */
   );

AT_ERRCOUNT ACCUAPI IG_display_PPM_correct_get(

   HIGEAR      hIGear,     /* Image handle                    */
   LPBOOL      lpToggle    /* Display with correct PPM (DPI)  */
   );

AT_ERRCOUNT ACCUAPI IG_display_PPM_correct_set(

   HIGEAR      hIGear,     /* Image handle                    */
   BOOL        fToggle     /* Display with correct PPM (DPI)  */
   );

AT_ERRCOUNT ACCUAPI IG_display_fit_method(
         
   HIGEAR      hIGear,        /* Image handle                  */ 
   HWND        HWND,          /* Display window handle         */
   LPAT_RECT   lprcReference, /* New reference rectangle       */ 
   LPUINT      lpZoomLevel,   /* New zoom level                */ 
   AT_MODE     nFitMethod     /*F   it mode setting            */
   );

AT_ERRCOUNT ACCUAPI IG_display_aspect_ratio_get(

   HIGEAR      hIGear,        /* Image handle                  */
   LPAT_MODE   lpAspectRatio  /* Aspect ratio setting          */
   );

AT_ERRCOUNT ACCUAPI IG_display_aspect_ratio_set(

   HIGEAR      hIGear,        /* Image handle                  */
   AT_MODE     nAspectRatio   /* Aspect ratio setting          */
   );

AT_ERRCOUNT ACCUAPI IG_display_palette_create(

   HIGEAR         hIGear,     	/* Image handle                  */ 
   HPALETTE FAR	*lpPalette   	/* Logical palette return        */
   );

AT_ERRCOUNT ACCUAPI IG_display_scroll_image(

   HIGEAR      hIGear,           /* Image handle            */ 
   HWND        hWnd,             /* Window to scroll        */
   AT_MODE     nScrollBar,       /* Direction Horz or Vert  */
   UINT        nThumbPos,        /* Position of scroll thumb*/ 
   AT_MODE     nScrollCode       /* Type of scroll          */
   );

AT_ERRCOUNT ACCUAPI IG_display_desktop_pattern_set(

   HIGEAR         hIGear,        /* Image handle               */ 
   HBITMAP        hPattern,      /* Background pattern to use  */
   const LPAT_RGB lpForeground,  /* Color of foreground        */
   const LPAT_RGB lpBackground,  /* Color of background        */
	BOOL				bEnable			/* TRUE - desktop enabled		*/
   );

AT_ERRCOUNT ACCUAPI IG_display_desktop_pattern_get(

   HIGEAR         hIGear,        /* Image handle               */ 
   HBITMAP FAR		*lpPattern,    /* Background pattern used    */
   LPAT_RGB       lpForeground,  /* Color of foreground        */
   LPAT_RGB       lpBackground,  /* Color of background        */
	LPBOOL			lpEnabled		/* TRUE - desktop enabled		*/
   );

AT_ERRCOUNT ACCUAPI IG_display_DDB(

   HDC            hDC,           /* Device to display DDB      */
   HBITMAP        hBitmap,       /* DDB to display             */
   HPALETTE       hPalette,      /* DDB's logical palette      */
   AT_PIXPOS      x,             /* X Coordinate to display at */
   AT_PIXPOS      y              /* Y Coordinate to display at */
   );

AT_ERRCOUNT ACCUAPI IG_image_create_DIB(

   AT_DIMENSION   nWidth,        /* Width of DIB               */ 
   AT_DIMENSION   nHeight,       /* Height of DIB              */
   UINT           nBitsPerPixel, /* Depth of the image         */
   LPAT_DIB       lpDIB,         /* NULL to create an empty DIB*/
   LPHIGEAR       lphIGear       /* Image handle returned      */
   );

AT_ERRCOUNT ACCUAPI IG_image_create_DDB(

   HIGEAR         	hIGear,        /* Image handle               */ 
   AT_DIMENSION      nWidth,        /* Width of DIB               */ 
   AT_DIMENSION      nHeight,       /* Height of DIB              */
   HBITMAP FAR			*lpDDB,         /* New DDB                    */
   HPALETTE FAR		*lpPalette      /* New palette, or pass NULL  */
   );                            

AT_ERRCOUNT ACCUAPI IG_image_import_DIB(

   const LPAT_DIB lpDIB,         /* DIB to import              */
   LPHIGEAR       lphIGear       /* Image handle returned      */
   );

AT_ERRCOUNT ACCUAPI IG_image_import_DDB(

   HBITMAP     hDDB,             /* DDB to import           */
   HPALETTE    hPalette,         /* Palette of DDB          */
   LPHIGEAR    lphIGear          /* Image handle returned   */
   );

AT_ERRCOUNT ACCUAPI IG_image_export_DIB(

   HIGEAR         hIGear,      /* Image handle to delete     */
   LPAT_DIB FAR 	*lpDIB       /* Exported DIB returned      */
   );

AT_ERRCOUNT ACCUAPI IG_image_export_DDB(

   HIGEAR         hIGear,      /* Image handle to delete     */
   HBITMAP FAR 	*lpDDB,      /* Exported DDB               */ 
   HPALETTE FAR 	*lpPalette   /* Exported Palette           */ 
   );

AT_ERRCOUNT ACCUAPI IG_image_compression_type_get(
   
   HIGEAR       hIGear,        /* Image handle                  */ 
   LPDWORD      lpCompression  /* Compression type              */
   );

AT_ERRCOUNT ACCUAPI IG_image_is_gray(
                            
   HIGEAR   hIGear,           /* Image handle                   */
   LPBOOL   lpIsImageGray     /* TRUE - Grayscale image         */
   );

AT_ERRCOUNT ACCUAPI IG_display_scroll_area_set(

   HIGEAR   hIGear,     /* ImageGear handle  */
   HWND     HWND        /* Display window    */
   );

AT_ERRCOUNT ACCUAPI IG_display_adjust_aspect(

   HIGEAR      hIGear,        /* ImageGear handle           */
   LPAT_RECT   lpRect,        /* Adjust for aspect ratio    */
   AT_MODE     nAspectMethod  /* Aspect ratio setting       */
   );

AT_ERRCOUNT ACCUAPI IG_display_device_to_image(

   HIGEAR      hIGear,        /* ImageGear handle           */
   LPAT_POINT  lpPoint,       /* Cnvt device to image point */
   UINT        nCount         /* Number of points to cnvert */
   );

AT_ERRCOUNT ACCUAPI IG_display_image_to_device(

   HIGEAR      hIGear,        /* ImageGear handle           */
   LPAT_POINT  lpPoint,       /* Cnvt device to image point */
   UINT        nCount         /* Number of points to cnvert */
   );

BOOL ACCUAPI IG_image_is_valid(
   
   HIGEAR   hIGear      /* ImageGear handle     */
   );

AT_ERRCOUNT ACCUAPI IG_clipboard_copy(

   HIGEAR          hIGear,          /* ImageGear handle           */
   const LPAT_RECT lprcRegion       /* Rect. area of image to copy*/
   );

AT_ERRCOUNT ACCUAPI IG_clipboard_paste(

   LPHIGEAR        lphIGear         /* ImageGear handle return  */
   );

AT_ERRCOUNT ACCUAPI IG_clipboard_paste_available(

   LPBOOL          lpPasteStatus    /* TRUE - Ok to paste image   */
   );

AT_ERRCOUNT ACCUAPI IG_clipboard_dimensions(

   LPAT_DIMENSION    lpWidth,          /* Width of the image      */
   LPAT_DIMENSION    lpHeight,         /* Height of the image     */
   LPUINT         	lpBitsPerPixel    /* Depth of the image      */
   );

AT_ERRCOUNT ACCUAPI IG_clipboard_paste_merge(
           
   HIGEAR         hIGear,           /* ImageGear handle           */
   AT_PIXPOS      nLeftPos,         /* X position of new image    */
   AT_PIXPOS      nTopPos           /* Y position of new image    */
   );    

AT_ERRCOUNT ACCUAPI IG_scan_source_select(
   
   HWND              HWND           /* Windows handle       */ 
   );

AT_ERRCOUNT ACCUAPI IG_scan_acquire(

   HWND              HWND,          /* Windows handle             */
   BOOL              bShowUI,       /* TRUE - enable UI           */
   LPHIGEAR          lphIGear       /* ImageGear handle returned  */
   );
      
AT_ERRCOUNT ACCUAPI IG_scan_pages(

   HWND              HWND,          /* Windows handle                */
   const LPSTR       lpFileName,    /* File name for output images   */
   AT_MODE           nFileType,     /* File type to save images      */
   BOOL              bShowUI        /* TRUE - enable UI              */
   ); 
      
VOID ACCUAPI IG_scan_capabilities_set(
           
   INT            BitsPixel,        /* bit depth of scanned image    */ 
   LPAT_DRECT     lpImageLayout,    /* image layout                  */
   INT            HorResolution,    /* horizontal resolution         */ 
   INT            VerResolution,    /* vertical resolution           */
   INT            Brightness,       /* brightness setting            */
   INT            Contrast          /* contrast setting              */
   );

VOID ACCUAPI IG_scan_driver_info_get(

   LPINT          lpTwain_major,    /* TWAIN major release number    */ 
   LPINT          lpTwain_minor     /* TWAIN minor release number    */
   );

AT_ERRCOUNT ACCUAPI  IG_IP_contrast_invert( 

   HIGEAR         hIGear,
   LPAT_RECT      lpRect,
   AT_MODE        nMethodMode       /* IG_CONTRAST_PALETTE, IG_CONTRAST_PIXEL */
   );

AT_ERRCOUNT ACCUAPI  IG_IP_contrast_adjust( 
   
   HIGEAR         hIGear,
   LPAT_RECT      lpRect,
   AT_MODE        nMethodMode,      /* IG_CONTRAST_PALETTE, IG_CONTRAST_PIXEL */
   DOUBLE         dblContrast, 
   DOUBLE         dblBrightness
   );

AT_ERRCOUNT ACCUAPI  IG_IP_contrast_gamma( 
   
   HIGEAR         hIGear,
   LPAT_RECT      lpRect,
   AT_MODE        nMethodMode,      /* IG_CONTRAST_PALETTE, IG_CONTRAST_PIXEL */
   DOUBLE         dblGamma
   );

AT_ERRCOUNT ACCUAPI  IG_IP_contrast_stretch( 

   HIGEAR         hIGear,
   LPAT_RECT      lpRect,
   AT_MODE        nMethodMode /* IG_CONTRAST_PALETTE, IG_CONTRAST_PIXEL */
   );

AT_ERRCOUNT ACCUAPI  IG_IP_contrast_equalize( 

   HIGEAR         hIGear,
   LPAT_RECT      lpRect,
   AT_MODE        nMethodMode /*I   G_CONTRAST_PALETTE, IG_CONTRAST_PIXEL */
   );

VOID ACCUAPI IG_error_get(

   INT            iErrorIndex,
   LPSTR          szFileName,    /* if set to NULL this value will not be set */
   INT            cbFileNameSize,/* size in bytes of szFileName               */
   LPINT          iLineNumber,   /* if set to NULL this value will not be set */
   LPAT_ERRCODE   iCode,         /* if set to NULL this value will not be set */
   LPLONG         lValue1,       /* if set to NULL this value will not be set */
   LPLONG         lValue2        /* if set to NULL this value will not be set */
   );

VOID ACCUAPI IG_error_clear(

   VOID
   );

AT_ERRCOUNT ACCUAPI IG_error_check(

   VOID
   );
         
AT_ERRCOUNT ACCUAPI  IG_IP_color_promote( 

   HIGEAR         hIGear,
   AT_MODE        to_8_or_24
   );

AT_ERRCOUNT ACCUAPI IG_IP_convert_to_gray(

   HIGEAR         hIGear         /* Source Image */
   );

AT_ERRCOUNT ACCUAPI IG_IP_color_reduce_octree(

   HIGEAR         hIGear,         /* Source Image */
   BOOL           fast_remap,
   UINT           max_colors
   );

AT_ERRCOUNT ACCUAPI IG_IP_color_reduce_popularity(

   HIGEAR         hIGear,        /* Source Image */
   BOOL           fast_remap,
   UINT           max_colors
   );

AT_ERRCOUNT ACCUAPI IG_IP_color_reduce_diffuse(

   HIGEAR         hIGear,        /* Source Image */
   UINT           to_bits,
   INT            level,
   LPAT_RGBQUAD   palette
   );

AT_ERRCOUNT ACCUAPI IG_IP_color_reduce_bayer(

   HIGEAR         hIGear,        /* Source Image */
   UINT           to_bits,
   LPAT_RGBQUAD   palette
   );

AT_ERRCOUNT ACCUAPI IG_IP_color_reduce_halftone(

   HIGEAR         hIGear,        /* Source Image */
   AT_MODE        options
   );

AT_ERRCOUNT ACCUAPI IG_IP_color_reduce_median_cut(

   HIGEAR         hIGear,            /* Source Image */
   BOOL           fast_remap,
   UINT           max_colors
   );

AT_ERRCOUNT ACCUAPI IG_IP_histo_tabulate(

   HIGEAR            hIGear,        /* Image to be histogramed             */
   LPDWORD           lpHisto,       /* Array of LONGS                      */
   UINT              number_of_bins,/* Number of bins in lpHisto           */
   const LPAT_RECT   lpRect,        /* Set to NULL for entire image        */
   UINT              segment_incr,  /* 0=every line, >0 skips lines (faster)*/
   AT_MODE           channel        /* IG_COLOR_COMP_ (Single onlye NO RGB)*/
   );

AT_ERRCOUNT ACCUAPI IG_IP_histo_clear(

   LPDWORD           lpHisto,       /* Array of LONGS                      */
   UINT              number_of_bins /* Number of bins in lpHisto           */
   );

AT_ERRCOUNT ACCUAPI IG_palette_get(
   
   HIGEAR            hIGear,        /* Image with palette to get                 */ 
   LPAT_RGBQUAD      lpPalette      /* Pointer to a location to copy the palette */
   );

AT_ERRCOUNT ACCUAPI IG_palette_set(
   
   HIGEAR               hIGear,     /* Image with palette to get                 */ 
   const LPAT_RGBQUAD   lpPalette   /* Pointer of a palette to copy to the image */
   );
   
AT_ERRCOUNT ACCUAPI IG_palette_entry_set(

   HIGEAR            hIGear,        /* Image with palette to alter               */
   const LPAT_RGB    lpRGB_entry,   /* A palette entry to place in the image pal */
   UINT              index          /* Index into image palette to place the RGBQ*/
   );
       
AT_ERRCOUNT ACCUAPI IG_palette_entry_get(

   HIGEAR         hIGear,        /* Image with palette to get entry from      */
   LPAT_RGB       lpRGB_entry,   /* An RGBQ to hold the palette entry copy    */
   UINT           index          /* Index into the palette of the desired RGBQ*/
   );

AT_ERRCOUNT ACCUAPI IG_palette_load(

   const LPSTR       lpszFileName,        /* File name of palette to load        */
   LPAT_RGBQUAD      lpPalette,           /* Image's palette                     */ 
   LPUINT            lpNnum_of_entries,   /* Num of RGBQs in lpPalette           */
   BOOL              BGR_order,           /* TRUE read raw as BGR instead of RGB */
   LPAT_MODE         lpFile_type          /* IG_PALETTE_FILE_FORMAT_             */
   );

AT_ERRCOUNT ACCUAPI IG_palette_save(

   const LPSTR       lpszFileName,     /* File name of palette to save  */
   LPAT_RGBQUAD      lpPalette,        /* Image's palette               */
   UINT              num_of_entries,   /* Num of RGBQs in lpPalette     */
   AT_MODE           file_type         /* IG_PALETTE_FILE_FORMAT_       */
   );

AT_ERRCOUNT ACCUAPI IG_IP_rotate_any_angle(

   HIGEAR         hIGear,        /* Image to be rotated                 */
   double         angle,         /* angle in degrees to rotate          */
   AT_MODE        rotate_mode    /* IG_ROTATE_CLIP & IG_ROTATE_EXPAND   */

   );

AT_ERRCOUNT ACCUAPI IG_IP_rotate_multiple_90(

   HIGEAR         hIGear,              /* Image to be rotated           */
   AT_MODE        mutliple_90_mode     /* IG_ROTATE_0 _90, _180, _270   */
   );       

AT_ERRCOUNT ACCUAPI IG_IP_flip(

   HIGEAR         hIGear,     /* Image to be flipped                    */
   AT_MODE        direction   /* IG_FLIP_HORIZONTAL, IG_FLIP_VERTICAL   */    
   );


/***************************************************************************/
/* ImageGear GUI function prototypes                                       */
/***************************************************************************/

#ifdef _WINDOWS

AT_ERRCOUNT ACCUAPI IG_GUI_window_create(

   HIGEAR         hIGear,     /* Image handle                    */ 
   HWND           hwndParent, /* Parent window handle            */ 
   const LPSTR    lpcszTitle, /* Window title                    */
   INT            x,          /* X Position of window            */
   INT            y,          /* Y Position of window            */
   INT            nWidth,     /* Width of window                 */ 
   INT            nHeight,    /* Height of window                */
   HWND FAR 		*lphwndImage /* Image window handle return      */
   );

AT_ERRCOUNT ACCUAPI IG_GUI_window_associate(

   HIGEAR         hIGear,     /* Image handle               */ 
   HWND           hwndImage,  /* Image window handle        */
   BOOL           fAssociate  /* Associate or Disassociate  */
   );

AT_ERRCOUNT ACCUAPI IG_GUI_window_CB_register(

   HWND                 hwndImage,     /* Image window handle               */
   LPFNIG_GUIWINDESTROY lpfnDestroy,   /* Called when window is destroyed   */
   LPVOID               lpPrivateData  /* Private data for CB func.         */
   );

AT_ERRCOUNT ACCUAPI IG_GUI_window_attribute_set(

   HWND						hwndImage,	   /* Image window handle					*/
   AT_MODE					nAttributeID,	/* ID of attribute to set				*/
   LPVOID 					lpData			/* Attribute data 						*/
   );

AT_ERRCOUNT ACCUAPI IG_GUI_window_attribute_get(

   HWND						hwndImage,	   /* Image window handle					*/
   AT_MODE					nAttributeID,	/* ID of attribute to get				*/
   LPVOID 					lpData			/* Attribute data 						*/
   );

AT_ERRCOUNT ACCUAPI IG_GUI_pan_window_create(

   HIGEAR         hIGear,     /* Image handle            */ 
   HWND           hwndParent, /* Parent window handle    */ 
   const LPSTR    lpcszTitle, /* Window title            */
   INT            x,          /* X position of window    */
   INT            y,          /* Y position of window    */
   INT            nWidth,     /* Width of window         */ 
   INT            nHeight,    /* Height of window        */
   HWND FAR			*lphwndPan  /* Pan window handle return*/
   );

AT_ERRCOUNT ACCUAPI IG_GUI_pan_track_mouse(

   HIGEAR         hIGear,     /* ImageGear handle           */ 
   HWND           hwndPan,    /* Image Window or pan window */
   INT            x,          /* X position of mouse click  */
   INT            y           /* Y position of mouse click  */
   );

AT_ERRCOUNT ACCUAPI IG_GUI_pan_update(

   HIGEAR         hIGear,     /* ImageGear handle              */ 
   HWND           hwndPan,    /* Window handle of pan window   */
   BOOL           fFullRepaint/* TRUE - Redraw image           */ 
   );

AT_ERRCOUNT ACCUAPI IG_GUI_magnify_window_create(

   HIGEAR         hIGear,        /* Image handle                  */ 
   HWND           hwndParent,    /* Parent window handle          */
   const LPSTR    lpcszTitle,    /* Window title                  */
   INT            x,             /* X Position of window          */
   INT            y,             /* Y Position of window          */
   INT            nWidth,        /* Width of window               */
   INT            nHeight,       /* Height of window              */
   HWND FAR			*lphwndMagnify /* Magnify window handle retrn   */
   );

AT_ERRCOUNT ACCUAPI IG_GUI_magnify_track_mouse(

   HIGEAR         hIGear,        /* Image handle                         */ 
   HWND           hwndMagnify,   /* Magnify window handle                */
   INT            x,             /* X position of mouse click            */
   INT            y              /* Y position of mouse click            */
   );

AT_ERRCOUNT ACCUAPI IG_GUI_magnify_update(

   HIGEAR         hIGear,        /* Image handle                         */ 
   HWND           hwndMagnify    /* Magnify window handle                */
   );

AT_ERRCOUNT ACCUAPI IG_GUI_palette_window_create(

   HIGEAR         hIGear,        /* Image handle                         */
   HWND           hwndParent,    /* Parent window handle                 */
   const LPSTR    lpcszTitle,    /* Window title                         */
   INT            x,             /* X Position of window                 */
   INT            y,             /* Y Position of window                 */
   INT            nWidth,        /* Width of window                      */
   INT            nHeight,       /* Height of window                     */
   HWND FAR			*lphwndPalette /* Palette window handle retrn          */
   );

AT_ERRCOUNT ACCUAPI IG_GUI_palette_update(

   HIGEAR          hIGear,       /* Image handle                         */
   HWND            hwndPalette   /* Palette window handle                */
   );                             

AT_ERRCOUNT ACCUAPI IG_GUI_palette_CB_register(

   HWND              hwndPalette,   /* Palette window handle         */
   LPFNIG_GUIPALETTE lpfnPalette,   /* Called when palette changes   */
   LPVOID            lpPrivateData  /* Private data for CB func.     */
   );

AT_ERRCOUNT ACCUAPI IG_GUI_select_track_mouse(

   HIGEAR            hIGear,        /* Image handle                  */
   HWND              hwndImage,     /* Image window                  */
   INT               x,             /* X position of mouse click     */
   INT               y,             /* Y position of mouse click     */
   LPFNIG_GUISELECT  lpfnSelect,    /* Called when rect created      */
   LPVOID            lpPrivateData  /* Private data for CB func.     */
   );

AT_ERRCOUNT ACCUAPI IG_GUI_thumbnail_window_create(

   HWND         hwndParent,         /* Parent window handle           */
   const LPSTR  lpcszTitle,         /* Window title                   */
   INT          x,                  /* X Position of window           */
   INT          y,                  /* Y Position of window           */
   INT          nWidth,             /* Width of window                */
   INT          nHeight,            /* Height of window               */
   HWND FAR     *lphwndThumbnail    /* Thumbnail window handle ret    */
   );

AT_ERRCOUNT ACCUAPI IG_GUI_thumbnail_file_append(

   HWND         hwndThumbnail,      /* Thumbnail window handle         */
   const LPSTR  lpcszFileName       /* Image file to append            */
   );

AT_ERRCOUNT ACCUAPI IG_GUI_thumbnail_CB_register(

   HWND                  hwndThumbnail,   /* Thumbnail window handle        */
   LPFNIG_GUITHUMBSELECT lpfnThumbSelect, /* Called when thumbnail selected */
   LPVOID                lpPrivateData    /* Private data for CB func.      */
   );

AT_ERRCOUNT ACCUAPI IG_GUI_thumbnail_sort(

   HWND                 hwndThumbnail,    /* Thumbnail window handle        */
   LPFNIG_GUITHUMBCOMP  lpfnThumbCompare, /* Thumbnail compare callback     */
   LPVOID               lpPrivateData     /* Private data for CB func.      */
   );

AT_ERRCOUNT ACCUAPI IG_GUI_thumbnail_dir_append(

   HWND              hwndThumbnail,       /* Thumbnail window handle       */
   const LPSTR       lpcszDirectory,      /* Thumbnail directory           */
   const LPSTR       lpcszFilter          /* Thumbnail file filter         */
   );

AT_ERRCOUNT ACCUAPI IG_GUI_thumbnail_update(

   HWND        hwndThumbnail        /* Thumbnail window handle         */
   );


/* #ifdef _WINDOWS */
#endif


AT_ERRCOUNT ACCUAPI IG_IP_crop(

   HIGEAR      hIGear,           /* Image to crop     */
   LPAT_RECT   lpCrop_rect       /* Rectangle to keep */
   );

AT_ERRCOUNT ACCUAPI IG_IP_thumbnail_create(

   HIGEAR      	hOriginalImage,
   LPHIGEAR    	lphNewThumbnail,
   AT_DIMENSION   new_width, 
   AT_DIMENSION   new_height,
   AT_MODE     	interpolation  
   );
      
AT_ERRCOUNT ACCUAPI IG_IP_resize(

   HIGEAR      	hIGear,        
   AT_DIMENSION   new_width, 
   AT_DIMENSION   new_height,
   AT_MODE     	interpolation  
   );

AT_ERRCOUNT ACCUAPI IG_IP_sharpen(

   HIGEAR          hIGear, 
   const LPAT_RECT lpRect,
   const INT       sharpness_factor
   );
      
AT_ERRCOUNT ACCUAPI IG_IP_smooth(

   HIGEAR          hIGear,
   const LPAT_RECT lpRect, 
   const INT       smooth_factor
   );

AT_ERRCOUNT ACCUAPI IG_IP_edge_map(

   HIGEAR          hIGear,
   const LPAT_RECT lpRect,
   const AT_MODE   edge_map_type
   );
      
AT_ERRCOUNT ACCUAPI IG_IP_despeckle(

   HIGEAR          hIGear,    /* 1-bit image to despeckle               */
   const LPAT_RECT lpRect     /* rectangle to process, NULL for all     */
   );

AT_ERRCOUNT ACCUAPI IG_IP_median(

   HIGEAR            hIGear,
   const LPAT_RECT   lpRect,
   AT_DIMENSION   	width,
   AT_DIMENSION   	height
   );

AT_ERRCOUNT ACCUAPI IG_DIB_raster_size_get(

   HIGEAR      		hIGear,
	AT_MODE				format,	/* IG_PIXEL_ 										*/
   LPAT_DIMENSION 	lpSize	/* Returned size in bytes 						*/
	);

AT_ERRCOUNT ACCUAPI IG_DIB_area_size_get(

   HIGEAR      		hIGear,
	LPAT_RECT			lpRect,
	AT_MODE				format,	/* IG_DIB_AREA_ 									*/
   LPAT_DIMENSION 	lpSize	/* Returned size in bytes 						*/
	);

AT_ERRCOUNT ACCUAPI IG_DIB_pixel_set(

   HIGEAR      		hIGear,     /* Image to set pixel into                */
   AT_PIXPOS  		   xpos,       /* X coord  (0 to width-1)                */
   AT_PIXPOS	      ypos,       /* Y coord  (0 to height-1)               */
   const LPAT_PIXEL  lpPixel     /* Pointer to pixel data to write         */
   );

AT_ERRCOUNT ACCUAPI IG_DIB_pixel_get(

   HIGEAR     		hIGear,        /* Image to get pixel from                */
   AT_PIXPOS      xpos,          /* X coord  (0 to width-1)                */
   AT_PIXPOS      ypos,          /* Y coord  (0 to height-1)               */
   LPAT_PIXEL     lpPixel        /* memory to hold pixel data              */
   );

AT_ERRCOUNT ACCUAPI IG_DIB_line_set(

   HIGEAR 	   	  hIGear,        /* Image to set line into                 */
   AT_PIXPOS 	     x1,            /* First x coord                          */
   AT_PIXPOS 	     y1,            /* First y coord                          */
   AT_PIXPOS 	     x2,            /* Second x coord                         */
   AT_PIXPOS 	     y2,            /* Second y coord                         */
   const LPAT_PIXEL lpPixel,       /* Array of pixs to set, RGB order for 24 */
   AT_DIMENSION	  num_of_pixels  /* Number of pixel in lpPixel (not bytes) */
   );

AT_ERRCOUNT ACCUAPI IG_DIB_line_get(

   HIGEAR      			hIGear,        /* Image to get line from                 */
   AT_PIXPOS      		x1,            /* First x coord                          */
   AT_PIXPOS      		y1,            /* First y coord                          */
   AT_PIXPOS      		x2,            /* Second x coord                         */
   AT_PIXPOS      		y2,            /* Second y coord                         */
   LPAT_PIXEL     		lpPixel,       /* Array of pixs to get, RGB order for 24 */
   const AT_DIMENSION	len_of_array,  /* Length of lpPixel block in bytes       */
   LPAT_DIMENSION 		lpNum_of_pixels   /* Number of pixels read (not bytes)   */
   );

AT_ERRCOUNT ACCUAPI IG_DIB_column_set(

   HIGEAR				hIGear,        /* Image to set column of pixels into     */
   AT_PIXPOS 	     	x,             /* First x coord                          */
   AT_PIXPOS 	     	y1,            /* First y coord (-1 for whole height)    */
   AT_PIXPOS 	     	y2,            /* Second y coord - if needed             */
   const LPAT_PIXEL 	lpPixel,       /* Array of pixs to set, RGB order for 24 */
   AT_DIMENSION	  	num_of_pixels  /* Number of pixel in lpPixel (not bytes) */
   );

AT_ERRCOUNT ACCUAPI IG_DIB_column_get(

   HIGEAR      	hIGear,			/* Image to get column of pixels from		*/
   AT_PIXPOS      x, 				/* First x coord									*/
   AT_PIXPOS      y1, 				/* First y coord (-1 for whole height)		*/
   AT_PIXPOS      y2, 				/* Second y coord - if needed					*/
   LPAT_PIXEL     lpPixel,			/* Array of pixs to get, RGB order for 24	*/
   AT_DIMENSION	len_of_array,	/* Length of lpPixel block in bytes			*/
   LPAT_DIMENSION	lpNum_of_pixels	/* Number of pixels read (not bytes)	*/
   );

AT_ERRCODE ACCUAPI IG_DIB_raster_get( 

   HIGEAR      	hIGear,     /* Image to get raster from                  */
   AT_PIXPOS      ypos,       /* Y location in image of the desired raster */
	LPAT_PIXEL		lpPixel,
	AT_MODE			format	/* IG_PIXEL_UNPACKED, IG_PIXEL_PACKED(padded) */
   );

AT_ERRCOUNT ACCUAPI	IG_DIB_raster_set( 

	HIGEAR			hIGear,
	AT_PIXPOS		ypos,
	LPAT_PIXEL		lpPixel,
	AT_MODE			format	/* IG_PIXEL_UNPACED, IG_PIXEL_PACKED(padded) */	
	);

AT_ERRCOUNT ACCUAPI IG_DIB_row_get(

   HIGEAR      	hIGear,     /* Image to get row from                     */
   AT_PIXPOS      x,          /* X of the row (-1 for entire raster)       */
   AT_PIXPOS      y,          /* Y of the row                              */
   AT_DIMENSION   length,     /* Length in pixels - if needed              */
   LPVOID      	lpPix_data, /* array to hold read pixels                 */
	AT_MODE			format		/* IG_PIXEL_*											*/
   );

AT_ERRCOUNT ACCUAPI IG_DIB_row_set(

   HIGEAR         	hIGear,     /* Image to set row into                  */
   AT_PIXPOS         x,          /* X on the row to start -1 for whole row */
   AT_PIXPOS         y,          /* Y of the row to set                    */
   AT_DIMENSION      length,     /* Length of the row to set in pixels     */
   const LPVOID   	lpPix_data, /* array of data to set                   */
	AT_MODE				format		/* IG_PIXEL_*											*/
   );

AT_ERRCOUNT ACCUAPI IG_DIB_area_set(

   HIGEAR            hIGear,     /* Image to set an area of pixel       */
   const LPAT_RECT   lpRect,     /* Rectangle to set                    */
   const LPAT_PIXEL  lpPixel,    /* Array of pixel data to set          */
   AT_MODE           format      /* Format of the data IG_DIB_AREA_     */
   );

AT_ERRCOUNT ACCUAPI IG_DIB_area_get(

   HIGEAR            hIGear,     /* Image to get pixel block from       */
   const LPAT_RECT   lpRect,     /* rect to get (NULL for whole image)  */
   LPAT_PIXEL        lpPixel,    /* block of mem to receive pixels      */
   AT_MODE           format      /* IG_DIB_AREA_                        */
   );

AT_ERRCOUNT ACCUAPI IG_DIB_area_get_info(

	HIGEAR				hIGear,		/* Image to get pixel block from 		*/
   const LPAT_RECT	lpRect,		/* rect to get (NULL for whole image) 	*/
   LPAT_PIXEL			lpPixel,		/* block of mem to receive pixels 		*/
   AT_MODE				channel,		/* IG_COLOR_COMP_								*/
   AT_MODE				info			/* IG_DIB_AREA_INFO_							*/
   );

AT_ERRCOUNT ACCUAPI  IG_FX_blur(

   HIGEAR            hIGear,     /* Image to blur                       */
   const LPAT_RECT   lpRect,     /* rect to process, NULL for whole     */
   const AT_MODE     blur_mode   /* IG_BLUR_                            */
   );

AT_ERRCOUNT ACCUAPI IG_FX_diffuse(

   HIGEAR            hIGear,        /* Image to diffuse                 */
   const LPAT_RECT   lpRect,        /* rect to process, NULL for whole  */
   const UINT        amount         /* amount to diffuse 1-16           */
   );

AT_ERRCOUNT ACCUAPI IG_FX_emboss(

   HIGEAR            hIGear,     /* Image to emboss                     */ 
   const LPAT_RECT   lpRect,     /* rect to process, NULL for whole     */
   const DOUBLE      strength,   /* strength of the result 0.1 to 5.0 	*/
   const AT_MODE     compass_direction    /* IG_COMPASS_*               */
   );

AT_ERRCOUNT ACCUAPI IG_FX_motion(

   HIGEAR            hIGear,        /* image to directionally blur      */
   const LPAT_RECT   lpRect,        /* rect to process, NULL for whole  */
   const UINT        extent,        /* num of pixel to smear 1-7			*/
   const	AT_MODE		direction    	/* IG_COMPASS_*               		*/
   );         
                 
AT_ERRCOUNT ACCUAPI IG_FX_noise(

   HIGEAR            hIGear,
   const LPAT_RECT   rect,
   const WORD        type,          /* IG_NOISE_                        */
   const DOUBLE      strength,      /* 0.1 - 127.0                      */
   const INT         hit_rate,      /* 1 - 500                          */
   const DOUBLE      sigma,         /* 0.1 - 25.0                       */
   const WORD        rgb            /* IG_COLOR_COMP_                   */
   );

AT_ERRCOUNT ACCUAPI  IG_FX_pixelate(

   HIGEAR            	hIGear,
   const LPAT_RECT   	rect,             
   const AT_DIMENSION   x_res,         /* 2 - image_width                  */
   const AT_DIMENSION   y_res,         /* 2 - image_height                 */
   const AT_MODE     	input_mode,    /* IG_RESAMPLE_IN_                  */
   const AT_MODE     	output_mode,   /* IG_RESAMPLE_OUT_                 */
   const WORD        	radius,        /* 2 - image_height                 */
   const LPAT_RGB    	lpBackgroundColor /* rgb                           */ 
   );

AT_ERRCOUNT ACCUAPI IG_FX_spotlight(

   HIGEAR            	hIGear,        /* Image to place spotlight effect into   		*/
   const LPAT_RECT   	rect,
   const AT_PIXPOS      center_x,      /* 0-width-1 Center of spotlight x  				*/
   const AT_PIXPOS      center_y,      /* 0-height-1 Center of spotlight y 				*/
   const AT_DIMENSION   radius,        /* 2-height-2 radius in pixels of the spotlight */
   const UINT        	darken_by,     /* 2-height-2, amount to subtract from outside 	*/
   const AT_PIXEL       smoothing      /* 1-255, 0-sharp edge, >0 smooths edge    		*/
   );

AT_ERRCOUNT ACCUAPI IG_FX_watermark(

   HIGEAR            hIGear,        /* Image to watermark               		*/
   const LPAT_RECT   lpRect,        /* rect to process, NULL for whole  		*/
   const HIGEAR      hWatermark		/* 8-bit sign centered img to use for WM	*/
   );

AT_ERRCOUNT ACCUAPI IG_FX_posterize(

   HIGEAR            hIGear,        /* Image to posterize               	*/
   const LPAT_RECT   lpRect,
   const WORD        levels,        /* 1-255 Number of levels in result 	*/
   const AT_MODE     rgb            /* IG_COLOR_COMP_                   	*/
   );

AT_ERRCOUNT ACCUAPI IG_FX_texture(

   HIGEAR            hIGear,        /* Image to texture                 */
   const LPAT_RECT   lpRect,        /* rect to process, NULL for whole  */
   const HIGEAR      hIGearTexture  /* 8-bit small texture image        */
   );

AT_ERRCOUNT ACCUAPI IG_FX_twist(

   HIGEAR            hIGear,        /* Image to apply the twist FX to   */
   const LPAT_RECT   rect,
   const AT_MODE     twist_type,    /* IG_TWIST_*                       */
   const UINT        size           /* 2 - 50 size of square to twist   */
   );
      
AT_ERRCOUNT ACCUAPI  IG_FX_stitch(
   HIGEAR            hIGear,
   const LPAT_RECT   lpRect,
   const WORD        direction,     /* IG_COMPAS_ 								*/
   const DOUBLE      strength       /* 0.01 - 5.0                     	*/
   );

AT_ERRCOUNT ACCUAPI IG_FX_chroma_key(

   HIGEAR            hIGear,
   const LPAT_RECT   lpRect,
   const HIGEAR      hIGearBackground, /* must be equal in both (width, height, bitcount) as image          */
   const DOUBLE      hue_center,       /* 0-360.0 (note that 360.0==0.0 and that this is not an 8-bit HSI hue) */
   const DOUBLE      hue_range,        /* 0-359.9 must be less than 359.0 degrees                                       */
   const UINT        smooth,           /* 0-25 smooths the resulting blending functions 0-25                                                                */
   const UINT        intensity_thresh  /* 0-255 intensity values below this setting are not changed {0-255}          */
   );

AT_ERRCOUNT ACCUAPI IG_image_DIB_pntr_get(

   HIGEAR         hIGear,
   LPAT_DIB FAR	*lpDIB             /* Returned pointer to the DIB      */
   );

AT_ERRCOUNT ACCUAPI IG_image_DIB_palette_pntr_get(

   HIGEAR               hIGear,
   LPAT_RGBQUAD FAR		*lpRGBQ,    /* Returned pointer to the palette  */
   LPUINT               lpEntries   /* Returns # of entries             */
   );

AT_ERRCOUNT ACCUAPI IG_image_DIB_bitmap_pntr_get(

   HIGEAR         hIGear,
   LPAT_PIXEL FAR *lpBitmap /* Returned pointer to the 1st pixel*/
   );

AT_ERRCOUNT ACCUAPI IG_display_image_wipe(

   HIGEAR         hIGearBefore,     /* Image handle               */
   HIGEAR         hIGearAfter,      /* Image handle               */
   HWND           hWnd,             /* HWND                       */
   AT_MODE        nWipeStyle,       /* selected transition style  */
   LONG           granularity       /* size of each square region */
   );

AT_ERRCOUNT ACCUAPI IG_image_control_set(

   AT_MODE           nOption,       /* Image option ID            */
   LPVOID            lpData         /* Image option data          */
   );

AT_ERRCOUNT ACCUAPI IG_image_control_get(

   AT_MODE           nOption,       /* Image option ID            */
   LPVOID            lpData         /* Image option data return   */
   );

AT_ERRCOUNT ACCUAPI  IG_IP_swap_red_blue(

   HIGEAR      hIGear         /* 24 bit image to swapped red and blue   */
   );

AT_ERRCOUNT ACCUAPI  IG_IP_convert_runs_to_DIB( 

   HIGEAR      hIGear
   );

AT_ERRCOUNT ACCUAPI  IG_IP_convert_DIB_to_runs( 

   HIGEAR      hIGear
   );

AT_ERRCOUNT ACCUAPI  IG_IP_arithmetic( 

   HIGEAR      hIGearOp1,  /* Image 1 and destination                      */
   HIGEAR      hIGearOp2,  /* Image 2  (images must be same width & height)*/
   AT_MODE     operation   /* IG_ARITH_                                    */
   );

AT_ERRCOUNT ACCUAPI  IG_IP_color_combine( 

   LPHIGEAR    lphIGear_result,  /* A created image of the combined image  */
   HIGEAR      hIGear1,          /* Channel 1                              */
   HIGEAR      hIGear2,          /* Channel 2                              */
   HIGEAR      hIGear3,          /* Channel 3                              */
   HIGEAR      hIGear4,          /* Channel 4                              */
   AT_MODE     color_space       /* IG_COLOR_SPACE_                        */
   );

AT_ERRCOUNT ACCUAPI  IG_IP_color_separate( 

   HIGEAR      hIGear_original,  /* Original 24-bit image to be separated  */
   LPHIGEAR    lphIGear1,        /* Created channel 1                      */
   LPHIGEAR    lphIGear2,        /* Created channel 2                      */
   LPHIGEAR    lphIGear3,        /* Created channel 3                      */
   LPHIGEAR    lphIGear4,        /* Created channel 4                      */
   AT_MODE     color_space       /* IG_COLOR_SPACE_                        */
   );

AT_ERRCOUNT ACCUAPI  IG_IP_encrypt( 

   HIGEAR      hIGear,           /* Image to be coded                      */
   LPAT_RECT   lpRect,           /* region to code                         */
   AT_MODE     encrypt_type,     /* Encryption scheme IG_ENCRYPT_METHOD_   */
   const LPSTR lpPassword        /* Pointer to password string             */
   );

AT_ERRCOUNT ACCUAPI  IG_IP_decrypt( 

   HIGEAR      hIGear,           /* Image to be decoded                    */
   LPAT_RECT   lpRect,           /* region to decode                       */
   AT_MODE     encrypt_type,     /* Encryption scheme IG_ENCRYPT_METHOD_   */
   const LPSTR lpPassword        /* Pointer to password string             */
   );

AT_ERRCOUNT ACCUAPI IG_IP_blend_percent( 

	HIGEAR				hIGearDest,			/* Image 1 and destination							*/
	const	HIGEAR		hIGear2,				/* Image 2, must be same size and bit depth	*/
	const	DOUBLE		dblPctOfImage2,	/* 0-100.0 0=all of 1, 100=all of 2				*/
	const AT_MODE		nColorChannel		/* IG_COLOR_COMP_*									*/
   );

AT_ERRCOUNT ACCUAPI IG_IP_blend_with_LUT( 

	HIGEAR				hIGearDest,
	HIGEAR				hIGear2,
	const LPAT_LUT		lpLUT
	);

AT_ERRCOUNT ACCUAPI  IG_IP_transform_with_LUT( 

   HIGEAR      	hIGear,        /* Image to be transformed                   */
   LPAT_PIXEL     lpLUTr,        /* Transform for red or for >24-bit images   */
   LPAT_PIXEL     lpLUTg,        /* Transform for green                       */
   LPAT_PIXEL     lpLUTb         /* Transform for bluew                       */
   );

AT_ERRCOUNT ACCUAPI  IG_IP_pseudocolor_limits( 

   HIGEAR      hIGear,        /* 8g-bit Image to be colored                */
   LPAT_RGB    lpRGB_low,     /* Color to apply below low                  */
   LPAT_RGB    lpRGB_high,    /* Color to apply above high                 */
   AT_PIXEL    low,           /* Values below this are colored lpRGB_low   */
   AT_PIXEL    high           /* Values above this are colored lpRGB_high  */
   );

AT_ERRCOUNT ACCUAPI  IG_IP_pseudocolor_small_grads( 

   HIGEAR      hIGear,     /* 8g-bit Image to be colored                   */
   UINT        slope       /* 1 to 255, high values increase color faster  */
   );

AT_ERRCOUNT ACCUAPI IG_IP_deskew_rotate(

   HIGEAR      hIGear,					/* 1-bit image to be rotated						*/
   DOUBLE	   angle,					/* angle of rotation									*/
   AT_MODE	   speed_memory_option,	/* IG_SPEED_OVER_MEMORY,IG_MEMORY_OVER_SPEED	*/
   AT_MODE	   expand_clip_option	/* option: expand or clip new image				*/
   );

AT_ERRCOUNT ACCUAPI  IG_IP_deskew_auto( 

   HIGEAR      hIGear,
   DOUBLE	   angle_thresh,
   AT_MODE	   expand_clip_option
   );

AT_ERRCOUNT ACCUAPI  IG_IP_deskew_angle_find( 

	HIGEAR		hIGear,
	LPDOUBLE		angle
	);

AT_ERRCOUNT ACCUAPI IG_ext_load(

   const LPSTR    lpszExtension,    /* Extension file name        */
   const LPSTR    lpszLicensee,     /* Licensee name              */
   const LPSTR    lpszAuthorization /* License authorization code */
   );

AT_ERRCOUNT ACCUAPI IG_ext_unload(

   const LPSTR    lpszExtension     /* Extension file name        */
   );

AT_ERRCOUNT ACCUAPI IG_ext_info_get(

   const LPSTR    lpszExtension,    /* Extension file name           */
   LPSTR          lpszCompanyName,  /* Company Name                  */
   UINT           nCompanyNameSize, /* Size of company name buffer   */
	LPSTR				lpszCompileDate,	/* Compile date						*/
	UINT				nCompileDate,		/* Size of compile date buffer	*/
   LPINT          lpVersionMajor,   /* Major version number          */
   LPINT          lpVersionMinor,   /* Minor version number          */
   LPINT          lpVersionUpdate   /* Update (bug fix) number       */
   );

AT_ERRCOUNT ACCUAPI IG_ext_find_first(

   LPSTR          lpszExtension,    /* Extension file name           */
   UINT           nExtensionSize,   /* Size of extension name buffer */
   LPBOOL         lpFound           /* TRUE - lpszExtension filled   */
   );

AT_ERRCOUNT ACCUAPI IG_ext_find_next(

   LPSTR          lpszExtension,    /* Extension file name           */
   UINT           nExtensionSize,   /* Size of extension name buffer */
   LPBOOL         lpFound           /* TRUE - lpszExtension filled   */
   );

AT_ERRCOUNT ACCUAPI IG_IP_draw_frame(

	HIGEAR			hIGear, 					/* Image to be drawn into			*/
	AT_DIMENSION	width, 					/* Width of frame in pixels		*/
	AT_MODE			method,					/* IG_DRAW_FRAME_*					*/
	LPAT_PIXEL		lpColor					/* Pointer to RGB to be drawn		*/
	);

LONG ACCUAPI IG_convert_PPM_to_DPI(

	LONG		lPelsPerMeter
	);

LONG ACCUAPI IG_convert_DPI_to_PPM(

   LONG		lDotsPerInch
	);

AT_ERRCOUNT ACCUAPI IG_IP_convolve_matrix(

	HIGEAR		hIGear,
	LPAT_RECT	lpRect,				/* rectangle to process, if NULL	then all image	*/
	LPINT			lpMatrix,			/* array of kernel elements							*/
	UINT			nMatxWidth,			/* width of the array									*/
	UINT			nMatxHeight,		/* height of the array									*/
	DOUBLE		dblNormalizer,		/* normalizer of kernel									*/
	AT_MODE		nColorChannel,		/* IG_COLOR_COMP_*										*/
	AT_MODE		nResultForm,		/* IG_CONV_RESULT_*										*/
	BOOL			bAddToOrigin		/* if TRUE then add to origin else replace		*/
	);

AT_ERRCOUNT ACCUAPI  IG_IP_merge(

	HIGEAR		hImage1, 			/* original. image to accept merge			*/
	HIGEAR		hImage2, 			/* Image to be merged into higear. Same bit-depth as	higear*/
	LPAT_RECT	lpImageRect2, 		/* Area to be merged, NULL for whole thing*/
	AT_PIXPOS	nDstX, 				/* left start point of merge into higear	*/
	AT_PIXPOS	nDstY,				/* top start point of merge into higear	*/
	AT_MODE		operation			/* Method to use to merge	IG_ARITH_		*/
	);

AT_ERRCOUNT ACCUAPI IG_image_resolution_set(

      HIGEAR	hIGear,				/* Image who's resolution is to be altered*/
      LONG		XResNumerator,		/* Numerator of the X resolution value		*/
      LONG		XResDenominator,	/* Denominator of the X resolution value	*/
      LONG		YResNumerator,		/* Numerator of the Y resolution value		*/
      LONG		YResDenominator,	/* Denominator of the Y resolution value	*/
      AT_MODE	units					/* Units of resolution: IG_RESOLUTION_		*/
		);

AT_ERRCOUNT ACCUAPI IG_image_resolution_get(

      HIGEAR	hIGear,					/* Image who's resolution is retrieved		*/
      LPLONG	lpXResNumerator,		/* Numerator of the X resolution value		*/
      LPLONG	lpXResDenominator,	/* Denominator of the X resolution value	*/
      LPLONG	lpYResNumerator,		/* Numerator of the Y resolution value		*/
      LPLONG	lpYResDenominator,	/* Denominator of the Y resolution value	*/
      LPAT_MODE	lpUnits				/* Units of resolution: IG_RESOLUTION_		*/
		);


#ifdef __cplusplus
}
#endif

/* #ifndef __GEAR_H__ */
#endif
