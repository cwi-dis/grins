
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef _WIN32_WCE
#include <io.h>
#include <fcntl.h>
#endif

#include "mpegdecoder.h"

#include "libglobals.h"

#include "mpegdisplay.h"

#include "../common/platform.h"

MpegDecoder::MpegDecoder()
:	m_base_layer(&base),
	m_enhan_layer(&enhan),
	m_display(NULL)
	{
	memset(&base, 0, sizeof(base));
	memset(&enhan, 0, sizeof(enhan));
	base.Infile = -1;
	}

MpegDecoder::~MpegDecoder()
	{
	if(base.Infile != -1 && base.Infile != 0)
		platform::close(base.Infile);
	}

bool MpegDecoder::check(int handle)
	{
	if(handle == -1 || handle == 0)
		return false;
	base.Infile = handle;
	base.infile_read_fn = platform::read;
	ld = m_base_layer;
	return check_mpeg();
	}

int MpegDecoder::detach_file_handle()
	{
	int handle = base.Infile;
	base.Infile = -1;
	return handle;
	}

bool MpegDecoder::check_mpeg()
	{
    platform::seek(base.Infile, 0, platform::f_begin);
    Initialize_Buffer(); 
    if(Show_Bits(8)==0x47)
		{
		sprintf(Error_Text,"Decoder currently does not parse transport streams\n");
		return false;
		}
	next_start_code();
	int code = Show_Bits(32);
    switch(code)
		{
		case SEQUENCE_HEADER_CODE:
			break;
		case PACK_START_CODE:
			System_Stream_Flag = 1;
		case VIDEO_ELEMENTARY_STREAM:
			System_Stream_Flag = 1;
			break;
		default:
			sprintf(Error_Text,"Unable to recognize stream type\n");
			return false;
		}
    platform::seek(base.Infile, 0, platform::f_begin);
    Initialize_Buffer();
	return true;
	}

bool MpegDecoder::parse_picture_header()
	{
	ld = m_base_layer;

	Output_Type = -1;
	// return when end of sequence (0) or picture
	//   header has been parsed (1) 
	int ret = Get_Hdr();
	if (Two_Streams)
		{
		ld = m_enhan_layer;
		if (Get_Hdr()!=ret && !Quiet_Flag)
			fprintf(stderr,"streams out of sync\n");
		ld = m_base_layer;
		}
	return ret == 1;
	}

void MpegDecoder::reset_framenum()
	{
	m_bitstream_framenum = 0;
	m_sequence_framenum = 0;
	}

void MpegDecoder::update_framenum()
	{
	if (!Second_Field)
		{
		m_bitstream_framenum++;
		m_sequence_framenum++;
		}
	}

void MpegDecoder::write_last_sequence_frame()
	{
	// put last frame
	if (m_sequence_framenum!=0)
		{
		//Output_Last_Frame_of_Sequence(m_bitstream_framenum);
		if (Second_Field)
			printf("last frame incomplete, not stored\n");
		else
			write_frame(backward_reference_frame,m_bitstream_framenum-1);
		}
	m_last_bitstream_framenumber = m_bitstream_framenum;
	}


void MpegDecoder::initialize_sequence()
{
  int cc, size;
  static int Table_6_20[3] = {6,8,12};

  /* check scalability mode of enhancement layer */
  if (Two_Streams && (enhan.scalable_mode!=SC_SNR) && (base.scalable_mode!=SC_DP))
    Error("unsupported scalability mode\n");

  /* force MPEG-1 parameters for proper decoder behavior */
  /* see ISO/IEC 13818-2 section D.9.14 */
  if (!base.MPEG2_Flag)
  {
    progressive_sequence = 1;
    progressive_frame = 1;
    picture_structure = FRAME_PICTURE;
    frame_pred_frame_dct = 1;
    chroma_format = CHROMA420;
    matrix_coefficients = 5;
  }

  /* round to nearest multiple of coded macroblocks */
  /* ISO/IEC 13818-2 section 6.3.3 sequence_header() */
  mb_width = (horizontal_size+15)/16;
  mb_height = (base.MPEG2_Flag && !progressive_sequence) ? 2*((vertical_size+31)/32)
                                        : (vertical_size+15)/16;

  Coded_Picture_Width = 16*mb_width;
  Coded_Picture_Height = 16*mb_height;

  /* ISO/IEC 13818-2 sections 6.1.1.8, 6.1.1.9, and 6.1.1.10 */
  Chroma_Width = (chroma_format==CHROMA444) ? Coded_Picture_Width
                                           : Coded_Picture_Width>>1;
  Chroma_Height = (chroma_format!=CHROMA420) ? Coded_Picture_Height
                                            : Coded_Picture_Height>>1;
  
  /* derived based on Table 6-20 in ISO/IEC 13818-2 section 6.3.17 */
  block_count = Table_6_20[chroma_format-1];

  for (cc=0; cc<3; cc++)
  {
    if (cc==0)
      size = Coded_Picture_Width*Coded_Picture_Height;
    else
      size = Chroma_Width*Chroma_Height;

    if (!(backward_reference_frame[cc] = (unsigned char *)malloc(size)))
      Error("backward_reference_frame[] malloc failed\n");

    if (!(forward_reference_frame[cc] = (unsigned char *)malloc(size)))
      Error("forward_reference_frame[] malloc failed\n");

    if (!(auxframe[cc] = (unsigned char *)malloc(size)))
      Error("auxframe[] malloc failed\n");

    if(Ersatz_Flag)
      if (!(substitute_frame[cc] = (unsigned char *)malloc(size)))
        Error("substitute_frame[] malloc failed\n");


    if (base.scalable_mode==SC_SPAT)
    {
      /* this assumes lower layer is 4:2:0 */
      if (!(llframe0[cc] = (unsigned char *)malloc((lower_layer_prediction_horizontal_size*lower_layer_prediction_vertical_size)/(cc?4:1))))
        Error("llframe0 malloc failed\n");
      if (!(llframe1[cc] = (unsigned char *)malloc((lower_layer_prediction_horizontal_size*lower_layer_prediction_vertical_size)/(cc?4:1))))
        Error("llframe1 malloc failed\n");
    }
  }

  /* SCALABILITY: Spatial */
  if (base.scalable_mode==SC_SPAT)
  {
    if (!(lltmp = (short *)malloc(lower_layer_prediction_horizontal_size*((lower_layer_prediction_vertical_size*vertical_subsampling_factor_n)/vertical_subsampling_factor_m)*sizeof(short))))
      Error("lltmp malloc failed\n");
  }

}

void MpegDecoder::get_display_info(display_info& di) const
	{
	di.horizontal_size = horizontal_size;
	di.vertical_size = vertical_size;
	di.chroma_format = chroma_format;
	di.coded_picture_width = Coded_Picture_Width;
	di.coded_picture_height = Coded_Picture_Height;
	di.mpeg2_flag = (base.MPEG2_Flag != 0);
	di.progressive_frame = (progressive_frame != 0);
	di.matrix_coefficients = matrix_coefficients;
	}

void MpegDecoder::finalize_sequence()
{
  int i;

  /* clear flags */
  base.MPEG2_Flag=0;

  for(i=0;i<3;i++)
  {
    free(backward_reference_frame[i]);
    free(forward_reference_frame[i]);
    free(auxframe[i]);

    if (base.scalable_mode==SC_SPAT)
    {
     free(llframe0[i]);
     free(llframe1[i]);
    }
  }

  if (base.scalable_mode==SC_SPAT)
    free(lltmp);
}

void MpegDecoder::decode_picture()
{

  if (picture_structure==FRAME_PICTURE && Second_Field)
  {
    /* recover from illegal number of field pictures */
    printf("odd number of field pictures\n");
    Second_Field = 0;
  }

  /* IMPLEMENTATION: update picture buffer pointers */
  Update_Picture_Buffers();

#ifdef VERIFY 
  //Check_Headers(m_bitstream_framenum, m_sequence_framenum);
#endif /* VERIFY */

  /* ISO/IEC 13818-4 section 2.4.5.4 "frame buffer intercept method" */
  /* (section number based on November 1995 (Dallas) draft of the 
      conformance document) */
  //if(Ersatz_Flag)
    //Substitute_Frame_Buffer(m_bitstream_framenum, m_sequence_framenum);

  /* form spatial scalable picture */
 
  /* form spatial scalable picture */
  /* ISO/IEC 13818-2 section 7.7: Spatial scalability */
  if (base.pict_scal && !Second_Field) 
  {
    Spatial_Prediction();
  }

  /* decode picture data ISO/IEC 13818-2 section 6.2.3.7 */
  picture_data(m_bitstream_framenum);

  /* write or display current or previously decoded reference frame */
  /* ISO/IEC 13818-2 section 6.1.1.11: Frame reordering */
  frame_reorder(m_bitstream_framenum, m_sequence_framenum);

  if (picture_structure!=FRAME_PICTURE)
    Second_Field = !Second_Field;
}

void MpegDecoder::frame_reorder(int bitstream_framenum, int sequence_framenum)
{
  /* tracking variables to insure proper output in spatial scalability */
  static int Oldref_progressive_frame, Newref_progressive_frame;

  if (sequence_framenum!=0)
  {
    if (picture_structure==FRAME_PICTURE || Second_Field)
    {
      if (picture_coding_type==B_TYPE)
        write_frame(auxframe,bitstream_framenum-1);
      else
      {
        Newref_progressive_frame = progressive_frame;
        progressive_frame = Oldref_progressive_frame;

        write_frame(forward_reference_frame,bitstream_framenum-1);

        Oldref_progressive_frame = progressive_frame = Newref_progressive_frame;
      }
    }
  }
  else
    Oldref_progressive_frame = progressive_frame;

}

void MpegDecoder::write_frame(unsigned char *src[], int frame)
	{
	if(m_display == 0) return;
	if (progressive_sequence || progressive_frame || Frame_Store_Flag)
		{
		// progressive
		m_display->update_surface(src, frame, 0, Coded_Picture_Width, vertical_size);
		}
	else
		{
		// interlaced
		m_display->update_surface(src, frame, 0, Coded_Picture_Width<<1, vertical_size>>1);
		m_display->update_surface(src, frame, Coded_Picture_Width, Coded_Picture_Width<<1, vertical_size>>1);
		}
	}

