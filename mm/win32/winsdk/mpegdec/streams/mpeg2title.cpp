#include "mpeg2title.h"

#include <stdlib.h>

#include "mpeg2io.h"

mpeg2_title_t* mpeg2_new_title(mpeg2_t *file, TCHAR *path)
	{
	mpeg2_title_t *title = (mpeg2_title_t *)calloc(1, sizeof(mpeg2_title_t));
	title->fs = mpeg2_new_fs(path);
	title->file = file;
	return title;
	}

int mpeg2_delete_title(mpeg2_title_t *title)
	{
	mpeg2_delete_fs(title->fs);
	if(title->timecode_table_size)
		{
		free(title->timecode_table);
		}
	free(title);
	return 0;
	}

int mpeg2_copy_title(mpeg2_title_t *dst, mpeg2_title_t *src)
	{
	int i;

	mpeg2_copy_fs(dst->fs, src->fs);
	dst->total_bytes = src->total_bytes;
	
	if(src->timecode_table_size)
		{
		dst->timecode_table_allocation = src->timecode_table_allocation;
		dst->timecode_table_size = src->timecode_table_size;
		dst->timecode_table = (mpeg2demux_timecode_t*)calloc(1, sizeof(mpeg2demux_timecode_t) * dst->timecode_table_allocation);

		for(i = 0; i < dst->timecode_table_size; i++)
			{
			dst->timecode_table[i] = src->timecode_table[i];
			}
		}
	return 1;
	}

int mpeg2_dump_title(mpeg2_title_t *title)
	{
	for(int i = 0;i < title->timecode_table_size; i++)
		{
		_tprintf(TEXT("%f: %d - %d %f %f %d\n"), 
			title->timecode_table[i].absolute_start_time, 
			title->timecode_table[i].start_byte, 
			title->timecode_table[i].end_byte, 
			title->timecode_table[i].start_time, 
			title->timecode_table[i].end_time, 
			title->timecode_table[i].program);
		}
	return 1;
	}
