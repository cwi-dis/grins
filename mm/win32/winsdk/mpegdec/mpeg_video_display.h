#ifndef INC_MPEG_VIDEO_DISPLAY
#define INC_MPEG_VIDEO_DISPLAY

struct display_info
	{
	int horizontal_size, vertical_size;
	int chroma_format;
	int coded_picture_width, coded_picture_height;
	bool mpeg2_flag;
	bool progressive_frame;
	int matrix_coefficients;
	};

class mpeg_video_display
	{
	public:
	typedef unsigned char uchar_t;

	virtual ~mpeg_video_display() {}
	virtual void set_direct_update_box(int x, int y, int w, int h) = 0;
	virtual void update_surface(uchar_t *src[], int frame, int offset,int incr, int vsteps) = 0;
	virtual void lock() = 0;
	virtual void unlock() = 0;
	};

#endif // INC_MPEG_VIDEO_DISPLAY
