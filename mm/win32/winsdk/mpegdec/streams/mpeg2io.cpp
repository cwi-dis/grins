#include "mpeg2io.h"

#include <string.h>

#include "mpeg2css.h"

mpeg2_fs_t* mpeg2_new_fs(TCHAR *path)
	{
	mpeg2_fs_t *fs = new mpeg2_fs_t;
	fs->css = mpeg2_new_css();
	_tcscpy(fs->path, path);
	return fs;
	}

int mpeg2_delete_fs(mpeg2_fs_t *fs)
	{
	mpeg2_delete_css(fs->css);
	delete fs;
	return 0;
	}

int mpeg2_copy_fs(mpeg2_fs_t *dst, mpeg2_fs_t *src)
	{
	_tcscpy(dst->path, src->path);
	dst->current_byte = 0;
	return 0;
	}

long mpeg2io_get_total_bytes(mpeg2_fs_t *fs)
	{	
	fs->total_bytes = fs->fd->get_total_bytes();
	return fs->total_bytes;
	}

int mpeg2io_open_file(mpeg2_fs_t *fs)
	{
	// Need to perform authentication before reading a single byte
	//mpeg2_get_keys(fs->css, fs->path);

	fs->fd = open_mpeg_input_stream(fs->path);
	
	if(fs->fd == NULL)
		{
		//perror("mpeg2io_open_file");
		return 1;
		}

	fs->total_bytes = mpeg2io_get_total_bytes(fs);
	
	if(!fs->total_bytes)
		{
		fs->fd->close();
		return 1;
		}
	fs->current_byte = 0;
	return 0;
	}

int mpeg2io_close_file(mpeg2_fs_t *fs)
	{
	if(fs != NULL && fs->fd != NULL) 
		{
		fs->fd->close();
		delete fs->fd;
		fs->fd = 0;
		}
	return 0;
	}


int mpeg2io_read_data(unsigned char *buffer, long bytes, mpeg2_fs_t *fs)
	{
	int result = !fs->fd->read(buffer, bytes);
	fs->current_byte += bytes;
	return (result && bytes);
	}

int mpeg2io_seek(mpeg2_fs_t *fs, long byte)
	{
	fs->current_byte = byte;
	if(fs->fd->seek(byte)) return 0;
	return 1;
	}

int mpeg2io_seek_relative(mpeg2_fs_t *fs, long bytes)
	{
	fs->current_byte += bytes;
	if(fs->fd->seek(fs->current_byte)) return 0;
	return 1;
	}

