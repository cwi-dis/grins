#ifndef INC_MPEG_VIDEO
#define INC_MPEG_VIDEO

// layer specific variables (needed for SNR and DP scalability)
struct mpeg_layer_data 
	{
	// sequence header and quant_matrix_extension()
	int intra_quantizer_matrix[64];
	int non_intra_quantizer_matrix[64];
	int chroma_intra_quantizer_matrix[64];
	int chroma_non_intra_quantizer_matrix[64];
  
	int load_intra_quantizer_matrix;
	int load_non_intra_quantizer_matrix;
	int load_chroma_intra_quantizer_matrix;
	int load_chroma_non_intra_quantizer_matrix;

	int MPEG2_Flag;
	// sequence scalable extension
	int scalable_mode;
	// picture coding extension 
	int q_scale_type;
	int alternate_scan;
	// picture spatial scalable extension
	int pict_scal;
	// slice/macroblock
	int priority_breakpoint;
	int quantizer_scale;
	int intra_slice;
	short block[12][64];
	};

#ifndef INC_MPEG_VIDEO_DISPLAY
#include "mpeg_video_display.h"
#endif

class mpeg_video_bitstream;

class mpeg_video
	{
  public:
	typedef unsigned char uchar_t;

	mpeg_video(mpeg_video_bitstream *stream);
	~mpeg_video();

	// driver interface
	bool get_header();
	void initialize_sequence();
	void finalize_sequence();
	void reset_framenum();
	void update_framenum();
	void decode_picture();

	void get_display_info(display_info& di) const;
	double get_frame_rate() const;
	double get_bit_rate() const;
	int get_frames_size() const { return m_sequence_framenum+1;}

	void set_display(mpeg_video_display *display) { m_display = display;}
	void reset_state_variables();
	void write_last_sequence_frame();

	// headers
	void marker_bit(const char *text);
	int slice_header();

	// get picture
	void picture_data(int framenum);
	void update_picture_buffers();

	// get vlc
	int get_macroblock_type();
	int get_motion_code();
	int get_dmvector();
	int get_coded_block_pattern();
	int get_macroblock_address_increment();
	int get_luma_dc_dct_diff();
	int get_chroma_dc_dct_diff();

	// getblk
	void decode_mpeg1_intra_block (int comp, int dc_dct_pred[]);
	void decode_mpeg1_non_intra_block (int comp);
	void decode_mpeg2_intra_block (int comp, int dc_dct_pred[]);
	void decode_mpeg2_non_intra_block (int comp);

	// idct
	void fast_idct(short *block);
	void initialize_fast_idct();

	// motion
	void motion_vectors (int PMV[2][2][2], int dmvector[2],
		int motion_vertical_field_select[2][2], int s, int motion_vector_count, 
		int mv_format, int h_r_size, int v_r_size, int dmv, int mvscale);
	void motion_vector (int *PMV, int *dmvector,
		int h_r_size, int v_r_size, int dmv, int mvscale, int full_pel_vector);
	void dual_prime_arithmetic (int DMV[][2], int *dmvector, int mvx, int mvy);

	// recon
	void form_predictions (int bx, int by, int macroblock_type, 
		int motion_type, int PMV[2][2][2], int motion_vertical_field_select[2][2], 
		int dmvector[2], int stwtype);

	// spatscal
	void spatial_prediction();

  private:
	void error(const char *text);
	void write_frame(unsigned char *src[], int frame);
	void frame_reorder(int bitstream_framenum, int sequence_framenum);
	void update_surface(unsigned char *src[], int frame, int offset,int incr, int height);

	// headers
	void sequence_header();
	void group_of_pictures_header();
	void picture_header();
	void extension_and_user_data();

	int extra_bit_information();

	void sequence_extension();
	void sequence_display_extension();
	void quant_matrix_extension();
	void sequence_scalable_extension();
	void picture_display_extension();
	void picture_coding_extension();
    void picture_spatial_scalable_extension();
	void picture_temporal_scalable_extension();
    void copyright_extension();
	void user_data();
	
	// get picture
	void macroblock_modes (int *pmacroblock_type, int *pstwtype, int *pstwclass, 
		int *pmotion_type, int *pmotion_vector_count, int *pmv_format, int *pdmv,
		int *pmvscale, int *pdct_type);
	void clear_block (int comp);
	void sum_block(int comp);
	void saturate(short *bp);
	void add_block (int comp, int bx, int by, int dct_type, int addflag);
	//void frame_reorder (int bitstream_framenum, int sequence_framenum);
	void secode_snr_nacroblock (int *SNRMBA, int *SNRMBAinc, int MBA, int MBAmax, int *dct_type);
	void motion_compensation (int MBA, int macroblock_type, 
		int motion_type, int PMV[2][2][2], int motion_vertical_field_select[2][2], 
		int dmvector[2], int stwtype, int dct_type);
	void skipped_macroblock (int dc_dct_pred[3], int PMV[2][2][2], 
		int *motion_type, int motion_vertical_field_select[2][2],
		int *stwtype, int *macroblock_type);
	int slice(int framenum, int MBAmax);
	int start_of_slice (int MBAmax, int *MBA,
		int *MBAinc, int dc_dct_pred[3], int PMV[2][2][2]);
	int decode_macroblock (int *macroblock_type, 
		int *stwtype, int *stwclass, int *motion_type, int *dct_type,
		int PMV[2][2][2], int dc_dct_pred[3], 
		int motion_vertical_field_select[2][2], int dmvector[2]);

	// getvlc
	// generic picture macroblock type processing functions 
	int get_i_macroblock_type();
	int get_p_macroblock_type();
	int get_b_macroblock_type();
	int get_d_macroblock_type();
	// spatial picture macroblock type processing functions 
	int get_i_spatial_macroblock_type();
	int get_p_spatial_macroblock_type();
	int get_b_spatial_macroblock_type();
	int get_snr_macroblock_type();

	void read_lower_layer_component_framewise (int comp, int lw, int lh);
	void read_lower_layer_component_fieldwise (int comp, int lw, int lh);
	void make_spatial_prediction_frame (int progressive_frame,
		int llprogressive_frame, unsigned char *fld0, unsigned char *fld1, 
		short *tmp, unsigned char *dst, int llx0, int lly0, int llw, int llh, 
		int horizontal_size, int vertical_size, int vm, int vn, int hm, int hn, 
		int aperture);
	void deinterlace (unsigned char *fld0, unsigned char *fld1,
		int j0, int lx, int ly, int aperture);
	void subsample_vertical (unsigned char *s, short *d,
		int lx, int lys, int lyd, int m, int n, int j0, int dj);
	void subsample_horizontal (short *s, unsigned char *d,
		int x0, int lx, int lxs, int lxd, int ly, int m, int n);

  protected:
	/////////////
	mpeg_layer_data *m_pld;
	mpeg_video_bitstream *m_bitstream;
	mpeg_video_display *m_display;
	int m_bitstream_framenum;
	int m_sequence_framenum;	
	uchar_t *m_clip_ptr;
	static int s_refcount;

	/////////////
	// non-normative variables derived from normative elements
	int Coded_Picture_Width;
	int Coded_Picture_Height;
	int Chroma_Width;
	int Chroma_Height;
	int block_count;
	int Second_Field;
	int profile;
	int level;

	/////////////
	// normative derived variables (as per ISO/IEC 13818-2)
	int horizontal_size;
	int vertical_size;
	int mb_width;
	int mb_height;
	double bit_rate;
	double frame_rate; 

	/////////////
	// headers 

	// ISO/IEC 13818-2 section 6.2.2.1:  sequence_header() 
	int aspect_ratio_information;
	int frame_rate_code; 
	int bit_rate_value; 
	int vbv_buffer_size;
	int constrained_parameters_flag;

	// ISO/IEC 13818-2 section 6.2.2.3:  sequence_extension() */
	int profile_and_level_indication;
	int progressive_sequence;
	int chroma_format;
	int low_delay;
	int frame_rate_extension_n;
	int frame_rate_extension_d;

	// ISO/IEC 13818-2 section 6.2.2.4:  sequence_display_extension()
	int video_format;  
	int color_description;
	int color_primaries;
	int transfer_characteristics;
	int matrix_coefficients;
	int display_horizontal_size;
	int display_vertical_size;

	// ISO/IEC 13818-2 section 6.2.3: picture_header() */
	int temporal_reference;
	int picture_coding_type;
	int vbv_delay;
	int full_pel_forward_vector;
	int forward_f_code;
	int full_pel_backward_vector;
	int backward_f_code;


	// ISO/IEC 13818-2 section 6.2.3.1: picture_coding_extension() header
	int f_code[2][2];
	int intra_dc_precision;
	int picture_structure;
	int top_field_first;
	int frame_pred_frame_dct;
	int concealment_motion_vectors;

	int intra_vlc_format;

	int repeat_first_field;

	int chroma_420_type;
	int progressive_frame;
	int composite_display_flag;
	int v_axis;
	int field_sequence;
	int sub_carrier;
	int burst_amplitude;
	int sub_carrier_phase;


	// ISO/IEC 13818-2 section 6.2.2.6: group_of_pictures_header()
	int drop_flag;
	int hour;
	int minute;
	int sec;
	int frame;
	int closed_gop;
	int broken_link;

	// ISO/IEC 13818-2 section 6.2.3.3: picture_display_extension() header 
	int frame_center_horizontal_offset[3];
	int frame_center_vertical_offset[3];

	// ISO/IEC 13818-2 section 6.2.2.5: sequence_scalable_extension() header
	int layer_id;
	int lower_layer_prediction_horizontal_size;
	int lower_layer_prediction_vertical_size;
	int horizontal_subsampling_factor_m;
	int horizontal_subsampling_factor_n;
	int vertical_subsampling_factor_m;
	int vertical_subsampling_factor_n;

	// ISO/IEC 13818-2 section 6.2.3.5: picture_spatial_scalable_extension() header 
	int lower_layer_temporal_reference;
	int lower_layer_horizontal_offset;
	int lower_layer_vertical_offset;
	int spatial_temporal_weight_code_table_index;
	int lower_layer_progressive_frame;
	int lower_layer_deinterlaced_field_select;

	// ISO/IEC 13818-2 section 6.2.3.6: copyright_extension() header
	int copyright_flag;
	int copyright_identifier;
	int original_or_copy;
	int copyright_number_1;
	int copyright_number_2;
	int copyright_number_3;

	//
	int global_MBA;
	int global_pic;
	int True_Framenum;

	// pointers to generic picture buffers
	unsigned char *backward_reference_frame[3];
	unsigned char *forward_reference_frame[3];

	unsigned char *auxframe[3];
	unsigned char *current_frame[3];
	unsigned char *substitute_frame[3];


	// pointers to scalability picture buffers
	unsigned char *llframe0[3];
	unsigned char *llframe1[3];

	short *lltmp;
	char *Lower_Layer_Picture_Filename;

	// decoder operation control flags
	int Quiet_Flag;
	int Trace_Flag;
	int Fault_Flag;
	int Verbose_Flag;
	int Two_Streams;
	int Spatial_Flag;
	int Reference_IDCT_Flag;
	int Frame_Store_Flag;
	int System_Stream_Flag;
	int Display_Progressive_Flag;
	int Ersatz_Flag;
	int Big_Picture_Flag;
	int Verify_Flag;
	int Stats_Flag;
	int User_Data_Flag;
	int Main_Bitstream_Flag;
  private:
	// introduced in September 1995 to assist spatial scalable decoding
	void Update_Temporal_Reference_Tacking_Data();

	// private variables
	int Temporal_Reference_Base;
	int True_Framenum_max;
	int Temporal_Reference_GOP_Reset;

	};

// const table used by display and mpeg_video
extern unsigned char *Clip;

#endif // INC_MPEG_VIDEO
