#ifndef MPEG2IO_H
#define MPEG2IO_H

#ifndef INC_MPEG2DEF
#include "mpeg2def.h"
#endif

#ifndef INC_MPEG_INPUT_STREAM
#include "mpeg_input_stream.h"
#endif

int mpeg2io_seek_relative(mpeg2_fs_t *fs, long bytes);
int mpeg2io_seek(mpeg2_fs_t *fs, long byte);
int mpeg2_copy_fs(mpeg2_fs_t *dst, mpeg2_fs_t *src);

mpeg2_fs_t* mpeg2_new_fs(TCHAR *path);
int mpeg2_delete_fs(mpeg2_fs_t *fs);
int mpeg2io_open_file(mpeg2_fs_t *fs);
int mpeg2io_close_file(mpeg2_fs_t *fs);
int mpeg2io_read_data(unsigned char *buffer, long bytes, mpeg2_fs_t *fs);

#define mpeg2io_tell(fs) (((mpeg2_fs_t *)(fs))->current_byte)

// End of file
#define mpeg2io_eof(fs) (((mpeg2_fs_t *)(fs))->current_byte >= ((mpeg2_fs_t *)(fs))->total_bytes)

// Beginning of file
#define mpeg2io_bof(fs)	(((mpeg2_fs_t *)(fs))->current_byte < 0)


#define mpeg2io_total_bytes(fs) (((mpeg2_fs_t *)(fs))->total_bytes)

inline unsigned int mpeg2io_read_int32(mpeg2_fs_t *fs)
	{
	int a = (unsigned char)fs->fd->read_char();
	int b = (unsigned char)fs->fd->read_char();
	int c = (unsigned char)fs->fd->read_char();
	int d = (unsigned char)fs->fd->read_char();
	unsigned int result = ((int)a << 24) |
					((int)b << 16) |
					((int)c << 8) |
					((int)d);
	fs->current_byte += 4;
	return result;
	}

inline unsigned int mpeg2io_read_char(mpeg2_fs_t *fs)
	{
	fs->current_byte++;
	return fs->fd->read_char();
	}

#endif
