
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#ifndef INC_MPEGDECODER
#define INC_MPEGDECODER

struct layer_data;
struct display_info;
class MpegDisplay;


class MpegDecoder
	{
	public:
	MpegDecoder();

	~MpegDecoder();

	bool check(int handle);
	bool check_mpeg();
	int detach_file_handle();

	bool parse_picture_header();
	void decode_picture();

	void initialize_sequence();
	void finalize_sequence();

	void reset_framenum();
	void update_framenum();

	void write_last_sequence_frame();

	void set_display(MpegDisplay *display) { m_display = display;}
	void get_display_info(display_info& di) const;
	double get_frame_rate() const;
	double get_bit_rate() const;
	int get_bitstream_framenum() const { return m_bitstream_framenum;}
	int get_sequence_framenum() const { return m_sequence_framenum;}
	
	private:
	void write_frame(unsigned char *src[], int frame);
	void frame_reorder(int bitstream_framenum, int sequence_framenum);
	void update_surface(unsigned char *src[], int frame, int offset,int incr, int height);

	int m_bitstream_framenum;
	int m_sequence_framenum;	
	layer_data *m_base_layer;
	layer_data *m_enhan_layer;
	MpegDisplay *m_display;
	};


#endif // INC_MPEGDECODER