/****************************************************************************
;
;       HEADER:   AccuIMG.h -   AccuSoft public data types and macros header.
;	          These data types are used by all AccuSoft
;				       products.
;
;       Date created:	   01/19/1996 DF
;
;       $Date$
;       $Revision$
;
;	       Copyright 1996, AccuSoft Corporation.
;
;****************************************************************************/


#ifndef __ACCUIMG_H__
#define __ACCUIMG_H__

/***************************************/
/* High level imaging type definitions */
/***************************************/

typedef struct  tagAT_RUNS
	{
	AT_PIXPOS		x;
	AT_DIMENSION	x_length;
	AT_DIMENSION	num_of_runs;
	LPAT_PIXPOS		lpLengthsArray;
	}
	AT_RUNS;
typedef AT_RUNS FAR		*LPAT_RUNS;

typedef LONG			RUN;
typedef RUN FAR		*LPRUN;


typedef AT_PIXEL		AT_LUT;
typedef LPAT_PIXEL	LPAT_LUT;


typedef struct  tagAT_VECTOR
	{
	AT_POINT		base;
	AT_POINT		tail;
	} 
	AT_VECTOR;
typedef AT_VECTOR FAR	*LPAT_VECTOR;


typedef struct  tagAT_DPOINT
	{
	double		x;
	double		y;
	} 
	AT_DPOINT;
typedef AT_DPOINT FAR	*LPAT_DPOINT;


typedef struct  tagAT_DRECT
	{
	double 	 left;
	double 	 top;
	double 	 right;
	double 	 bottom;
	} 
	AT_DRECT;
typedef AT_DRECT FAR	*LPAT_DRECT;


typedef struct  tagAT_LINE
	{
	AT_POINT	p1;
	AT_POINT	p2;
	} 
	AT_LINE;
typedef AT_LINE FAR	*LPAT_LINE;


typedef struct  tagAT_AOI
	{
	AT_POINT		p1;             /*      Well formed     AOI has P1 at top-left corner   */
	AT_POINT		p2;             /*      and has P2 at bottom-right      corner           */
	} 
	AT_AOI;
typedef AT_AOI FAR	*LPAT_AOI;


typedef struct  tagAT_SQUARE
	{
	AT_POINT			p;
	AT_DIMENSION	length;
	} 
	AT_SQUARE;
typedef AT_SQUARE FAR	*LPAT_SQUARE;


typedef struct  tagAT_CIRCLE
	{
	AT_POINT	center;
	UINT		radius;
	} 
	AT_CIRCLE;
typedef AT_CIRCLE FAR	*LPAT_CIRCLE;


typedef struct  tagAT_POLYGON
	{
	UINT		num_of_nodes;
	UINT		max_num_of_nodes;
	AT_POINT	node[1];
	} 
	AT_POLYGON;
typedef AT_POLYGON FAR	*LPAT_POLYGON;


typedef struct  tagAT_SEGMENT
	{
	AT_PIXPOS		y;      /*      raster line     number of segment 		        */
	AT_PIXPOS		x;      /*      first   x on raster 				      */
	AT_DIMENSION	length; /*      # of pixels     on      this segment 		     */
	}              
	AT_SEGMENT;
typedef AT_SEGMENT FAR	*LPAT_SEGMENT;
		

typedef struct  tagAT_SEG_LIST
	{
	DWORD				num_of_segments;
	DWORD				max_num_of_segments;
	LPAT_SEGMENT	segment;
	} 
	AT_SEG_LIST;
typedef AT_SEG_LIST FAR	*LPAT_SEG_LIST;


typedef struct tagAT_ROI_STATS
	{
	DWORD		area;
	DWORD		perimeter;
	AT_POINT	centroid;
	}              
	AT_ROI_STATS;
typedef AT_ROI_STATS FAR	*LPAT_ROI_STATS;


typedef struct  tagAT_HISTO_STATS
	{
	UINT		start;		  /*      first_pix_value_considered;       */
	UINT		end;		            /*      last_pix_value_considered 	*/
	UINT		min_pix_value;
	UINT		max_pix_value;
	UINT		most_common_pix_value;
	UINT		least_common_pix_value;
	DWORD		count_of_most_common_pix_value;
	DWORD		count_of_least_common_pix_value;
	DWORD		sum;
	DWORD		sum_below_start;
	DWORD		sum_above_end;
	double	ave;
	double	var;
	double	sd;
	AT_RECT	AOI;
	UINT	segment_incr;
	}
	AT_HISTO_STATS;
typedef AT_HISTO_STATS FAR		*LPAT_HISTO_STATS;


typedef struct  tagAT_HISTOGRAM
	{
	UINT				number_of_bins;
	DWORD				bin[256];
	AT_RECT			AOI;
	UINT				segment_incr;
	AT_HISTO_STATS	seg_stats;
	AT_HISTO_STATS	total_stats;
	} 
	AT_HISTOGRAM;
typedef AT_HISTOGRAM FAR	*LPAT_HISTOGRAM;


typedef DWORD			AT_HISTO_BIN;
typedef DWORD FAR		*LPAT_HISTO_BINS;


/* #ifndef __ACCUIMG_H__ */
#endif
