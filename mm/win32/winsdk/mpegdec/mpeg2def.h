#ifndef INC_MPEG2DEF
#define INC_MPEG2DEF

#ifndef INC_MPEG2CON
#include "mpeg2con.h"
#endif

#ifndef _INC_TCHAR
#include <tchar.h>
#endif

struct mpeg2_block {
	unsigned char b[5];
	};

struct mpeg2_playkey {
	int offset;
	unsigned char key[5];
	};

struct mpeg2_css_t
	{
	int encrypted;
	char device_path[MPEG2_STRLEN];    // Device the file is located on
	unsigned char disk_key[MPEG2_DVD_PACKET_SIZE];
	unsigned char title_key[5];
	char challenge[10];
	struct mpeg2_block key1;
	struct mpeg2_block key2;
	struct mpeg2_block keycheck;
	int varient;
	int fd;
	char path[MPEG2_STRLEN];
	};

struct mpeg2_timecode_t
	{
	long hour;
	long minute;
	long second;
	long frame;
	};

// abstract input_stream 
class mpeg_input_stream;

// Filesystem structure
struct mpeg2_fs_t
	{
	mpeg_input_stream *fd;
	mpeg2_css_t *css;          // Encryption object
	TCHAR path[MPEG2_STRLEN];
	// Hypothetical position of file pointer
	long current_byte;
	long total_bytes;
	};

struct mpeg2demux_timecode_t
	{
	long start_byte;
	double start_time;
	double absolute_start_time;
	double absolute_end_time;
	long end_byte;
	double end_time;
	int program;
	};

struct mpeg2_title_t
	{
	void *file;
	mpeg2_fs_t *fs;
	long total_bytes;     // Total bytes in file.  Critical for seeking and length.
	mpeg2demux_timecode_t *timecode_table; // Timecode table
	long timecode_table_size;    // Number of entries
	long timecode_table_allocation;    // Number of available slots
	};

struct mpeg2_demuxer_t
	{
	void* file;
	
	// Data consisting of the multiplexed packet
	unsigned char *raw_data;
	long raw_offset;
	int raw_size;
	long packet_size;
	
	// Only one is on depending on which track owns the demultiplexer
	int do_audio;
	int do_video;

	// Data consisting of the elementary stream
	unsigned char *data_buffer;
	long data_size;
	long data_position;
	long data_allocated;
	// Remember when the file descriptor is at the beginning of the packet just read.
	int reverse;
	// Set to 1 when eof or attempt to read before beginning
	int error_flag;
	// Temp variables for returning
	unsigned char next_char;
	// Correction factor for time discontinuity
	double time_offset;
	int generating_timecode;

	// Titles
	mpeg2_title_t *titles[MPEG2_MAX_STREAMS];
	int total_titles;
	int current_title;

	// Tables of every stream ID encountered
	int astream_table[MPEG2_MAX_STREAMS];  // macro of audio format if audio
	int vstream_table[MPEG2_MAX_STREAMS];  // 1 if video 

	// Programs
	int total_programs;
	int current_program;

	// Timecode in the current title
	int current_timecode;

	// Byte position in the current title
	long current_byte;

	int transport_error_indicator;
	int payload_unit_start_indicator;
	int pid;
	int transport_scrambling_control;
	int adaptation_field_control;
	int continuity_counter;
	int is_padding;
	int pid_table[MPEG2_PIDMAX];
	int continuity_counters[MPEG2_PIDMAX];
	int total_pids;
	int adaptation_fields;
	double time;           // Time in seconds
	int audio_pid;
	int video_pid;
	int astream;     // Video stream ID being decoded.  -1 = select first ID in stream 
	int vstream;     // Audio stream ID being decoded.  -1 = select first ID in stream 
	int aformat;      // format of the audio derived from multiplexing codes 
	long program_association_tables;
	int table_id;
	int section_length;
	int transport_stream_id;
	long pes_packets;
	double pes_audio_time;  // Presentation Time stamps
	double pes_video_time;  // Presentation Time stamps
	};

struct mpeg2_bits_t
	{
	unsigned MPEG2_INT32 bfr;  // bfr = buffer for bits
	int bit_number;   // position of pointer in bfr
	int bfr_size;    // number of bits in bfr.  Should always be a multiple of 8
	void *file;    // Mpeg2 file
	mpeg2_demuxer_t *demuxer;   // Mpeg2 demuxer
	
	// If the input ptr is true, data is read from it instead of the demuxer
	unsigned char *input_ptr;
	};

struct mpeg2audio_t;

struct mpeg2_atrack_t
	{
	int channels;
	int sample_rate;
	mpeg2_demuxer_t *demuxer;
	mpeg2audio_t *audio;
	long current_position;
	long total_samples;
	};

struct mpeg2video_t;

struct mpeg2_vtrack_t
	{
	int width;
	int height;
	float frame_rate;
	mpeg2_demuxer_t *demuxer;
	mpeg2video_t *video;
	long current_position;  // Number of next frame to be played
	long total_frames;     // Total frames in the file
	};

struct mpeg2_t
	{
	mpeg2_fs_t *fs;      // Store entry path here
	mpeg2_demuxer_t *demuxer;        // Master tables

	// Media specific
	int has_audio;
	int has_video;
	int total_astreams;
	int total_vstreams;
	mpeg2_atrack_t *atrack[MPEG2_MAX_STREAMS];
	mpeg2_vtrack_t *vtrack[MPEG2_MAX_STREAMS];

	// Only one of these is set to 1 to specify what kind of stream we have
	int is_transport_stream;
	int is_program_stream;
	int is_audio_stream;         // Elemental stream
	int is_video_stream;         // Elemental stream 
	long packet_size;
	// Type and stream for getting current percentage 
	int last_type_read;  // 1 - audio   2 - video
	int last_stream_read;

	int program;  // Number of program to play
	int cpus;
	};


#endif