
#include "mpeg_video.h"

#include "mpeg2con.h"
#include "mpeg_video_bitstream.h"

#include <memory.h> // memset

#define GLOBAL
#include "mpeg_video_globals.h"

unsigned char *Clip = NULL;

int mpeg_video::s_refcount = 0;

mpeg_video::mpeg_video(mpeg_video_bitstream *stream)
:	m_pld(NULL),
	m_bitstream(stream),
	m_display(NULL),
	m_bitstream_framenum(0),
	m_sequence_framenum(0),
	m_clip_ptr(NULL)
	{	
	// reset all variables except the above
	reset_state_variables();
	mpeg_video::s_refcount++;

	m_pld = new mpeg_layer_data;
	memset(m_pld, 0, sizeof(mpeg_layer_data));
	
	// init clip table 
	if(Clip == NULL)
		{
		m_clip_ptr = Clip = new uchar_t[1024]; 
		Clip += 384;
		for (int i=-384; i<640; i++)
			Clip[i] = (i<0) ? 0 : ((i>255) ? 255 : i);
		}

	// init fast IDCT transform
	initialize_fast_idct();
	}

mpeg_video::~mpeg_video()
	{
	finalize_sequence();
	delete m_pld;
	mpeg_video::s_refcount--;
	if(mpeg_video::s_refcount == 0)
		{
		delete[] m_clip_ptr;
		Clip = NULL;
		}
	}

void mpeg_video::error(const char *text)
	{
	fprintf(stderr,text);
	exit(1);
	}

void mpeg_video::initialize_sequence()
	{
	static int Table_6_20[3] = {6,8,12};

	// check scalability mode of enhancement layer */
	//if (Two_Streams && (enhan.scalable_mode!=SC_SNR) && (base.scalable_mode!=SC_DP))
	//	error("unsupported scalability mode\n");

	// force MPEG-1 parameters for proper decoder behavior */
	// see ISO/IEC 13818-2 section D.9.14 */
	if (!m_pld->MPEG2_Flag)
		{
		progressive_sequence = 1;
		progressive_frame = 1;
		picture_structure = FRAME_PICTURE;
		frame_pred_frame_dct = 1;
		chroma_format = CHROMA420;
		matrix_coefficients = 5;
		}

	  // round to nearest multiple of coded macroblocks 
	  // ISO/IEC 13818-2 section 6.3.3 sequence_header()
	  mb_width = (horizontal_size+15)/16;
	  mb_height = (m_pld->MPEG2_Flag && !progressive_sequence) ? 2*((vertical_size+31)/32)
											: (vertical_size+15)/16;

	  Coded_Picture_Width = 16*mb_width;
	  Coded_Picture_Height = 16*mb_height;

	  // ISO/IEC 13818-2 sections 6.1.1.8, 6.1.1.9, and 6.1.1.10 
	  Chroma_Width = (chroma_format==CHROMA444) ? Coded_Picture_Width
											   : Coded_Picture_Width>>1;
	  Chroma_Height = (chroma_format!=CHROMA420) ? Coded_Picture_Height
                                            : Coded_Picture_Height>>1;
  
	  // derived based on Table 6-20 in ISO/IEC 13818-2 section 6.3.17 
	  block_count = Table_6_20[chroma_format-1];
	
	for (int cc=0; cc<3; cc++)
		{
		int size;
		if (cc==0)
		  size = Coded_Picture_Width*Coded_Picture_Height;
		else
		  size = Chroma_Width*Chroma_Height;

		backward_reference_frame[cc] = new uchar_t[size];
		forward_reference_frame[cc] = new uchar_t[size];
		auxframe[cc] = new uchar_t[size];

		if(Ersatz_Flag)
			substitute_frame[cc] = new uchar_t[size];


		if (m_pld->scalable_mode==SC_SPAT)
			{
			 // this assumes lower layer is 4:2:0 
			int n = (lower_layer_prediction_horizontal_size*lower_layer_prediction_vertical_size)/(cc?4:1);
			llframe0[cc] =  new uchar_t[n];
			
			n = (lower_layer_prediction_horizontal_size*lower_layer_prediction_vertical_size)/(cc?4:1);
			llframe1[cc] =  new uchar_t[n];
			}
		}

	// SCALABILITY: Spatial
	if (m_pld->scalable_mode==SC_SPAT)
		{
		int n = lower_layer_prediction_horizontal_size*((lower_layer_prediction_vertical_size*vertical_subsampling_factor_n)/vertical_subsampling_factor_m)*sizeof(short);
		lltmp = (short*) new uchar_t[n];
		}
	}

void mpeg_video::finalize_sequence()
	{
	for(int i=0;i<3;i++)
		{
		if(backward_reference_frame[i] != NULL) 
			delete[] backward_reference_frame[i];
		if(forward_reference_frame[i] != NULL)
			delete[] forward_reference_frame[i];
		if(auxframe[i] != NULL)
			delete[] auxframe[i];

		if (m_pld->scalable_mode==SC_SPAT)
			{
			if(llframe0[i] != NULL) delete[] llframe0[i];
			if(llframe1[i] != NULL) delete[] llframe1[i];
			}
		}
	if (m_pld->scalable_mode==SC_SPAT)
		{
		if(lltmp != NULL) delete[] lltmp;
		}

	// pointers to generic picture buffers
	backward_reference_frame[0] = backward_reference_frame[1] = backward_reference_frame[2] = 0;
	forward_reference_frame[0] = forward_reference_frame[1] = forward_reference_frame[2] = 0;

	auxframe[0] = auxframe[1] = auxframe[2] = 0;
	current_frame[0] = current_frame[1] = current_frame[2] = 0;
	substitute_frame[0] = substitute_frame[1] = substitute_frame[2] = 0;


	// pointers to scalability picture buffers
	llframe0[0] = llframe0[1] = llframe0[2] = 0;
	llframe1[0] = llframe1[1] = llframe1[2] = 0;

	lltmp = 0;
	}

void mpeg_video::reset_framenum()
	{
	m_bitstream_framenum = 0;
	m_sequence_framenum = 0;
	}

void mpeg_video::update_framenum()
	{
	if (!Second_Field)
		{
		m_bitstream_framenum++;
		m_sequence_framenum++;
		}
	}

void mpeg_video::decode_picture()
	{
	if (picture_structure==FRAME_PICTURE && Second_Field)
		{
		// recover from illegal number of field pictures
		printf("odd number of field pictures\n");
		Second_Field = 0;
		}

	// IMPLEMENTATION: update picture buffer pointers
	update_picture_buffers();

	 // ISO/IEC 13818-4 section 2.4.5.4 "frame buffer intercept method" 
	 // (section number based on November 1995 (Dallas) draft of the 
	 //   conformance document) 
	 //if(Ersatz_Flag)
		//substitute_frame_buffer(m_bitstream_framenum, m_sequence_framenum);

  // form spatial scalable picture 
 
	// form spatial scalable picture 
	// ISO/IEC 13818-2 section 7.7: Spatial scalability 
	if (m_pld->pict_scal && !Second_Field) 
		{
		spatial_prediction();
		}

	// decode picture data ISO/IEC 13818-2 section 6.2.3.7 
	picture_data(m_bitstream_framenum);

	// write or display current or previously decoded reference frame 
	// ISO/IEC 13818-2 section 6.1.1.11: Frame reordering 
	frame_reorder(m_bitstream_framenum, m_sequence_framenum);

	if (picture_structure != FRAME_PICTURE)
		Second_Field = !Second_Field;
	}

void mpeg_video::frame_reorder(int bitstream_framenum, int sequence_framenum)
	{
	// tracking variables to insure proper output in spatial scalability 
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

void mpeg_video::write_frame(unsigned char *src[], int frame)
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

void mpeg_video::write_last_sequence_frame()
	{
	// put last frame
	if (m_sequence_framenum!=0)
		{
		//Output_Last_Frame_of_Sequence(m_bitstream_framenum);
		if (Second_Field)
			_tprintf(TEXT("last frame incomplete, not stored\n"));
		else
			write_frame(backward_reference_frame,m_bitstream_framenum-1);
		}
	}

void mpeg_video::get_display_info(display_info& di) const
	{
	di.horizontal_size = horizontal_size;
	di.vertical_size = vertical_size;
	di.chroma_format = chroma_format;
	di.coded_picture_width = Coded_Picture_Width;
	di.coded_picture_height = Coded_Picture_Height;
	di.mpeg2_flag = (m_pld->MPEG2_Flag != 0);
	di.progressive_frame = (progressive_frame != 0);
	di.matrix_coefficients = matrix_coefficients;
	}

double mpeg_video::get_frame_rate() const
	{
	return frame_rate_Table[frame_rate_code];
	}

double mpeg_video::get_bit_rate() const
	{
	return ((double) bit_rate_value) * 400.0;
	}

void mpeg_video::reset_state_variables()
	{
	/////////////
	// non-normative variables derived from normative elements
	Coded_Picture_Width = 0;
	Coded_Picture_Height = 0;
	Chroma_Width = 0;
	Chroma_Height = 0;
	block_count = 0;
	Second_Field = 0;
	profile = 0; 
	level = 0;

	/////////////
	// normative derived variables (as per ISO/IEC 13818-2)
	horizontal_size = 0;
	vertical_size = 0;
	mb_width = 0;
	mb_height = 0;
	bit_rate = 0.0;
	frame_rate = 0.0; 

	/////////////
	// headers 

	// ISO/IEC 13818-2 section 6.2.2.1:  sequence_header() 
	aspect_ratio_information = 0;
	frame_rate_code = 0; 
	bit_rate_value = 0; 
	vbv_buffer_size = 0;
	constrained_parameters_flag = 0;

	// ISO/IEC 13818-2 section 6.2.2.3:  sequence_extension() */
	profile_and_level_indication = 0;
	progressive_sequence = 0;
	chroma_format = 0;
	low_delay = 0;
	frame_rate_extension_n = 0;
	frame_rate_extension_d = 0;

	// ISO/IEC 13818-2 section 6.2.2.4:  sequence_display_extension()
	video_format = 0;  
	color_description = 0;
	color_primaries = 0;
	transfer_characteristics = 0;
	matrix_coefficients = 0;
	display_horizontal_size = 0;
	display_vertical_size = 0;

	// ISO/IEC 13818-2 section 6.2.3: picture_header() */
	temporal_reference = 0;
	picture_coding_type = 0;
	vbv_delay = 0;
	full_pel_forward_vector = 0;
	forward_f_code = 0;
	full_pel_backward_vector = 0;
	backward_f_code = 0;


	// ISO/IEC 13818-2 section 6.2.3.1: picture_coding_extension() header
	f_code[2][2];
	intra_dc_precision = 0;
	picture_structure = 0;
	top_field_first = 0;
	frame_pred_frame_dct = 0;
	concealment_motion_vectors = 0;

	intra_vlc_format = 0;

	repeat_first_field = 0;

	chroma_420_type = 0;
	progressive_frame = 0;
	composite_display_flag = 0;
	v_axis = 0;
	field_sequence = 0;
	sub_carrier = 0;
	burst_amplitude = 0;
	sub_carrier_phase = 0;


	// ISO/IEC 13818-2 section 6.2.2.6: group_of_pictures_header()
	drop_flag = 0;
	hour = 0;
	minute = 0;
	sec = 0;
	frame = 0;
	closed_gop = 0;
	broken_link = 0;

	// ISO/IEC 13818-2 section 6.2.3.3: picture_display_extension() header 
	frame_center_horizontal_offset[3];
	frame_center_vertical_offset[3];

	// ISO/IEC 13818-2 section 6.2.2.5: sequence_scalable_extension() header
	layer_id = 0;
	lower_layer_prediction_horizontal_size = 0;
	lower_layer_prediction_vertical_size = 0;
	horizontal_subsampling_factor_m = 0;
	horizontal_subsampling_factor_n = 0;
	vertical_subsampling_factor_m = 0;
	vertical_subsampling_factor_n = 0;

	// ISO/IEC 13818-2 section 6.2.3.5: picture_spatial_scalable_extension() header 
	lower_layer_temporal_reference = 0;
	lower_layer_horizontal_offset = 0;
	lower_layer_vertical_offset = 0;
	spatial_temporal_weight_code_table_index = 0;
	lower_layer_progressive_frame = 0;
	lower_layer_deinterlaced_field_select = 0;

	// ISO/IEC 13818-2 section 6.2.3.6: copyright_extension() header
	copyright_flag = 0;
	copyright_identifier = 0;
	original_or_copy = 0;
	copyright_number_1 = 0;
	copyright_number_2 = 0;
	copyright_number_3 = 0;

	//
	global_MBA;
	global_pic = 0;
	True_Framenum = 0;

	// pointers to generic picture buffers
	backward_reference_frame[0] = backward_reference_frame[1] = backward_reference_frame[2] = 0;
	forward_reference_frame[0] = forward_reference_frame[1] = forward_reference_frame[2] = 0;

	auxframe[0] = auxframe[1] = auxframe[2] = 0;
	current_frame[0] = current_frame[1] = current_frame[2] = 0;
	substitute_frame[0] = substitute_frame[1] = substitute_frame[2] = 0;


	// pointers to scalability picture buffers
	llframe0[0] = llframe0[1] = llframe0[2] = 0;
	llframe1[0] = llframe1[1] = llframe1[2] = 0;

	lltmp = NULL;
	Lower_Layer_Picture_Filename = NULL;

	Clip  = NULL;

	// decoder operation control flags
	Quiet_Flag = 0;
	Trace_Flag = 0;
	Fault_Flag = 0;
	Verbose_Flag = 0;
	Two_Streams = 0;
	Spatial_Flag = 0;
	Reference_IDCT_Flag = 0;
	Frame_Store_Flag = 0;
	System_Stream_Flag = 0;
	Display_Progressive_Flag = 0;
	Ersatz_Flag = 0;
	Big_Picture_Flag = 0;
	Verify_Flag = 0;
	Stats_Flag = 0;
	User_Data_Flag = 0;
	Main_Bitstream_Flag = 0;

	Temporal_Reference_Base = 0;
	True_Framenum_max = 0;
	Temporal_Reference_GOP_Reset = 0;

	// 
	True_Framenum_max = -1;
	}