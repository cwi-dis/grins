#ifndef INC_MPEG2DEMUX
#define INC_MPEG2DEMUX

#ifndef INC_MPEG2DEF
#include "mpeg2def.h"
#endif

int mpeg2demux_seek_byte(mpeg2_demuxer_t *demuxer, long byte);
long mpeg2demuxer_total_bytes(mpeg2_demuxer_t *demuxer);
int mpeg2demux_seek_time(mpeg2_demuxer_t *demuxer, double new_time);
int mpeg2demux_seek_percentage(mpeg2_demuxer_t *demuxer, double percentage);
unsigned int mpeg2demux_read_char_packet(mpeg2_demuxer_t *demuxer);
unsigned int mpeg2demux_read_prev_char_packet(mpeg2_demuxer_t *demuxer);
int mpeg2demux_read_data(mpeg2_demuxer_t *demuxer, 
		unsigned char *output, 
		long size);
int mpeg2demux_open_title(mpeg2_demuxer_t *demuxer, int title_number);
int mpeg2demux_copy_titles(mpeg2_demuxer_t *dst, mpeg2_demuxer_t *src);
int mpeg2demux_bof(mpeg2_demuxer_t *demuxer);
int mpeg2demux_eof(mpeg2_demuxer_t *demuxer);
long mpeg2demux_tell(mpeg2_demuxer_t *demuxer);
mpeg2_demuxer_t* mpeg2_new_demuxer(mpeg2_t *file, int do_audio, int do_video, int stream_id);
int mpeg2_delete_demuxer(mpeg2_demuxer_t *demuxer);
int mpeg2demux_read_titles(mpeg2_demuxer_t *demuxer);
int mpeg2demux_create_title(mpeg2_demuxer_t *demuxer, int timecode_search, FILE *toc);
double mpeg2demux_length(mpeg2_demuxer_t *demuxer);
double mpeg2demux_tell_percentage(mpeg2_demuxer_t *demuxer);

#define mpeg2demux_error(demuxer) (((mpeg2_demuxer_t *)(demuxer))->error_flag)

#define mpeg2demux_time_offset(demuxer) (((mpeg2_demuxer_t *)(demuxer))->time_offset)

#define mpeg2demux_current_time(demuxer) (((mpeg2_demuxer_t *)(demuxer))->time + ((mpeg2_demuxer_t *)(demuxer))->time_offset)

#define mpeg2demux_read_char(demuxer) \
    ((((mpeg2_demuxer_t *)(demuxer))->data_position < ((mpeg2_demuxer_t *)(demuxer))->data_size) ? \
    ((mpeg2_demuxer_t *)(demuxer))->data_buffer[((mpeg2_demuxer_t *)(demuxer))->data_position++] : \
    mpeg2demux_read_char_packet(demuxer))

#define mpeg2demux_read_prev_char(demuxer) \
    ((((mpeg2_demuxer_t *)(demuxer))->data_position != 0) ? \
    ((mpeg2_demuxer_t *)(demuxer))->data_buffer[((mpeg2_demuxer_t *)(demuxer))->data_position--] : \
    mpeg2demux_read_prev_char_packet(demuxer))


#endif // INC_MPEG2DEMUX