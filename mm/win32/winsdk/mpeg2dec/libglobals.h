
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#ifndef INC_LIBGLOBALS
#define INC_LIBGLOBALS

extern "C" {

#include "mpglib/global.h"

void clear_options();
void initialize_decoder();
void finalize_decoder();

void Error(char *text);

void Update_Picture_Buffers();
void picture_data(int framenum);

int win_file_read(int handle, void *buffer, unsigned int count);


} // extern "C"

#endif
