/***************************************************************************/
/*                                                                         */
/* MODULE:    ERRS.H -  Master AccuSoft Error Code File                    */
/*                                                                         */
/*                                                                         */
/* Date created:        01/19/1996 DF (modified from IPL project)          */
/*                                                                         */
/*    $Date$                                             */
/*    $Revision$                                                   */
/*                                                                         */
/*       Copyright 1996, AccuSoft Corporation.										*/
/*                                                                         */
/***************************************************************************/


#ifndef __GEARERRS_H__
#define __GEARERRS_H__


/***************************************************************************/
/* For now add error codes here and give them any value you want           */
/* Also, please add an English descriptive sentence as a comment           */
/* following the error code - these will be placed in an RC file           */
/***************************************************************************/


/***************************************************************************/
/* Misc. error codes                                                       */
/***************************************************************************/

#define  IGE_SUCCESS                            0     /* No errors -- Success          */
#define  IGE_FAILURE                            -1    /* General error - Failure       */

#define  IGE_NOT_DONE_YET                       -100  /* For internal reference of areas to return to                                                       */
#define  IGE_NOT_IMPLEMENTED                    -200  /* For internal reference of areas to return to                                                       */
#define	IGE_PRO_GOLD_FEATURE							-300	/* An attempt was made to use a Pro Gold feature in the standard product. */
#define  IGE_ERROR_COMPRESSION                  -400
#define	IGE_EXTENSION_NOT_LOADED					-500	/* the ImageGear extension was not present or couldn't be loaded			  */
#define	IGE_INVALID_CONTROL_OPTION					-600	/* invalid image control option ID													  */
#define	IGE_INVALID_EXTENSION_MODULE				-700	/* the specified ImageGear extension file was not a valid extension file  */
#define	IGE_EXTENSION_INITIALIZATION_FAILED		-800	/* the specified ImageGear extension was unable to initialize.				  */


/***************************************************************************/
/* Lowlevel & Support code errors                                          */
/***************************************************************************/

#define  IGE_OUT_OF_MEMORY                      -1000 /* No more global memory is available for allocation, reduced used resources                          */
#define  IGE_EVAL_DLL_TIMEOUT_HAS_EXPIRED       -1003 /* The DLL is an Evaluation copy and as timed out - contact ACCUSOFT to purchase a release copy       */
#define  IGE_INVALID_STANDARD_KERNEL            -1004 /* The kernel expected should be one of the predefined ones, your could not be found                  */
#define  IGE_INTERNAL_ERROR                     -1005 /* An internal error has occured, contact ACCUSOFT techical support                                   */
#define  IGE_INVALID_RECTANGLE                  -1007 /* Occurs when a rectangle's left >= right or top >= bottom                                           */
#define	IGE_NO_CLIPBOARD_IMAGE_AVAILABLE			-1008 /* No image is available for a clipboard paste																			*/
#define	IGE_CLIPBOARD_OPEN_FAILED					-1009 /* Could not open the clipboard																								*/
#define  IGE_SETCLIPBOARDDATA_FAILED				-1010 /* Could not put data into the clipboard																					*/
#define  IGE_COULD_NOT_GET_DDB_DIMENSIONS			-1011 /* GetObject() failed.  Couldn't get the DDB's dimensions															*/
#define	IGE_COULD_NOT_GET_DDB_BITS					-1012 /* GetDIBits() failed.  Couldn't get the DDB's image data															*/
#define	IGE_CREATE_BITMAP_FAILED					-1013 /* CreateBitmap() failed.  Couldn't create a DDB.																		*/
#define	IGE_COULD_DISPLAY_DDB						-1014 /* BitBlt()	failed.  Couldn't display the DDB																			*/
#define	IGE_INVALID_PATTERN_BITMAP					-1015 /* The DDB was > 1 bit per pixel or the width was > 8 or the height was > 8									*/
#define	IGE_PASSWORD_INVALID							-1016 /* The Password is not recognized																							*/	

/***************************************************************************/
/* Filter Error codes                                                      */
/***************************************************************************/

#define  IGE_THUMBNAIL_NOT_PRESENT              -2000 /* Thumnails are supported but non can be found in this image file                                    */
#define  IGE_THUMBNAIL_READ_ERROR               -2001 /* A read error occured while reading a thumbnail                                                     */
#define  IGE_THUMBNAIL_NOT_SUPPORTED            -2002 /* Thumbnails are not supported by this format                                                        */

#define  IGE_PAGE_NOT_PRESENT                   -2005 /* The requested image page does not exit in the file                                                 */
#define  IGE_PAGE_INVALID                       -2006 /* The page number provided is outside of the range of valid pages for this file                      */
#define  IGE_PAGE_COULD_NOT_BE_READ             -2007 /* The page number could not be determined                                                            */

#define  IGE_CANT_DETECT_FORMAT                 -2010 /* The format of the file can not be determined                                                       */

#define  IGE_FILE_CANT_BE_OPENED                -2030 /* An attempt to open a file failed, it may not exist in the provided path                            */
#define  IGE_FILE_CANT_BE_CREATED					-2031 /* An attempt to create a file failed, it may already exist in the provided path                      */
#define  IGE_FILE_CANT_BE_CLOSED						-2032 /* An attempt to close a file failed	                      														*/
#define  IGE_FILE_TO_SMALL_TO_BE_BMFH           -2033 /* The file is too small to be a valid BMFH                                                           */
#define  IGE_FILE_IS_NOT_BMP                    -2034 /* The BMFH Magic number is invalid                                                                   */
#define  IGE_FILE_TO_SMALL_TO_BE_BMIH           -2035 /* The file is too small to be a valid BMIH                                                           */
#define  IGE_BMP_IS_COMPRESSED                  -2040 /* The BMP file is in compressed (RLE) format                                                         */
#define  IGE_FILE_SIZE_WRITE_ERROR					-2041	/* Could not write file size field to BMP																					*/
#define  IGE_CANT_READ_PALETTE                  -2050
#define  IGE_CANT_READ_PIXELS                   -2051
#define  IGE_CANT_READ_HEADER                   -2052
#define  IGE_INVALID_FILE_TYPE                  -2060
#define  IGE_INVALID_HEADER                     -2061
#define  IGE_CANT_WRITE_PALETTE                 -2070
#define  IGE_CANT_WRITE_PIXELS                  -2071
#define  IGE_CANT_WRITE_HEADER                  -2072
#define  IGE_FORMAT_NOT_DETECTABLE					-2073
#define  IGE_INVALID_COMPRESSION                -2080
#define  IGE_INSTANCE_FAILURE                   -2090
#define  IGE_CANT_READ_FILE                     -2100
#define  IGE_INVALID_IMAGE_FORMAT               -2110 /* The image file is invalid as the expected format      															*/
#define  IGE_FILE_FORMAT_IS_READONLY            -2111 /* The image file is read only and can not be written to 															*/
#define  IGE_INVALID_BITCOUNT_FOR_FORMAT        -2112 /* The bitcount found is not supported by this format    															*/
#define  IGE_INTERRUPTED_BY_USER						-2113 /* Status bar callback returned FALSE																						*/
#define	IGE_NO_BITMAP_REGION                   -2390
#define  IGE_BAD_FILE_FORMAT                    -2391 /* Format is not correct.  																									*/
#define	IGE_EPS_NO_PREVIEW							-2392 /* EPS file has no screen preview image to load 																		*/
#define	IGE_CANT_WRITE_FILE							-2393
#define	IGE_NO_BITMAP_FOUND							-2394	/* WPG, WMF etc.  No raster image exists in file																		*/
#define	IGE_PALETTE_FILE_TYPE_INVALID				-2395	/* IG_PALETTE_ value is not known																							*/
#define	IGE_PALETTE_FILE_WRITE_ERROR				-2396	/* Error writing to a palette file																							*/
#define	IGE_PALETTE_FILE_READ_ERROR				-2397	/* Error reading from a palette file																						*/
#define	IGE_PALETTE_FILE_NOT_DETECTED				-2398	/* The file is not a valid palette file																					*/
#define	IGE_PALETTE_FILE_INVALID_HALO_PAL		-2399	/* Detected Dr. Halo Palette file is invalid																				*/
#define	IGE_G4_PREMATURE_EOF_AT_SCAN_LINE      -2400
#define	IGE_G4_PREMATURE_EOL_AT_SCAN_LINE      -2401
#define	IGE_G4_BAD_2D_CODE_AT_SCAN_LINE        -2402
#define	IGE_G4_BAD_DECODING_STATE_AT_SCAN_LINE	-2403
#define	IGE_G3_PREMATURE_EOF_AT_SCAN_LINE		-2410
#define	IGE_G3_BAD_1D_CODE_AT_SCAN_LINE			-2411						                      
#define	IGE_G3_PREMATURE_EOL_AT_SCAN_LINE		-2412
#define	IGE_OPERATION_IS_NOT_ALLOWED				-2432

/*TIFF ERRORS*/
#define 	IGE_INVALID_TAG								-2450		/*Tag Read did not contain correct num of bytes	*/
#define 	IGE_INVALID_IFD								-2451 	/*IFD Read did not contain correct num of bytes	*/
#define 	IGE_IFD_PROC_FAILURE							-2452 	/*Invalid IFD information was detected				*/
#define 	IGE_SEEK_FAILURE								-2453		/*IOS position seek failed								*/
#define 	IGE_INVALID_BYTE_ORDER 						-2454    /*Byte order flag was not Intel or Motarola		*/
#define 	IGE_CANT_READ_TAG_DATA						-2455		/*Was unable to read all TAG information			*/
#define	IGE_INVALID_BITS_PER_SAMPLE  				-2456    /*Bits per sample tag was invalid					*/
#define	IGE_INVALID_COLOR_MAP						-2457		/*Color Map was found to be invalid					*/
#define	IGE_INVALID_PHOTOMETRIC						-2458    /*Photometric tag value was found to be invalid */
#define	IGE_INVALID_REQ_INFO							-2459    /*Required information was not supplied			*/
#define	IGE_COMP_NOT_SUPPORTED						-2460    /*Compression is not supported at this time		*/
#define	IGE_RASTER_FEED_ERROR    					-2461		/*Error feeding raster data to the DIB				*/
#define	IGE_IMAGE_DATA_READ_ERROR    				-2462		/*Was unable to read all image data requested	*/
#define	IGE_HEADER_WRITE_FAILED						-2463		/*Header write failed									*/
#define	IGE_DIB_GET_FAILURE							-2464		/*Was unable to retreive the DIB information		*/
#define	IGE_CANT_REALLOC_MEM							-2465		/*Was not able to reallocate memory					*/
#define	IGE_IFD_WRITE_ERROR							-2466		/*Was not able to write IFD info to the IOS		*/
#define	IGE_TAG_WRITE_ERROR							-2467		/*Was not able to write TAG info to the IOS		*/
#define	IGE_IMAGE_DATA_WRITE_ERROR					-2468		/*Was not able to write IMAGE data to the IOS	*/
#define	IGE_PLANAR_CONFIG_ERROR						-2469		/*Planar Config detected is unsupported			*/
#define	IGE_RASTER_TO_LONG							-2470		/*One raster lines exceeds the max num of bytes */
#define	IGE_LZW_ERROR									-2471		/*Error occured in LZW decode							*/
#define	IGE_INVALID_IMG_DEM							-2472		/*Image Dimension was invalid							*/
#define	IGE_BAD_DATA_TYPE								-2473		/*Data type detected is not valid					*/
#define	IGE_PAGE_COUNT_FAILURE						-2474		/*count not count the number of pages in the file*/
#define	IGE_CORRUPTED_FILE							-2475		/*data in file was not what was expected and could not be interp*/
#define	IGE_INVALID_STRIP_BYTE_CNT					-2476		/*strip byte count was zero and could not be estimated*/
#define	IGE_INVALID_COMP_BIT_DEPTH					-2477		/*bit depth is invalid for this compression scheme*/
#define  IGE_REPAGE_FAILED								-2478		/*unable to write new page numbers while repaging file */
#define  IGE_PRIV_TAG_TYPE_INVALID					-2479		/*private user tag had an invalid type				*/

#define	IGE_CLP_INVALID_FORMAT_ID					-2500	/* Windows clipboard file contains an unsupport Format ID at this page											*/



/***************************************************************************/
/* Image Processing Error codes                                            */
/***************************************************************************/

#define  IGE_WRONG_DIB_BIT_COUNT                -3000 /* The DIB has bit with the wrong bit count for this routine                                          */
#define  IGE_LOCK_FAILED                        -3010 /* Memory required for this routine could not be locked, most likly running out of memory resources   */
#define  IGE_ALLOC_FAILED                       -3020 /* Memory required for this routine could not be allocated, free up some resources and try again      */
#define  IGE_FREE_FAILED                        -3030 /* An internal memory free has failed, ussally a bad handle, or corrupted system                      */
#define  IGE_BAD_KERN_TYPE                      -3040 /**/
#define  IGE_AI_HANDLES_USED_UP                 -3050 /* The maximum number od AccuSoft handles has been used - no more left.  Free up some and try again   */
#define  IGE_AI_HANDLE_INVALID                  -3060 /* This routine requires an AccuSoft handle.  The handle passed in was not allocated by AccuSoft      */
#define  IGE_DIBS_ARE_INCOMPATIBLE              -3070 /* The images are not compatible for this function, either dimension, bit count, or both              */
#define  IGE_DIB_DIMENSIONS_NOT_EQUAL           -3090 /* The images must be the same dimensions                                                             */
#define  IGE_DIB_BIT_COUNTS_NOT_EQUAL           -3100 /* The images must have the same bit count                                                            */
#define  IGE_DIB_HAS_NO_PALETTE                 -3101 /* The image passed in does not have a palette and this routine requires one                          */
#define  IGE_ROI_WRONG_TYPE                     -3110 /**/
#define  IGE_REQUIRES_CONVEX_ROI                -3120 /* This function requires a convex ROI. The one passed in must be convex                              */
#define  IGE_INVALID_RAMP_DIRECTION             -3130 /* The contrast ramps direction is not supported                                                      */
#define  IGE_INVALID_LUT_ARITH_FUNC             -3140 /* The LUT_ARITH_FUNC is not a valid function number, check the constant                              */
#define  IGE_INVALID_KERN_MOTION_EXTENT         -3150 /**/
#define  IGE_INVALID_NOISE_TYPE                 -3160 /**/
#define  IGE_INVALID_KERN_NORMALIZER            -3170 /**/
#define  IGE_INVALID_SIGMA                      -3180 /**/
#define  IGE_INVALID_SKEW_POINTS                -3190 /* A valid line could not be drawn through the two point provided.  Y1==Y2                            */
#define  IGE_TILE_IS_LARGER_THAN_IMAGE          -3200 /* The tile image must be the same size or smaller in both dimensions than the original source        */
#define  IGE_COLOR_SPACE_INVALID                -3210 /* Invalid type of color space MODE                                                                   */
#define  IGE_DIB_POINTER_IS_NULL                -3220 /* The DIB pointer about to be used is NULL (invalid)                                                 */
#define  IGE_PROC_INVAL_FOR_BIT_COUNT           -3300 /* This function can not be used on images with this one's bit count                                  */
#define  IGE_PROC_INVAL_FOR_PALETTE_IMG         -3310 /* This function can not be used on 8-bit color images - try to promote to 24-bit                     */
#define  IGE_PARAMETER_OUT_OF_LIMITS            -3320 /* A parameter is out of its legal range                                                              */
#define  IGE_INVALID_POINTER                    -3330 /* A pointer was detected to be NULL                                                                  */
#define  IGE_INVALID_ENCRYPT_MODE					-3340	/* The selected Encryption Method is invalid																				*/
#define  IGE_PASSWORD_LENGTH_INVALID				-3350	/* Password must be at least 1-byte long (should be at least 5 bytes)											*/
#define  IGE_PROC_REQUIRE_8BIT_GRAYSCALE			-3360	/* This functionn can be used on 8-bit grayscale images only														*/
#define	IGE_INVALID_RESOLUTION_UNIT				-3370 /* The units of the image resolution are not supported																*/


/***************************************************************************/
/* TWAIN Scanning Function Error codes                                     */
/***************************************************************************/

#define	IGE_TW_SM_SUCCESS                      -3400	/* Operation worked                                                            */
#define	IGE_TW_SM_BUMMER                       -3401	/* General failure due to unknown causes                                       */
#define	IGE_TW_SM_LOWMEMORY                    -3402	/* Not enough memory to complete operation                                     */
#define	IGE_TW_SM_NODS                         -3403	/* Source Manager unable to find the specified Source                          */
#define	IGE_TW_SM_MAXCONNECTIONS               -3404	/* Source is connected to maximum number of applications                       */
#define	IGE_TW_SM_OPERATIONERROR               -3400	/* Source or Source Manager reported an error to the user                      */
#define	IGE_TW_SM_BADCAP                       -3405	/* Capability not supported by Source or operation not supported by capability */	
#define	IGE_TW_SM_BADPROTOCOL                  -3406	/* Unrecognized operation triplet                                              */
#define	IGE_TW_SM_BADVALUE                     -3407	/* Data parameter out of supported range                                       */
#define	IGE_TW_SM_SEQERROR                     -3408	/* Illegal operation for current Source Manager or Source state                */
#define	IGE_TW_SM_BADDEST                      -3409	/* Unknown destination in DSM_ENTRY                                            */
#define	IGE_TW_CANT_OPENDSM                    -3420	/* Cannot load Source Manager                                                  */
#define  IGE_TW_CANT_OPENDS                     -3421 /* Cannot load data Source                                                     */
#define	IGE_TW_CANT_ENABLEDS                   -3422	/* Cannot enable data Source                                                   */
#define	IGE_TW_CANT_FINDDSM                    -3423	/* Cannot find Source Manager                                                  */
#define	IGE_TW_CANT_LOADDSM                    -3424	/* Cannot load Source Manager to memory                                        */
#define	IGE_TW_CANT_SCAN_PAGES                 -3425	/* Cannot scan pages                                                           */
#define	IGE_TW_CANT_TRANSFERIMAGE              -3426	/* Cannot transfer image to application                                        */
#define	IGE_TW_CANT_GETDSMADDR                 -3427	/* Cannot get address of the Source Manager                                    */
#define	IGE_TW_CANT_PROCESSMSG                 -3428	/* Cannot process TWAIN message                                                */
#define	IGE_TW_INVALID_DIBHANDLE               -3429	/* Invalid DIB handle                                                          */
#define	IGE_TW_CANT_SET_ICAP_PIX_FLAVOR			-3430	/* Cannot set Pixel Flavor																		 */

/***************************************************************************/
/* Disk File Access Error codes                                            */
/***************************************************************************/

#define	IGE_FILE_CANT_OPEN                     -3440	/* Cannot open file   */
#define	IGE_FILE_CANT_SAVE                     -3441	/* Cannot save file   */
#define	IGE_FILE_CANT_DELETE                   -3442	/* Cannot delete file */
#define	IGE_FILE_INVALID_FILENAME              -3443	/* Invalid file name  */
                                                              

/***************************************************************************/
/* GUI Function Error codes                                                */
/***************************************************************************/

#define  IGE_REGISTER_CLASS_FAILED              -6000 /* Microsoft Windows function:  RegisterClass() failed. */
#define  IGE_CREATE_WINDOW_FAILED               -6010 /* Microsoft Windows function:  CreateWindow() failed.  */
#define  IGE_WINDOW_NOT_ASSOCATED               -6020 /* An attempt was made to disassociate a window that was never assocated.  */
#define	IGE_INVALID_WINDOW							-6030	/* An invalid window handle was passed as one of the parameters to the function. */


/***************************************************************************/
/* VBX/OCX level error codes                                               */
/***************************************************************************/

#define  IGE_VBX_INVALID_FUNCTION_NUM           -7000 /* Invalid VBX function number                                                                     */


/***************************************************************************/
/* Application error codes must be less that the following last number used*/
/***************************************************************************/

#define  IGE_LAST_ERROR_NUMBER                  -9999 


/*#ifndef __GEARERRS_H__*/
#endif
