/***************************************************************************/
/*                                                                         */
/* MODULE:    GEARESTR.H -  Master AccuSoft Error String File              */
/*                                                                         */
/*                                                                         */
/* Date created:        07/17/1996 SW 												   */
/*                                                                         */
/*    $Date$                                             */
/*    $Revision$                                                   */
/*                                                                         */
/*       Copyright 1996, AccuSoft Corporation.										*/
/*                                                                         */
/***************************************************************************/


#ifndef __GEARESTR_H__
#define __GEARESTR_H__

                         
typedef struct
   {
	AT_ERRCODE	ErrCode;
	LPSTR			ErrString;
	} ERROR_STRING;



const ERROR_STRING ErrString[] = 
{
IGE_SUCCESS,								"Success",
IGE_FAILURE,								"Failure",
IGE_NOT_DONE_YET,							"Not done yet",
IGE_NOT_IMPLEMENTED,						"Not implemented",
IGE_PRO_GOLD_FEATURE,					"Pro Gold feature",
IGE_ERROR_COMPRESSION,					"Compression error",
IGE_EXTENSION_NOT_LOADED, 				"ImageGear extension not present or could not be loaded",
IGE_INVALID_CONTROL_OPTION,  			"Invalid image control option ID",
IGE_INVALID_EXTENSION_MODULE,			"Specified ImageGear extension file is invalid",
IGE_EXTENSION_INITIALIZATION_FAILED, "Specified ImageGear extension was unable to initialize",
IGE_OUT_OF_MEMORY,						"Global memory has been depleated",
IGE_EVAL_DLL_TIMEOUT_HAS_EXPIRED,	"Evaluation version has expired - please contact AccuSoft",
IGE_INVALID_STANDARD_KERNEL,			"Kernel size is invalid",
IGE_INTERNAL_ERROR,						"An internal error has occurred",
IGE_INVALID_RECTANGLE,					"Rectangle values are invalid",
IGE_NO_CLIPBOARD_IMAGE_AVAILABLE,	"No image is available in clipboard",
IGE_CLIPBOARD_OPEN_FAILED,				"Clipboard open has failed",
IGE_SETCLIPBOARDDATA_FAILED,			"Could not put data into clipboard",
IGE_COULD_NOT_GET_DDB_DIMENSIONS,	"Could not get dimensions of DDB",
IGE_COULD_NOT_GET_DDB_BITS,			"Could not get DDB image data",
IGE_CREATE_BITMAP_FAILED,				"Could not create a new DDB",
IGE_COULD_DISPLAY_DDB,					"Could not display the DDB",
IGE_INVALID_PATTERN_BITMAP,			"Invalid DDB",
IGE_THUMBNAIL_NOT_PRESENT,				"This image does not contain a thumbnail",
IGE_THUMBNAIL_READ_ERROR,				"Read error occured while loading a thumbnail",
IGE_THUMBNAIL_NOT_SUPPORTED,			"This format does not support thumbnails",
IGE_PAGE_NOT_PRESENT,					"The specified page does not exist in this file",
IGE_PAGE_INVALID,							"The specified page is outside the valid range",
IGE_PAGE_COULD_NOT_BE_READ,			"The specified page could not be read",
IGE_CANT_DETECT_FORMAT,					"Could not detect the format of this file",
IGE_FILE_CANT_BE_OPENED,				"File open failed",
IGE_FILE_CANT_BE_CREATED,				"File create failed",
IGE_FILE_CANT_BE_CLOSED,				"File close failed",
IGE_FILE_TO_SMALL_TO_BE_BMFH,			"File too small to be a BMP",
IGE_FILE_IS_NOT_BMP,						"File is not a BMP",
IGE_FILE_TO_SMALL_TO_BE_BMIH,			"File too small to be valid",
IGE_BMP_IS_COMPRESSED,					"BMP image is compressed",
IGE_FILE_SIZE_WRITE_ERROR,				"BMP Could not write file size field to BMP",								
IGE_CANT_READ_PALETTE,					"Can't read palette",
IGE_CANT_READ_PIXELS,					"Can't read pixel data",
IGE_CANT_READ_HEADER,					"Can't read header",
IGE_INVALID_FILE_TYPE,					"Invalid file type",
IGE_INVALID_HEADER,						"Invalild file header",
IGE_CANT_WRITE_PALETTE,					"Can't write palette",
IGE_CANT_WRITE_PIXELS,					"Can't write pixel data",
IGE_CANT_WRITE_HEADER,					"Can't write header",
IGE_INVALID_COMPRESSION,				"Invalid compression",
IGE_INSTANCE_FAILURE,					"Instance failure",
IGE_CANT_READ_FILE,						"Can't read file",
IGE_INVALID_IMAGE_FORMAT,				"Invalid image format",
IGE_FORMAT_NOT_DETECTABLE,				"Save Format can not be detected from File Extension used",
IGE_FILE_FORMAT_IS_READONLY,			"File is read only",
IGE_INVALID_BITCOUNT_FOR_FORMAT,		"Invalid bitcount (depth) for this format",
IGE_INTERRUPTED_BY_USER,				"Interrupted by user",
IGE_NO_BITMAP_REGION,					"No bitmap region",
IGE_BAD_FILE_FORMAT,						"Bad file format",
IGE_EPS_NO_PREVIEW,						"EPS file has no screen preview to read",
IGE_CANT_WRITE_FILE,						"Can't write file",
IGE_NO_BITMAP_FOUND,						"No raster image found in file to load",
IGE_PALETTE_FILE_TYPE_INVALID,		"Palette file type is invalid",
IGE_PALETTE_FILE_WRITE_ERROR,			"Palette file write error",
IGE_PALETTE_FILE_READ_ERROR,			"Palette file read error",
IGE_PALETTE_FILE_NOT_DETECTED,		"Palette file not detected",
IGE_PALETTE_FILE_INVALID_HALO_PAL,	"Invalid Halo palette file",
IGE_G4_PREMATURE_EOF_AT_SCAN_LINE,	"Group 4 premature EOF",
IGE_G4_PREMATURE_EOL_AT_SCAN_LINE,	"Group 4 premature EOL",
IGE_G4_BAD_2D_CODE_AT_SCAN_LINE,		"Group 4 invalid 2D code",
IGE_G4_BAD_DECODING_STATE_AT_SCAN_LINE, "Group 4 bad decoding state",
IGE_G3_PREMATURE_EOF_AT_SCAN_LINE,	"Group 3 premature EOF",
IGE_G3_BAD_1D_CODE_AT_SCAN_LINE,		"Group 3 bad 1D code",
IGE_G3_PREMATURE_EOL_AT_SCAN_LINE,	"Group 3 premature EOL",
IGE_INVALID_TAG,							"Invalid TIFF tag",
IGE_INVALID_IFD,							"Invalid TIFF IFD",
IGE_IFD_PROC_FAILURE,					"TIFF IFD proc failed",
IGE_SEEK_FAILURE,							"TIFF seek failure",
IGE_INVALID_BYTE_ORDER,					"TIFF invalid byte order",
IGE_CANT_READ_TAG_DATA,					"TIFF can't read tag data",
IGE_INVALID_BITS_PER_SAMPLE,			"TIFF invalid bits per sample",
IGE_INVALID_COLOR_MAP,					"TIFF invalid color map",
IGE_INVALID_PHOTOMETRIC,				"TIFF invalid photometric interpretation value",
IGE_INVALID_REQ_INFO,					"TIFF required information missing",
IGE_COMP_NOT_SUPPORTED,					"TIFF compression is not supported",	/* only used during development */
IGE_RASTER_FEED_ERROR,					"TIFF raster feed error",
IGE_IMAGE_DATA_READ_ERROR,				"TIFF image data read error",
IGE_HEADER_WRITE_FAILED,				"TIFF header write failure",
IGE_DIB_GET_FAILURE,						"TIFF DIB get failure",
IGE_CANT_REALLOC_MEM,					"TIFF can't realloc memory error",
IGE_IFD_WRITE_ERROR,						"TIFF IFD write error",
IGE_TAG_WRITE_ERROR,						"TIFF tag write error",
IGE_IMAGE_DATA_WRITE_ERROR,         "TIFF image data write error",
IGE_PLANAR_CONFIG_ERROR,            "TIFF planar config error",
IGE_RASTER_TO_LONG,						"TIFF raster too long",
IGE_LZW_ERROR,								"TIFF LZW error",
IGE_INVALID_IMG_DEM,						"TIFF invalid image dimension",
IGE_BAD_DATA_TYPE,						"TIFF bad data type",
IGE_PAGE_COUNT_FAILURE,					"TIFF count not count the number of pages in the file",
IGE_CORRUPTED_FILE,						"TIFF data in file was not what was expected and could not be interp",
IGE_INVALID_STRIP_BYTE_CNT,			"TIFF strip byte count was zero and could not be estimated",
IGE_INVALID_COMP_BIT_DEPTH,			"TIFF bit depth is invalid for this compression scheme",
IGE_REPAGE_FAILED,						"TIFF unable to write new page numbers while repaging file",
IGE_PRIV_TAG_TYPE_INVALID,				"TIFF private user tag had an invalid type",
IGE_CLP_INVALID_FORMAT_ID,				"CLP invalid format ID",
IGE_WRONG_DIB_BIT_COUNT,				"Invalid bit count for this function",
IGE_LOCK_FAILED,							"Memory lock failed",
IGE_ALLOC_FAILED,							"Memory alloc failed",
IGE_FREE_FAILED,                    "Memory free failed",
IGE_BAD_KERN_TYPE,						"Bad kernel type",
IGE_AI_HANDLES_USED_UP,					"Maximum number of handles have been used",
IGE_AI_HANDLE_INVALID,					"Invalid handle",
IGE_DIBS_ARE_INCOMPATIBLE,				"Incompatible DIBs",
IGE_DIB_DIMENSIONS_NOT_EQUAL,			"DIB dimensions not equal",
IGE_DIB_BIT_COUNTS_NOT_EQUAL,			"DIB bit counts not equal",
IGE_DIB_HAS_NO_PALETTE,					"DIB palette missing",
IGE_ROI_WRONG_TYPE,						"Region of interest is wrong type",
IGE_REQUIRES_CONVEX_ROI,				"Function requires convex ROI",
IGE_INVALID_RAMP_DIRECTION,			"Invalid ramp direction",
IGE_INVALID_LUT_ARITH_FUNC,			"Invalid LUT arithmetic function",
IGE_INVALID_KERN_MOTION_EXTENT,		"Invalid kernel motion extent",
IGE_INVALID_NOISE_TYPE,					"Invalid noise type",
IGE_INVALID_KERN_NORMALIZER,			"Invalid kernel normalizer",
IGE_INVALID_SIGMA,						"Invalid sigma",
IGE_INVALID_SKEW_POINTS,				"Invalid skew points",
IGE_TILE_IS_LARGER_THAN_IMAGE,		"Tile is larger than image",
IGE_COLOR_SPACE_INVALID,				"Invalid color space",
IGE_DIB_POINTER_IS_NULL,				"DIB pointer is NULL",
IGE_PROC_INVAL_FOR_BIT_COUNT,			"Bit count not supported by this function",
IGE_PROC_INVAL_FOR_PALETTE_IMG,		"Function does not support 8 bit images",
IGE_PARAMETER_OUT_OF_LIMITS,			"Parameters are out of limits",
IGE_INVALID_POINTER,						"Invalid pointer",
IGE_INVALID_ENCRYPT_MODE,				"Invalid encryption mode",
IGE_PASSWORD_LENGTH_INVALID,			"Invalid password length",
IGE_PROC_REQUIRE_8BIT_GRAYSCALE,		"This functionn can be used on 8-bit grayscale images only",
IGE_INVALID_RESOLUTION_UNIT,			"The units of the image resolution are not supported",
IGE_TW_SM_SUCCESS,						"Twain function successful",
IGE_TW_SM_BUMMER,							"General TWAIN error",
IGE_TW_SM_LOWMEMORY,						"TWAIN low memory",
IGE_TW_SM_NODS,							"TWAIN no source",
IGE_TW_SM_MAXCONNECTIONS,				"TWAIN maximum connections",
IGE_TW_SM_OPERATIONERROR,				"TWAIN source or source manager reported error",
IGE_TW_SM_BADCAP,							"TWAIN capability incompatible",
IGE_TW_SM_BADPROTOCOL,					"TWAIN bad protocol",
IGE_TW_SM_BADVALUE,						"TWAIN bad value",
IGE_TW_SM_SEQERROR,						"TWAIN operation sequence error",
IGE_TW_SM_BADDEST,						"TWAIN unknown destination",
IGE_TW_CANT_OPENDSM,						"TWAIN cannot load source manager",
IGE_TW_CANT_OPENDS,						"TWAIN cannot load data source",
IGE_TW_CANT_ENABLEDS,					"TWAIN cannot enable data source",
IGE_TW_CANT_FINDDSM,						"TWAIN cannot find source manager",
IGE_TW_CANT_LOADDSM,						"TWAIN cannot load source manager",
IGE_TW_CANT_SCAN_PAGES,					"TWAIN cannot scan pages",
IGE_TW_CANT_TRANSFERIMAGE,				"TWAIN cannot transfer image to application",
IGE_TW_CANT_GETDSMADDR,					"TWAIN cannot get address of source manager",
IGE_TW_CANT_PROCESSMSG,					"TWAIN cannot procees message",
IGE_TW_INVALID_DIBHANDLE,           "TWAIN invalid DIB handle",
IGE_TW_CANT_SET_ICAP_PIX_FLAVOR,		"TWAIN cannot set Pixel Flavor Caps",	

IGE_FILE_CANT_OPEN,						"Open file failure",
IGE_FILE_CANT_SAVE,						"Save file failure",
IGE_FILE_CANT_DELETE,					"Delete file failure",
IGE_FILE_INVALID_FILENAME,				"Invalid file name",
IGE_REGISTER_CLASS_FAILED,				"RegisterClass failed",
IGE_CREATE_WINDOW_FAILED,				"CreateWindow failed",
IGE_WINDOW_NOT_ASSOCATED,				"Window not associated",
IGE_INVALID_WINDOW,						"Invalid window handle",
IGE_VBX_INVALID_FUNCTION_NUM,			"Invalid VBX function number",

/* Keep this one last - it is used to mark the end of the list	*/
IGE_LAST_ERROR_NUMBER,					""
};



/*#ifndef __GEARESTR_H__*/
#endif
