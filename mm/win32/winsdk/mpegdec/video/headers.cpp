#include "headers.h"

#include "streams/bitstream.h"
#include "seek.h"

int mpeg2video_getseqhdr(mpeg2video_t *video)
	{
	int i;
	mpeg2_t *file = (mpeg2_t *)video->file;

	int aspect_ratio,  vbv_buffer_size;
	//int picture_rate;
	int constrained_parameters_flag;
	int load_intra_quantizer_matrix, load_non_intra_quantizer_matrix;

	video->horizontal_size = mpeg2bits_getbits(video->vstream, 12);
	video->vertical_size = mpeg2bits_getbits(video->vstream, 12);
	aspect_ratio = mpeg2bits_getbits(video->vstream, 4);
	video->framerate_code = mpeg2bits_getbits(video->vstream, 4);
	video->bitrate = mpeg2bits_getbits(video->vstream, 18);
	mpeg2bits_getbit_noptr(video->vstream); /* marker bit (=1) */
	vbv_buffer_size = mpeg2bits_getbits(video->vstream, 10);
	constrained_parameters_flag = mpeg2bits_getbit_noptr(video->vstream);
	video->frame_rate = (float)mpeg2_frame_rate_table[video->framerate_code];

 	load_intra_quantizer_matrix = mpeg2bits_getbit_noptr(video->vstream);
 	if(load_intra_quantizer_matrix)
		{
    	for(i = 0; i < 64; i++)
      		video->intra_quantizer_matrix[video->mpeg2_zigzag_scan_table[i]] = mpeg2bits_getbyte_noptr(video->vstream);
  		}
  	else 
		{
    	for(i = 0; i < 64; i++)
      		video->intra_quantizer_matrix[i] = mpeg2_default_intra_quantizer_matrix[i];
		}

	load_non_intra_quantizer_matrix = mpeg2bits_getbit_noptr(video->vstream);
	if(load_non_intra_quantizer_matrix)
		{
    	for(i = 0; i < 64; i++)
      		video->non_intra_quantizer_matrix[video->mpeg2_zigzag_scan_table[i]] = mpeg2bits_getbyte_noptr(video->vstream);
  		}
  	else 
		{
    	for(i = 0; i < 64; i++)
      		video->non_intra_quantizer_matrix[i] = 16;
  		}

	// copy luminance to chrominance matrices
  	for(i = 0; i < 64; i++)
		{
    	video->chroma_intra_quantizer_matrix[i] = video->intra_quantizer_matrix[i];
   	 	video->chroma_non_intra_quantizer_matrix[i] = video->non_intra_quantizer_matrix[i];
  		}

	return 0;
	}


// decode sequence extension
int mpeg2video_sequence_extension(mpeg2video_t *video)
	{
	int prof_lev;
	int horizontal_size_extension, vertical_size_extension;
	int bit_rate_extension, vbv_buffer_size_extension, low_delay;
	int frame_rate_extension_n, frame_rate_extension_d;
	int pos = 0;

	video->mpeg2 = 1;
	video->scalable_mode = SC_NONE; // unless overwritten by seq. scal. ext.
	prof_lev = mpeg2bits_getbyte_noptr(video->vstream);
	video->prog_seq = mpeg2bits_getbit_noptr(video->vstream);
	video->chroma_format = mpeg2bits_getbits(video->vstream, 2);
	horizontal_size_extension = mpeg2bits_getbits(video->vstream, 2);
	vertical_size_extension = mpeg2bits_getbits(video->vstream, 2);
	bit_rate_extension = mpeg2bits_getbits(video->vstream, 12);
	mpeg2bits_getbit_noptr(video->vstream);
	vbv_buffer_size_extension = mpeg2bits_getbyte_noptr(video->vstream);
	low_delay = mpeg2bits_getbit_noptr(video->vstream);
	frame_rate_extension_n = mpeg2bits_getbits(video->vstream, 2);
	frame_rate_extension_d = mpeg2bits_getbits(video->vstream, 5);
	video->horizontal_size = (horizontal_size_extension << 12) | (video->horizontal_size & 0x0fff);
	video->vertical_size = (vertical_size_extension << 12) | (video->vertical_size & 0x0fff);
	return 0; // na
	}


// decode sequence display extension
int mpeg2video_sequence_display_extension(mpeg2video_t *video)
	{
	int colour_primaries = 0, transfer_characteristics = 0;
	int display_horizontal_size, display_vertical_size;
	int pos = 0;
	int video_format = mpeg2bits_getbits(video->vstream, 3);
	int colour_description = mpeg2bits_getbit_noptr(video->vstream);

	if(colour_description)
		{
    	colour_primaries = mpeg2bits_getbyte_noptr(video->vstream);
    	transfer_characteristics = mpeg2bits_getbyte_noptr(video->vstream);
    	video->matrix_coefficients = mpeg2bits_getbyte_noptr(video->vstream);
		}

	display_horizontal_size = mpeg2bits_getbits(video->vstream, 14);
	mpeg2bits_getbit_noptr(video->vstream);
	display_vertical_size = mpeg2bits_getbits(video->vstream, 14);
	return 0; // na
	}


// decode quant matrix entension
int mpeg2video_quant_matrix_extension(mpeg2video_t *video)
	{
	int i;
	int load_intra_quantiser_matrix, load_non_intra_quantiser_matrix;
	int load_chroma_intra_quantiser_matrix;
	int load_chroma_non_intra_quantiser_matrix;
	int pos = 0;

	if((load_intra_quantiser_matrix = mpeg2bits_getbit_noptr(video->vstream)) != 0)
		{
      	for(i = 0; i < 64; i++)
			{
    		video->chroma_intra_quantizer_matrix[video->mpeg2_zigzag_scan_table[i]]
    			= video->intra_quantizer_matrix[video->mpeg2_zigzag_scan_table[i]]
    			= mpeg2bits_getbyte_noptr(video->vstream);
      		}
		}

	if((load_non_intra_quantiser_matrix = mpeg2bits_getbit_noptr(video->vstream)) != 0)
		{
    	for (i = 0; i < 64; i++)
			{
    		video->chroma_non_intra_quantizer_matrix[video->mpeg2_zigzag_scan_table[i]]
    			= video->non_intra_quantizer_matrix[video->mpeg2_zigzag_scan_table[i]]
    			= mpeg2bits_getbyte_noptr(video->vstream);
    		}
		}

	if((load_chroma_intra_quantiser_matrix = mpeg2bits_getbit_noptr(video->vstream)) != 0)
		{
    	for(i = 0; i < 64; i++)
    		video->chroma_intra_quantizer_matrix[video->mpeg2_zigzag_scan_table[i]] = mpeg2bits_getbyte_noptr(video->vstream);
		}

	if((load_chroma_non_intra_quantiser_matrix = mpeg2bits_getbit_noptr(video->vstream)) != 0)
		{
      	for(i = 0; i < 64; i++)
    		video->chroma_non_intra_quantizer_matrix[video->mpeg2_zigzag_scan_table[i]] = mpeg2bits_getbyte_noptr(video->vstream);
		}
	return 0; // na
	}


// decode sequence scalable extension
int mpeg2video_sequence_scalable_extension(mpeg2video_t *video)
	{
	int layer_id;

	video->scalable_mode = mpeg2bits_getbits(video->vstream, 2) + 1; // add 1 to make SC_DP != SC_NONE 
	layer_id = mpeg2bits_getbits(video->vstream, 4);

	if(video->scalable_mode == SC_SPAT)
		{
    	video->llw = mpeg2bits_getbits(video->vstream, 14); // lower_layer_prediction_horizontal_size 
    	mpeg2bits_getbit_noptr(video->vstream);
    	video->llh = mpeg2bits_getbits(video->vstream, 14); // lower_layer_prediction_vertical_size 
    	video->hm = mpeg2bits_getbits(video->vstream, 5);
    	video->hn = mpeg2bits_getbits(video->vstream, 5);
    	video->vm = mpeg2bits_getbits(video->vstream, 5);
    	video->vn = mpeg2bits_getbits(video->vstream, 5);
		}

	if(video->scalable_mode == SC_TEMP)
      	_tprintf(TEXT("mpeg2video_sequence_scalable_extension: temporal scalability not implemented\n"));
	return 0; // na
	}


// decode picture display extension
int mpeg2video_picture_display_extension(mpeg2video_t *video)
	{
	int n, i;
	short frame_centre_horizontal_offset[3];
	short frame_centre_vertical_offset[3];

	if(video->prog_seq || video->pict_struct != FRAME_PICTURE)
		n = 1;
	else 
		n = video->repeatfirst ? 3 : 2;

	for(i = 0; i < n; i++)
		{
    	frame_centre_horizontal_offset[i] = (short)mpeg2bits_getbits(video->vstream, 16);
    	mpeg2bits_getbit_noptr(video->vstream);
    	frame_centre_vertical_offset[i] = (short)mpeg2bits_getbits(video->vstream, 16);
    	mpeg2bits_getbit_noptr(video->vstream);
		}
	return 0; // na
	}


// decode picture coding extension
int mpeg2video_picture_coding_extension(mpeg2video_t *video)
	{
	int chroma_420_type, composite_display_flag;
	int v_axis = 0, field_sequence = 0, sub_carrier = 0, burst_amplitude = 0, sub_carrier_phase = 0;

	video->h_forw_r_size = mpeg2bits_getbits(video->vstream, 4) - 1;
	video->v_forw_r_size = mpeg2bits_getbits(video->vstream, 4) - 1;
	video->h_back_r_size = mpeg2bits_getbits(video->vstream, 4) - 1;
	video->v_back_r_size = mpeg2bits_getbits(video->vstream, 4) - 1;
	video->dc_prec = mpeg2bits_getbits(video->vstream, 2);
	video->pict_struct = mpeg2bits_getbits(video->vstream, 2);
	video->topfirst = mpeg2bits_getbit_noptr(video->vstream);
	video->frame_pred_dct = mpeg2bits_getbit_noptr(video->vstream);
	video->conceal_mv = mpeg2bits_getbit_noptr(video->vstream);
	video->qscale_type = mpeg2bits_getbit_noptr(video->vstream);
	video->intravlc = mpeg2bits_getbit_noptr(video->vstream);
	video->altscan = mpeg2bits_getbit_noptr(video->vstream);
	video->repeatfirst = mpeg2bits_getbit_noptr(video->vstream);
	chroma_420_type = mpeg2bits_getbit_noptr(video->vstream);
	video->prog_frame = mpeg2bits_getbit_noptr(video->vstream);

	if(video->repeat_count > 100)
		video->repeat_count = 0;
	video->repeat_count += 100;

	video->current_repeat = 0;

	if(video->prog_seq)
		{
		if(video->repeatfirst)
			{
			if(video->topfirst)
				video->repeat_count += 200;
			else
				video->repeat_count += 100;
			}
		}
	else if(video->prog_frame)
		{
		if(video->repeatfirst)
			{
			video->repeat_count += 50;
			}
		}

	// printf("mpeg2video_picture_coding_extension %d\n", video->repeat_count);
	composite_display_flag = mpeg2bits_getbit_noptr(video->vstream);

	if(composite_display_flag)
		{
    	v_axis = mpeg2bits_getbit_noptr(video->vstream);
    	field_sequence = mpeg2bits_getbits(video->vstream, 3);
    	sub_carrier = mpeg2bits_getbit_noptr(video->vstream);
    	burst_amplitude = mpeg2bits_getbits(video->vstream, 7);
    	sub_carrier_phase = mpeg2bits_getbyte_noptr(video->vstream);
		}
	return 0; // na
	}


// decode picture spatial scalable extension
int mpeg2video_picture_spatial_scalable_extension(mpeg2video_t *video)
	{
	video->pict_scal = 1; // use spatial scalability in this picture

	video->lltempref = mpeg2bits_getbits(video->vstream, 10);
	mpeg2bits_getbit_noptr(video->vstream);
	video->llx0 = mpeg2bits_getbits(video->vstream, 15);
	if(video->llx0 >= 16384) video->llx0 -= 32768;
	mpeg2bits_getbit_noptr(video->vstream);
	video->lly0 = mpeg2bits_getbits(video->vstream, 15);
	if(video->lly0 >= 16384) video->lly0 -= 32768;
	video->stwc_table_index = mpeg2bits_getbits(video->vstream, 2);
	video->llprog_frame = mpeg2bits_getbit_noptr(video->vstream);
	video->llfieldsel = mpeg2bits_getbit_noptr(video->vstream);
	return 0; // na
	}


// decode picture temporal scalable extension
// not implemented
int mpeg2video_picture_temporal_scalable_extension(mpeg2video_t *video)
	{
  	return _tprintf(TEXT("mpeg2video_picture_temporal_scalable_extension: temporal scalability not supported\n"));
	}


// decode extension and user data

int mpeg2video_ext_user_data(mpeg2video_t *video)
	{
  	int code = mpeg2bits_next_startcode(video->vstream);


  	while(code == MPEG2_EXT_START_CODE || code == MPEG2_USER_START_CODE && !mpeg2bits_eof(video->vstream))
		{
    	mpeg2bits_refill(video->vstream);
		
    	if(code == MPEG2_EXT_START_CODE)
			{
      		int ext_id = mpeg2bits_getbits(video->vstream, 4);
      		switch(ext_id)
				{
    			case SEQ_ID:
					mpeg2video_sequence_extension(video);
					break;
    			case DISP_ID:
					mpeg2video_sequence_display_extension(video);
					break;
    			case QUANT_ID:
					mpeg2video_quant_matrix_extension(video);
					break;
    			case SEQSCAL_ID:
					mpeg2video_sequence_scalable_extension(video);
					break;
    			case PANSCAN_ID:
					mpeg2video_picture_display_extension(video);
					break;
    			case CODING_ID:
					mpeg2video_picture_coding_extension(video);
					break;
    			case SPATSCAL_ID:
					mpeg2video_picture_spatial_scalable_extension(video);
					break;
    			case TEMPSCAL_ID:
					mpeg2video_picture_temporal_scalable_extension(video);
					break;
    			default:
					_tprintf(TEXT("mpeg2video_ext_user_data: reserved extension start code ID %d\n"), ext_id);
					break;
      			}
   			}
   		code = mpeg2bits_next_startcode(video->vstream);
  		}
	return 0; // na
	}


// decode group of pictures header
int mpeg2video_getgophdr(mpeg2video_t *video, int dont_repeat)
	{
	int drop_flag, closed_gop, broken_link;

	drop_flag = mpeg2bits_getbit_noptr(video->vstream);
	video->gop_timecode.hour = mpeg2bits_getbits(video->vstream, 5);
	video->gop_timecode.minute = mpeg2bits_getbits(video->vstream, 6);
	mpeg2bits_getbit_noptr(video->vstream);
	video->gop_timecode.second = mpeg2bits_getbits(video->vstream, 6);
	video->gop_timecode.frame = mpeg2bits_getbits(video->vstream, 6);
	closed_gop = mpeg2bits_getbit_noptr(video->vstream);
	broken_link = mpeg2bits_getbit_noptr(video->vstream);

	// printf("%d:%d:%d:%d %d %d %d\n", video->gop_timecode.hour, video->gop_timecode.minute, video->gop_timecode.second, video->gop_timecode.frame, 
	//  	drop_flag, closed_gop, broken_link);
	return mpeg2bits_error(video->vstream);
	}

// decode picture header
int mpeg2video_getpicturehdr(mpeg2video_t *video)
	{
	int temp_ref, vbv_delay;

	video->pict_scal = 0; /* unless overwritten by pict. spat. scal. ext. */

	temp_ref = mpeg2bits_getbits(video->vstream, 10);
	video->pict_type = mpeg2bits_getbits(video->vstream, 3);
	vbv_delay = mpeg2bits_getbits(video->vstream, 16);

	if(video->pict_type == P_TYPE || video->pict_type == B_TYPE)
		{
    	video->full_forw = mpeg2bits_getbit_noptr(video->vstream);
    	video->forw_r_size = mpeg2bits_getbits(video->vstream, 3) - 1;
		}

	if(video->pict_type == B_TYPE)
		{
    	video->full_back = mpeg2bits_getbit_noptr(video->vstream);
    	video->back_r_size = mpeg2bits_getbits(video->vstream, 3) - 1;
		}

	// get extra bit picture
	while(mpeg2bits_getbit_noptr(video->vstream) &&
		!mpeg2bits_eof(video->vstream)) mpeg2bits_getbyte_noptr(video->vstream);
	return 0;
	}


int mpeg2video_get_header(mpeg2video_t *video, int dont_repeat)
	{
	unsigned int code;

	// a sequence header should be found before returning from `getheader' the
	// first time (this is to set horizontal/vertical size properly)

	// Repeat the frame until it's less than 1 count from repeat_count 
	if(video->repeat_count - video->current_repeat >= 100 && !dont_repeat)
		{
		return 0;
		}

	if(dont_repeat)
		{
		video->repeat_count = 0;
		video->current_repeat = 0;
		}
	else
		video->repeat_count -= video->current_repeat;

	while(1)
		{
		// look for startcode
    	code = mpeg2bits_next_startcode(video->vstream);
		if(mpeg2bits_eof(video->vstream)) return 1;
		if(code != MPEG2_SEQUENCE_END_CODE) mpeg2bits_refill(video->vstream);
    	switch(code)
			{
    		case MPEG2_SEQUENCE_START_CODE:
    			video->found_seqhdr = 1;
    			mpeg2video_getseqhdr(video);  
    			mpeg2video_ext_user_data(video);
    			break;

    		case MPEG2_GOP_START_CODE:
    			mpeg2video_getgophdr(video);
    			mpeg2video_ext_user_data(video);
    			break;

    		case MPEG2_PICTURE_START_CODE:
    			mpeg2video_getpicturehdr(video);
    			mpeg2video_ext_user_data(video);
    			if(video->found_seqhdr) return 0;       /* Exit here */
    			break;

    		case MPEG2_SEQUENCE_END_CODE:
				// Continue until the end
				mpeg2bits_refill(video->vstream);
				break;

    		default:
    			break;
    		}
  		}
 	return 1;      // Shouldn't be reached.
	}

int mpeg2video_ext_bit_info(mpeg2_slice_buffer_t *slice_buffer)
	{
	while(mpeg2slice_getbit(slice_buffer)) mpeg2slice_getbyte(slice_buffer);
	return 0;
	}

// decode slice header
int mpeg2video_getslicehdr(mpeg2_slice_t *slice, mpeg2video_t *video)
	{
	int slice_vertical_position_extension, intra_slice;
	int qs;

  	slice_vertical_position_extension = (video->mpeg2 && video->vertical_size > 2800) ? 
		mpeg2slice_getbits(slice->slice_buffer, 3) : 0;

  	if(video->scalable_mode == SC_DP) slice->pri_brk = mpeg2slice_getbits(slice->slice_buffer, 7);

  	qs = mpeg2slice_getbits(slice->slice_buffer, 5);
  	slice->quant_scale = video->mpeg2 ? (video->qscale_type ? mpeg2_non_linear_mquant_table[qs] : (qs << 1)) : qs;

  	if(mpeg2slice_getbit(slice->slice_buffer))
		{
    	intra_slice = mpeg2slice_getbit(slice->slice_buffer);
    	mpeg2slice_getbits(slice->slice_buffer, 7);
    	mpeg2video_ext_bit_info(slice->slice_buffer);
  		}
  	else 
		intra_slice = 0;

	return slice_vertical_position_extension;
	}
