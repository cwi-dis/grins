
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <windows.h>

#ifndef _WIN32_WCE
#include <io.h>
#include <fcntl.h>
#endif

#define GLOBAL
#include "libglobals.h"


/////////////////////////////////////////////////
extern "C" {

static unsigned char *Clip_MB;
	
void Error(char *text)
	{
	fprintf(stderr,text);
	exit(1);
	}

void clear_options()
	{
	Verbose_Flag = 0;
	Output_Type = -1;
	Output_Picture_Filename = " ";
	hiQdither  = 0;
	Output_Type = 0;
	Frame_Store_Flag = 0;
	Spatial_Flag = 0;
	Lower_Layer_Picture_Filename = " ";
	Reference_IDCT_Flag = 0;
	Trace_Flag = 0;
	Quiet_Flag = 0;
	Ersatz_Flag = 0;
	Substitute_Picture_Filename  = " ";
	Two_Streams = 0;
	Enhancement_Layer_Bitstream_Filename = " ";
	Big_Picture_Flag = 0;
	Main_Bitstream_Flag = 0;
	Main_Bitstream_Filename = " ";
	Verify_Flag = 0;
	Stats_Flag  = 0;
	User_Data_Flag = 0; 
	}

void initialize_decoder()
	{
	// Clip table 
	Clip_MB = Clip = (unsigned char *)malloc(1024);
	Clip += 384;

	for (int i=-384; i<640; i++)
		Clip[i] = (i<0) ? 0 : ((i>255) ? 255 : i);

	// IDCT */
	if (Reference_IDCT_Flag)
		Initialize_Reference_IDCT();
	else
		Initialize_Fast_IDCT();
	}

// undo initialize_decoder
void finalize_decoder()
	{
	free(Clip_MB);
	}

/////////////////////////////////////////////////
} // extern "C"

