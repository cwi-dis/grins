#include "mpeg_video.h"

#include "mpeg2con.h"

#include "mpeg_video_bitstream.h"

#include "mpeg_video_globals.h"

// decode headers from one input stream
// until an end of sequence or picture start code is found
bool mpeg_video::get_header()
	{
	for (;;)
		{
		// look for next_start_code
		m_bitstream->next_code();
		unsigned int code = m_bitstream->get_bits32();
		switch (code)
			{
			case MPEG2_SEQUENCE_START_CODE:
				//printf("MPEG2_SEQUENCE_START_CODE\n");
				sequence_header();
				break;
			case MPEG2_GROUP_START_CODE:
				//printf("MPEG2_GROUP_START_CODE\n");
				group_of_pictures_header();
				break;
			case MPEG2_PICTURE_START_CODE:
				//printf("MPEG2_PICTURE_START_CODE\n");
				picture_header();
				return true;
			case MPEG2_SEQUENCE_END_CODE:
				//printf("MPEG2_SEQUENCE_END_CODE\n");
				return false;
			default:
				fprintf(stderr,"Unexpected next_code %08x (ignored)\n",code);
				break;
			}
		}
	return false;
	}

// ISO/IEC 13818-2 section 5.3 */
// Purpose: this function is mainly designed to aid in bitstream conformance
//  testing.  A simple m_bitstream->flush_buffer(1) would do
void mpeg_video::marker_bit(const char *text)
	{
	int marker = m_bitstream->get_bits(1);
#ifdef VERIFY  
	if(!marker)
		printf("ERROR: %s--marker_bit set to 0",text);
#endif
	}

// decode sequence header
void mpeg_video::sequence_header()
{
  int i;
  int pos;

  pos = m_bitstream->m_Bitcnt;
  horizontal_size             = m_bitstream->get_bits(12);
  vertical_size               = m_bitstream->get_bits(12);
  aspect_ratio_information    = m_bitstream->get_bits(4);
  frame_rate_code             = m_bitstream->get_bits(4);
  bit_rate_value              = m_bitstream->get_bits(18);
  marker_bit("sequence_header()");
  vbv_buffer_size             = m_bitstream->get_bits(10);
  constrained_parameters_flag = m_bitstream->get_bits(1);

  if((m_pld->load_intra_quantizer_matrix = m_bitstream->get_bits(1)))
  {
    for (i=0; i<64; i++)
      m_pld->intra_quantizer_matrix[scan[ZIG_ZAG][i]] = m_bitstream->get_bits(8);
  }
  else
  {
    for (i=0; i<64; i++)
      m_pld->intra_quantizer_matrix[i] = default_intra_quantizer_matrix[i];
  }

  if((m_pld->load_non_intra_quantizer_matrix = m_bitstream->get_bits(1)))
  {
    for (i=0; i<64; i++)
      m_pld->non_intra_quantizer_matrix[scan[ZIG_ZAG][i]] = m_bitstream->get_bits(8);
  }
  else
  {
    for (i=0; i<64; i++)
      m_pld->non_intra_quantizer_matrix[i] = 16;
  }

  /* copy luminance to chrominance matrices */
  for (i=0; i<64; i++)
  {
    m_pld->chroma_intra_quantizer_matrix[i] =
      m_pld->intra_quantizer_matrix[i];

    m_pld->chroma_non_intra_quantizer_matrix[i] =
      m_pld->non_intra_quantizer_matrix[i];
  }

#ifdef VERBOSE
  if (Verbose_Flag > NO_LAYER)
  {
    printf("sequence header (byte %d)\n",(pos>>3)-4);
    if (Verbose_Flag > SEQUENCE_LAYER)
    {
      printf("  horizontal_size=%d\n",horizontal_size);
      printf("  vertical_size=%d\n",vertical_size);
      printf("  aspect_ratio_information=%d\n",aspect_ratio_information);
      printf("  frame_rate_code=%d",frame_rate_code);
      printf("  bit_rate_value=%d\n",bit_rate_value);
      printf("  vbv_buffer_size=%d\n",vbv_buffer_size);
      printf("  constrained_parameters_flag=%d\n",constrained_parameters_flag);
      printf("  load_intra_quantizer_matrix=%d\n",m_pld->load_intra_quantizer_matrix);
      printf("  load_non_intra_quantizer_matrix=%d\n",m_pld->load_non_intra_quantizer_matrix);
    }
  }
#endif /* VERBOSE */

#ifdef VERIFY
  verify_sequence_header++;
#endif /* VERIFY */

  extension_and_user_data();
}

// decode group of pictures header 
// ISO/IEC 13818-2 section 6.2.2.6 
void mpeg_video::group_of_pictures_header()
{
  int pos;

  //if (ld == &base)
  if(true)
  {
    Temporal_Reference_Base = True_Framenum_max + 1; 	// *CH*
    Temporal_Reference_GOP_Reset = 1;
  }
  pos = m_bitstream->m_Bitcnt;
  drop_flag   = m_bitstream->get_bits(1);
  hour        = m_bitstream->get_bits(5);
  minute      = m_bitstream->get_bits(6);
  marker_bit("group_of_pictures_header()");
  sec         = m_bitstream->get_bits(6);
  frame       = m_bitstream->get_bits(6);
  closed_gop  = m_bitstream->get_bits(1);
  broken_link = m_bitstream->get_bits(1);

#ifdef VERBOSE
  if (Verbose_Flag > NO_LAYER)
  {
    printf("group of pictures (byte %d)\n",(pos>>3)-4);
    if (Verbose_Flag > SEQUENCE_LAYER)
    {
      printf("  drop_flag=%d\n",drop_flag);
      printf("  timecode %d:%02d:%02d:%02d\n",hour,minute,sec,frame);
      printf("  closed_gop=%d\n",closed_gop);
      printf("  broken_link=%d\n",broken_link);
    }
  }
#endif // VERBOSE

#ifdef VERIFY
  verify_group_of_pictures_header++;
#endif // VERIFY 

  extension_and_user_data();
}


// decode picture header
// ISO/IEC 13818-2 section 6.2.3
void mpeg_video::picture_header()
{
  int pos;
  int Extra_Information_Byte_Count;

  // unless later overwritten by picture_spatial_scalable_extension()
  m_pld->pict_scal = 0; 
  
  pos = m_bitstream->m_Bitcnt;
  temporal_reference  = m_bitstream->get_bits(10);
  picture_coding_type = m_bitstream->get_bits(3);
  vbv_delay           = m_bitstream->get_bits(16);

  if (picture_coding_type==P_TYPE || picture_coding_type==B_TYPE)
  {
    full_pel_forward_vector = m_bitstream->get_bits(1);
    forward_f_code = m_bitstream->get_bits(3);
  }
  if (picture_coding_type==B_TYPE)
  {
    full_pel_backward_vector = m_bitstream->get_bits(1);
    backward_f_code = m_bitstream->get_bits(3);
  }

#ifdef VERBOSE
  if (Verbose_Flag>NO_LAYER)
  {
    printf("picture header (byte %d)\n",(pos>>3)-4);
    if (Verbose_Flag>SEQUENCE_LAYER)
    {
      printf("  temporal_reference=%d\n",temporal_reference);
      printf("  picture_coding_type=%d\n",picture_coding_type);
      printf("  vbv_delay=%d\n",vbv_delay);
      if (picture_coding_type==P_TYPE || picture_coding_type==B_TYPE)
      {
        printf("  full_pel_forward_vector=%d\n",full_pel_forward_vector);
        printf("  forward_f_code =%d\n",forward_f_code);
      }
      if (picture_coding_type==B_TYPE)
      {
        printf("  full_pel_backward_vector=%d\n",full_pel_backward_vector);
        printf("  backward_f_code =%d\n",backward_f_code);
      }
    }
  }
#endif // VERBOSE

#ifdef VERIFY
  verify_picture_header++;
#endif // VERIFY

  Extra_Information_Byte_Count = 
    extra_bit_information();
  
  extension_and_user_data();

  // update tracking information used to assist spatial scalability
  Update_Temporal_Reference_Tacking_Data();
}



// decode slice header
// ISO/IEC 13818-2 section 6.2.4
int mpeg_video::slice_header()
{
  int slice_vertical_position_extension;
  int quantizer_scale_code;
  int pos;
  int slice_picture_id_enable = 0;
  int slice_picture_id = 0;
  int extra_information_slice = 0;

  pos = m_bitstream->m_Bitcnt;

  slice_vertical_position_extension =
    (m_pld->MPEG2_Flag && vertical_size>2800) ? m_bitstream->get_bits(3) : 0;

  if (m_pld->scalable_mode==SC_DP)
    m_pld->priority_breakpoint = m_bitstream->get_bits(7);

  quantizer_scale_code = m_bitstream->get_bits(5);
  m_pld->quantizer_scale =
    m_pld->MPEG2_Flag ? (m_pld->q_scale_type ? Non_Linear_quantizer_scale[quantizer_scale_code] : quantizer_scale_code<<1) : quantizer_scale_code;

  // slice_id introduced in March 1995 as part of the video corridendum
   //  (after the IS was drafted in November 1994)
  if (m_bitstream->get_bits(1))
  {
    m_pld->intra_slice = m_bitstream->get_bits(1);

    slice_picture_id_enable = m_bitstream->get_bits(1);
	slice_picture_id = m_bitstream->get_bits(6);

    extra_information_slice = extra_bit_information();
  }
  else
    m_pld->intra_slice = 0;

#ifdef VERBOSE
  if (Verbose_Flag>PICTURE_LAYER)
  {
    printf("slice header (byte %d)\n",(pos>>3)-4);
    if (Verbose_Flag>SLICE_LAYER)
    {
      if (m_pld->MPEG2_Flag && vertical_size>2800)
        printf("  slice_vertical_position_extension=%d\n",slice_vertical_position_extension);
  
      if (ld->scalable_mode==SC_DP)
        printf("  priority_breakpoint=%d\n",ld->priority_breakpoint);

      printf("  quantizer_scale_code=%d\n",quantizer_scale_code);

      printf("  slice_picture_id_enable = %d\n", slice_picture_id_enable);

      if(slice_picture_id_enable)
        printf("  slice_picture_id = %d\n", slice_picture_id);

    }
  }
#endif // VERBOSE

#ifdef VERIFY
  verify_slice_header++;
#endif // VERIFY


  return slice_vertical_position_extension;
}


// decode extension and user data 
// ISO/IEC 13818-2 section 6.2.2.2 
void mpeg_video::extension_and_user_data()
{
  int code,ext_ID;

  m_bitstream->next_start_code();

  while ((code = m_bitstream->next_bits(32))==MPEG2_EXTENSION_START_CODE || code==MPEG2_USER_DATA_START_CODE)
  {
    if (code==MPEG2_EXTENSION_START_CODE)
    {
      m_bitstream->flush_buffer32();
      ext_ID = m_bitstream->get_bits(4);
      switch (ext_ID)
      {
      case SEQUENCE_EXTENSION_ID:
        sequence_extension();
        break;
      case SEQUENCE_DISPLAY_EXTENSION_ID:
        sequence_display_extension();
        break;
      case QUANT_MATRIX_EXTENSION_ID:
        quant_matrix_extension();
        break;
      case SEQUENCE_SCALABLE_EXTENSION_ID:
        sequence_scalable_extension();
        break;
      case PICTURE_DISPLAY_EXTENSION_ID:
        picture_display_extension();
        break;
      case PICTURE_CODING_EXTENSION_ID:
        picture_coding_extension();
        break;
      case PICTURE_SPATIAL_SCALABLE_EXTENSION_ID:
        picture_spatial_scalable_extension();
        break;
      case PICTURE_TEMPORAL_SCALABLE_EXTENSION_ID:
        picture_temporal_scalable_extension();
        break;
      case COPYRIGHT_EXTENSION_ID:
        copyright_extension();
        break;
     default:
        fprintf(stderr,"reserved extension start code ID %d\n",ext_ID);
        break;
      }
      m_bitstream->next_start_code();
    }
    else
    {
#ifdef VERBOSE
      if (Verbose_Flag>NO_LAYER)
        printf("user data\n");
#endif // VERBOSE 
      m_bitstream->flush_buffer32();
      user_data();
    }
  }
}

// decode sequence extension */
// ISO/IEC 13818-2 section 6.2.2.3 */
void mpeg_video::sequence_extension()
{
  int horizontal_size_extension;
  int vertical_size_extension;
  int bit_rate_extension;
  int vbv_buffer_size_extension;
  //int pos;

  /* derive bit position for trace */
#ifdef VERBOSE
  pos = m_bitstream->m_Bitcnt;
#endif

  m_pld->MPEG2_Flag = 1;

  m_pld->scalable_mode = SC_NONE; // unless overwritten by sequence_scalable_extension()
  layer_id = 0;                // unless overwritten by sequence_scalable_extension()
  
  profile_and_level_indication = m_bitstream->get_bits(8);
  progressive_sequence         = m_bitstream->get_bits(1);
  chroma_format                = m_bitstream->get_bits(2);
  horizontal_size_extension    = m_bitstream->get_bits(2);
  vertical_size_extension      = m_bitstream->get_bits(2);
  bit_rate_extension           = m_bitstream->get_bits(12);
  marker_bit("sequence_extension");
  vbv_buffer_size_extension    = m_bitstream->get_bits(8);
  low_delay                    = m_bitstream->get_bits(1);
  frame_rate_extension_n       = m_bitstream->get_bits(2);
  frame_rate_extension_d       = m_bitstream->get_bits(5);

  frame_rate = frame_rate_Table[frame_rate_code] *
    ((frame_rate_extension_n+1)/(frame_rate_extension_d+1));

  /* special case for 422 profile & level must be made */
  if((profile_and_level_indication>>7) & 1)
  {  /* escape bit of profile_and_level_indication set */
  
    /* 4:2:2 Profile @ Main Level */
    if((profile_and_level_indication&15)==5)
    {
      profile = PROFILE_422;
      level   = MAIN_LEVEL;  
    }
  }
  else
  {
    profile = profile_and_level_indication >> 4;  /* Profile is upper nibble */
    level   = profile_and_level_indication & 0xF;  /* Level is lower nibble */
  }
  
 
  horizontal_size = (horizontal_size_extension<<12) | (horizontal_size&0x0fff);
  vertical_size = (vertical_size_extension<<12) | (vertical_size&0x0fff);


  /* ISO/IEC 13818-2 does not define bit_rate_value to be composed of
   * both the original bit_rate_value parsed in sequence_header() and
   * the optional bit_rate_extension in sequence_extension_header(). 
   * However, we use it for bitstream verification purposes. 
   */

  bit_rate_value += (bit_rate_extension << 18);
  bit_rate = ((double) bit_rate_value) * 400.0;
  vbv_buffer_size += (vbv_buffer_size_extension << 10);

#ifdef VERBOSE
  if (Verbose_Flag>NO_LAYER)
  {
    printf("sequence extension (byte %d)\n",(pos>>3)-4);

    if (Verbose_Flag>SEQUENCE_LAYER)
    {
      printf("  profile_and_level_indication=%d\n",profile_and_level_indication);

      if (profile_and_level_indication<128)
      {
        printf("    profile=%d, level=%d\n",profile,level);
      }

      printf("  progressive_sequence=%d\n",progressive_sequence);
      printf("  chroma_format=%d\n",chroma_format);
      printf("  horizontal_size_extension=%d\n",horizontal_size_extension);
      printf("  vertical_size_extension=%d\n",vertical_size_extension);
      printf("  bit_rate_extension=%d\n",bit_rate_extension);
      printf("  vbv_buffer_size_extension=%d\n",vbv_buffer_size_extension);
      printf("  low_delay=%d\n",low_delay);
      printf("  frame_rate_extension_n=%d\n",frame_rate_extension_n);
      printf("  frame_rate_extension_d=%d\n",frame_rate_extension_d);
    }
  }
#endif /* VERBOSE */

#ifdef VERIFY
  verify_sequence_extension++;
#endif /* VERIFY */


}


// decode sequence display extension
void mpeg_video::sequence_display_extension()
{
  int pos;

  pos = m_bitstream->m_Bitcnt;
  video_format      = m_bitstream->get_bits(3);
  color_description = m_bitstream->get_bits(1);

  if (color_description)
  {
    color_primaries          = m_bitstream->get_bits(8);
    transfer_characteristics = m_bitstream->get_bits(8);
    matrix_coefficients      = m_bitstream->get_bits(8);
  }

  display_horizontal_size = m_bitstream->get_bits(14);
  marker_bit("sequence_display_extension");
  display_vertical_size   = m_bitstream->get_bits(14);

#ifdef VERBOSE
  if (Verbose_Flag>NO_LAYER)
  {
    printf("sequence display extension (byte %d)\n",(pos>>3)-4);
    if (Verbose_Flag>SEQUENCE_LAYER)
    {

      printf("  video_format=%d\n",video_format);
      printf("  color_description=%d\n",color_description);

      if (color_description)
      {
        printf("    color_primaries=%d\n",color_primaries);
        printf("    transfer_characteristics=%d\n",transfer_characteristics);
        printf("    matrix_coefficients=%d\n",matrix_coefficients);
      }
      printf("  display_horizontal_size=%d\n",display_horizontal_size);
      printf("  display_vertical_size=%d\n",display_vertical_size);
    }
  }
#endif // VERBOSE

#ifdef VERIFY
  verify_sequence_display_extension++;
#endif // VERIFY

}


// decode quant matrix entension */
// ISO/IEC 13818-2 section 6.2.3.2 */
void mpeg_video::quant_matrix_extension()
{
  int i;
  int pos;

  pos = m_bitstream->m_Bitcnt;

  if((m_pld->load_intra_quantizer_matrix = m_bitstream->get_bits(1)))
  {
    for (i=0; i<64; i++)
    {
      m_pld->chroma_intra_quantizer_matrix[scan[ZIG_ZAG][i]]
      = m_pld->intra_quantizer_matrix[scan[ZIG_ZAG][i]]
      = m_bitstream->get_bits(8);
    }
  }

  if((m_pld->load_non_intra_quantizer_matrix = m_bitstream->get_bits(1)))
  {
    for (i=0; i<64; i++)
    {
      m_pld->chroma_non_intra_quantizer_matrix[scan[ZIG_ZAG][i]]
      = m_pld->non_intra_quantizer_matrix[scan[ZIG_ZAG][i]]
      = m_bitstream->get_bits(8);
    }
  }

  if((m_pld->load_chroma_intra_quantizer_matrix = m_bitstream->get_bits(1)))
  {
    for (i=0; i<64; i++)
      m_pld->chroma_intra_quantizer_matrix[scan[ZIG_ZAG][i]] = m_bitstream->get_bits(8);
  }

  if((m_pld->load_chroma_non_intra_quantizer_matrix = m_bitstream->get_bits(1)))
  {
    for (i=0; i<64; i++)
      m_pld->chroma_non_intra_quantizer_matrix[scan[ZIG_ZAG][i]] = m_bitstream->get_bits(8);
  }

#ifdef VERBOSE
  if (Verbose_Flag>NO_LAYER)
  {
    printf("quant matrix extension (byte %d)\n",(pos>>3)-4);
    printf("  load_intra_quantizer_matrix=%d\n",
      m_pld->load_intra_quantizer_matrix);
    printf("  load_non_intra_quantizer_matrix=%d\n",
      m_pld->load_non_intra_quantizer_matrix);
    printf("  load_chroma_intra_quantizer_matrix=%d\n",
      m_pld->load_chroma_intra_quantizer_matrix);
    printf("  load_chroma_non_intra_quantizer_matrix=%d\n",
      m_pld->load_chroma_non_intra_quantizer_matrix);
  }
#endif /* VERBOSE */

#ifdef VERIFY
  verify_quant_matrix_extension++;
#endif /* VERIFY */

}


// decode sequence scalable extension
// ISO/IEC 13818-2   section 6.2.2.5
void mpeg_video::sequence_scalable_extension()
{
  int pos;

  pos = m_bitstream->m_Bitcnt;

  /* values (without the +1 offset) of scalable_mode are defined in 
     Table 6-10 of ISO/IEC 13818-2 */
  m_pld->scalable_mode = m_bitstream->get_bits(2) + 1; /* add 1 to make SC_DP != SC_NONE */

  layer_id = m_bitstream->get_bits(4);

  if (m_pld->scalable_mode==SC_SPAT)
  {
    lower_layer_prediction_horizontal_size = m_bitstream->get_bits(14);
    marker_bit("sequence_scalable_extension()");
    lower_layer_prediction_vertical_size   = m_bitstream->get_bits(14); 
    horizontal_subsampling_factor_m        = m_bitstream->get_bits(5);
    horizontal_subsampling_factor_n        = m_bitstream->get_bits(5);
    vertical_subsampling_factor_m          = m_bitstream->get_bits(5);
    vertical_subsampling_factor_n          = m_bitstream->get_bits(5);
  }

  if (m_pld->scalable_mode==SC_TEMP)
    error("temporal scalability not implemented\n");

#ifdef VERBOSE
  if (Verbose_Flag>NO_LAYER)
  {
    printf("sequence scalable extension (byte %d)\n",(pos>>3)-4);
    if (Verbose_Flag>SEQUENCE_LAYER)
    {
      printf("  scalable_mode=%d\n",m_pld->scalable_mode-1);
      printf("  layer_id=%d\n",layer_id);
      if (m_pld->scalable_mode==SC_SPAT)
      {
        printf("    lower_layer_prediction_horiontal_size=%d\n",
          lower_layer_prediction_horizontal_size);
        printf("    lower_layer_prediction_vertical_size=%d\n",
          lower_layer_prediction_vertical_size);
        printf("    horizontal_subsampling_factor_m=%d\n",
          horizontal_subsampling_factor_m);
        printf("    horizontal_subsampling_factor_n=%d\n",
          horizontal_subsampling_factor_n);
        printf("    vertical_subsampling_factor_m=%d\n",
          vertical_subsampling_factor_m);
        printf("    vertical_subsampling_factor_n=%d\n",
          vertical_subsampling_factor_n);
      }
    }
  }
#endif /* VERBOSE */

#ifdef VERIFY
  verify_sequence_scalable_extension++;
#endif /* VERIFY */

}


/* decode picture display extension */
/* ISO/IEC 13818-2 section 6.2.3.3. */
void mpeg_video::picture_display_extension()
{
  int i;
  int number_of_frame_center_offsets;
  int pos;

  pos = m_bitstream->m_Bitcnt;
  /* based on ISO/IEC 13818-2 section 6.3.12 
    (November 1994) Picture display extensions */

  /* derive number_of_frame_center_offsets */
  if(progressive_sequence)
  {
    if(repeat_first_field)
    {
      if(top_field_first)
        number_of_frame_center_offsets = 3;
      else
        number_of_frame_center_offsets = 2;
    }
    else
    {
      number_of_frame_center_offsets = 1;
    }
  }
  else
  {
    if(picture_structure!=FRAME_PICTURE)
    {
      number_of_frame_center_offsets = 1;
    }
    else
    {
      if(repeat_first_field)
        number_of_frame_center_offsets = 3;
      else
        number_of_frame_center_offsets = 2;
    }
  }


  /* now parse */
  for (i=0; i<number_of_frame_center_offsets; i++)
  {
    frame_center_horizontal_offset[i] = m_bitstream->get_bits(16);
    marker_bit("picture_display_extension, first marker bit");
    
    frame_center_vertical_offset[i]   = m_bitstream->get_bits(16);
    marker_bit("picture_display_extension, second marker bit");
  }

#ifdef VERBOSE
  if (Verbose_Flag>NO_LAYER)
  {
    printf("picture display extension (byte %d)\n",(pos>>3)-4);
    if (Verbose_Flag>SEQUENCE_LAYER)
    {

      for (i=0; i<number_of_frame_center_offsets; i++)
      {
        printf("  frame_center_horizontal_offset[%d]=%d\n",i,
          frame_center_horizontal_offset[i]);
        printf("  frame_center_vertical_offset[%d]=%d\n",i,
          frame_center_vertical_offset[i]);
      }
    }
  }
#endif /* VERBOSE */

#ifdef VERIFY
  verify_picture_display_extension++;
#endif /* VERIFY */

}


/* decode picture coding extension */
void mpeg_video::picture_coding_extension()
{
  int pos;

  pos = m_bitstream->m_Bitcnt;

  f_code[0][0] = m_bitstream->get_bits(4);
  f_code[0][1] = m_bitstream->get_bits(4);
  f_code[1][0] = m_bitstream->get_bits(4);
  f_code[1][1] = m_bitstream->get_bits(4);

  intra_dc_precision         = m_bitstream->get_bits(2);
  picture_structure          = m_bitstream->get_bits(2);
  top_field_first            = m_bitstream->get_bits(1);
  frame_pred_frame_dct       = m_bitstream->get_bits(1);
  concealment_motion_vectors = m_bitstream->get_bits(1);
  m_pld->q_scale_type           = m_bitstream->get_bits(1);
  intra_vlc_format           = m_bitstream->get_bits(1);
  m_pld->alternate_scan         = m_bitstream->get_bits(1);
  repeat_first_field         = m_bitstream->get_bits(1);
  chroma_420_type            = m_bitstream->get_bits(1);
  progressive_frame          = m_bitstream->get_bits(1);
  composite_display_flag     = m_bitstream->get_bits(1);

  if (composite_display_flag)
  {
    v_axis            = m_bitstream->get_bits(1);
    field_sequence    = m_bitstream->get_bits(3);
    sub_carrier       = m_bitstream->get_bits(1);
    burst_amplitude   = m_bitstream->get_bits(7);
    sub_carrier_phase = m_bitstream->get_bits(8);
  }

#ifdef VERBOSE
  if (Verbose_Flag>NO_LAYER)
  {
    printf("picture coding extension (byte %d)\n",(pos>>3)-4);
    if (Verbose_Flag>SEQUENCE_LAYER)
    {
      printf("  forward horizontal f_code=%d\n", f_code[0][0]);
      printf("  forward vertical f_code=%d\n", f_code[0][1]);
      printf("  backward horizontal f_code=%d\n", f_code[1][0]);
      printf("  backward_vertical f_code=%d\n", f_code[1][1]);
      printf("  intra_dc_precision=%d\n",intra_dc_precision);
      printf("  picture_structure=%d\n",picture_structure);
      printf("  top_field_first=%d\n",top_field_first);
      printf("  frame_pred_frame_dct=%d\n",frame_pred_frame_dct);
      printf("  concealment_motion_vectors=%d\n",concealment_motion_vectors);
      printf("  q_scale_type=%d\n",m_pld->q_scale_type);
      printf("  intra_vlc_format=%d\n",intra_vlc_format);
      printf("  alternate_scan=%d\n",m_pld->alternate_scan);
      printf("  repeat_first_field=%d\n",repeat_first_field);
      printf("  chroma_420_type=%d\n",chroma_420_type);
      printf("  progressive_frame=%d\n",progressive_frame);
      printf("  composite_display_flag=%d\n",composite_display_flag);

      if (composite_display_flag)
      {
        printf("    v_axis=%d\n",v_axis);
        printf("    field_sequence=%d\n",field_sequence);
        printf("    sub_carrier=%d\n",sub_carrier);
        printf("    burst_amplitude=%d\n",burst_amplitude);
        printf("    sub_carrier_phase=%d\n",sub_carrier_phase);
      }
    }
  }
#endif /* VERBOSE */

#ifdef VERIFY
  verify_picture_coding_extension++;
#endif /* VERIFY */
}


/* decode picture spatial scalable extension */
/* ISO/IEC 13818-2 section 6.2.3.5. */
void mpeg_video::picture_spatial_scalable_extension()
{
  int pos;

  pos = m_bitstream->m_Bitcnt;

  m_pld->pict_scal = 1; /* use spatial scalability in this picture */

  lower_layer_temporal_reference = m_bitstream->get_bits(10);
  marker_bit("picture_spatial_scalable_extension(), first marker bit");
  lower_layer_horizontal_offset = m_bitstream->get_bits(15);
  if (lower_layer_horizontal_offset>=16384)
    lower_layer_horizontal_offset-= 32768;
  marker_bit("picture_spatial_scalable_extension(), second marker bit");
  lower_layer_vertical_offset = m_bitstream->get_bits(15);
  if (lower_layer_vertical_offset>=16384)
    lower_layer_vertical_offset-= 32768;
  spatial_temporal_weight_code_table_index = m_bitstream->get_bits(2);
  lower_layer_progressive_frame = m_bitstream->get_bits(1);
  lower_layer_deinterlaced_field_select = m_bitstream->get_bits(1);

#ifdef VERBOSE
  if (Verbose_Flag>NO_LAYER)
  {
    printf("picture spatial scalable extension (byte %d)\n",(pos>>3)-4);
    if (Verbose_Flag>SEQUENCE_LAYER)
    {
      printf("  lower_layer_temporal_reference=%d\n",lower_layer_temporal_reference);
      printf("  lower_layer_horizontal_offset=%d\n",lower_layer_horizontal_offset);
      printf("  lower_layer_vertical_offset=%d\n",lower_layer_vertical_offset);
      printf("  spatial_temporal_weight_code_table_index=%d\n",
        spatial_temporal_weight_code_table_index);
      printf("  lower_layer_progressive_frame=%d\n",lower_layer_progressive_frame);
      printf("  lower_layer_deinterlaced_field_select=%d\n",lower_layer_deinterlaced_field_select);
    }
  }
#endif /* VERBOSE */

#ifdef VERIFY
  verify_picture_spatial_scalable_extension++;
#endif /* VERIFY */

}


/* decode picture temporal scalable extension
 *
 * not implemented
 */
/* ISO/IEC 13818-2 section 6.2.3.4. */
void mpeg_video::picture_temporal_scalable_extension()
{
  error("temporal scalability not supported\n");

#ifdef VERIFY
  verify_picture_temporal_scalable_extension++;
#endif /* VERIFY */
}


/* decode extra bit information */
/* ISO/IEC 13818-2 section 6.2.3.4. */
int mpeg_video::extra_bit_information()
{
  int Byte_Count = 0;

  while (m_bitstream->get_bits1())
  {
    m_bitstream->flush_buffer(8);
    Byte_Count++;
  }

  return(Byte_Count);
}



// ISO/IEC 13818-2  sections 6.3.4.1 and 6.2.2.2.2
void mpeg_video::user_data()
	{
	// skip ahead to the next start code
	m_bitstream->next_start_code();
	}



// Copyright extension 
// ISO/IEC 13818-2 section 6.2.3.6. 
// (header added in November, 1994 to the IS document) 
void mpeg_video::copyright_extension()
{
  int pos;
  int reserved_data;
  int Verbose_Flag = 0;
  pos = m_bitstream->m_Bitcnt;
  

  copyright_flag =       m_bitstream->get_bits(1); 
  copyright_identifier = m_bitstream->get_bits(8);
  original_or_copy =     m_bitstream->get_bits(1);
  
  /* reserved */
  reserved_data = m_bitstream->get_bits(7);

  marker_bit("copyright_extension(), first marker bit");
  copyright_number_1 =   m_bitstream->get_bits(20);
  marker_bit("copyright_extension(), second marker bit");
  copyright_number_2 =   m_bitstream->get_bits(22);
  marker_bit("copyright_extension(), third marker bit");
  copyright_number_3 =   m_bitstream->get_bits(22);

  if(Verbose_Flag>NO_LAYER)
  {
    printf("copyright_extension (byte %d)\n",(pos>>3)-4);
    if (Verbose_Flag>SEQUENCE_LAYER)
    {
      printf("  copyright_flag =%d\n",copyright_flag);
        
      printf("  copyright_identifier=%d\n",copyright_identifier);
        
      printf("  original_or_copy = %d (original=1, copy=0)\n",
        original_or_copy);
        
      printf("  copyright_number_1=%d\n",copyright_number_1);
      printf("  copyright_number_2=%d\n",copyright_number_2);
      printf("  copyright_number_3=%d\n",copyright_number_3);
    }
  }

#ifdef VERIFY
  verify_copyright_extension++;
#endif /* VERIFY */
}



// introduced in September 1995 to assist Spatial Scalability
void mpeg_video::Update_Temporal_Reference_Tacking_Data()
{
  static int temporal_reference_wrap  = 0;
  static int temporal_reference_old   = 0;

  if(true) // (ld == &base)			/* *CH* */
  {
    if (picture_coding_type!=B_TYPE && temporal_reference!=temporal_reference_old) 	
    /* check first field of */
    {							
       /* non-B-frame */
      if (temporal_reference_wrap) 		
      {/* wrap occured at previous I- or P-frame */	
       /* now all intervening B-frames which could 
          still have high temporal_reference values are done  */
        Temporal_Reference_Base += 1024;
	    temporal_reference_wrap = 0;
      }
      
      /* distinguish from a reset */
      if (temporal_reference<temporal_reference_old && !Temporal_Reference_GOP_Reset)	
	    temporal_reference_wrap = 1;  /* we must have just passed a GOP-Header! */
      
      temporal_reference_old = temporal_reference;
      Temporal_Reference_GOP_Reset = 0;
    }

    True_Framenum = Temporal_Reference_Base + temporal_reference;
    
    /* temporary wrap of TR at 1024 for M frames */
    if (temporal_reference_wrap && temporal_reference <= temporal_reference_old)	
      True_Framenum += 1024;				

    True_Framenum_max = (True_Framenum > True_Framenum_max) ?
                        True_Framenum : True_Framenum_max;
  }
}
