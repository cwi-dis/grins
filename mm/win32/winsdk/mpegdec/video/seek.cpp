#include "seek.h"

#include "streams/bitstream.h"

#include "headers.h"

#include <string.h>
#include <math.h>

// Line up on the beginning of the next code.
int mpeg2video_next_code(mpeg2_bits_t* stream, unsigned int code)
	{
	while(!mpeg2bits_eof(stream) && mpeg2bits_showbits32_noptr(stream) != code)
		{
		mpeg2bits_getbyte_noptr(stream);
		}
	return mpeg2bits_eof(stream);
	}

// Line up on the beginning of the previous code.
int mpeg2video_prev_code(mpeg2_bits_t* stream, unsigned int code)
	{
	while(!mpeg2bits_bof(stream) && mpeg2bits_showbits_reverse(stream, 32) != code)
		{
		mpeg2bits_getbits_reverse(stream, 8);
		}
	return mpeg2bits_bof(stream);
	}

long mpeg2video_goptimecode_to_frame(mpeg2video_t *video)
	{
	//  printf("mpeg2video_goptimecode_to_frame %d %d %d %d %f\n",  */
	// 	video->gop_timecode.hour, video->gop_timecode.minute, video->gop_timecode.second, video->gop_timecode.frame, video->frame_rate); */
	return (long)(video->gop_timecode.hour * 3600 * video->frame_rate + 
		video->gop_timecode.minute * 60 * video->frame_rate +
		video->gop_timecode.second * video->frame_rate +
		video->gop_timecode.frame) - 1 - video->first_frame;
	}

int mpeg2video_match_refframes(mpeg2video_t *video)
	{
	for(int i = 0; i < 3; i++)
		{
		if(video->newframe[i])
			{
			unsigned char *dst, *src;
			if(video->newframe[i] == video->refframe[i])
				{
				src = video->refframe[i];
				dst = video->oldrefframe[i];
				}
			else
				{
				src = video->oldrefframe[i];
				dst = video->refframe[i];
				}
			int size;
    		if(i == 0)
				size = video->coded_picture_width * video->coded_picture_height + 32 * video->coded_picture_width;
    		else 
				size = video->chrom_width * video->chrom_height + 32 * video->chrom_width;
			memcpy(dst, src, size);
			}
		}
	return 0;
	}

int mpeg2video_seek(mpeg2video_t *video)
	{
	long this_gop_start;
	int result = 0;
	//int back_step;
	//int attempts;
	mpeg2_t *file = (mpeg2_t *)video->file;
	mpeg2_bits_t *vstream = video->vstream;
	double percentage;
	long frame_number;
	int match_refframes = 1;

	// Seek to a percentage 
	if(video->percentage_seek >= 0)
		{
		percentage = video->percentage_seek;
		video->percentage_seek = -1;
		mpeg2bits_seek_percentage(vstream, percentage);
		// Go to previous I-frame
		mpeg2bits_start_reverse(vstream);
		result = mpeg2video_prev_code(vstream, MPEG2_GOP_START_CODE);
		if(!result) mpeg2bits_getbits_reverse(vstream, 32);
		mpeg2bits_start_forward(vstream);

		if(mpeg2bits_tell_percentage(vstream) < 0) mpeg2bits_seek_percentage(vstream, 0);

		// Read up to the correct percentage
		result = 0;
		while(!result && mpeg2bits_tell_percentage(vstream) < percentage)
			{
			result = mpeg2video_read_frame_backend(video, 0);
			if(match_refframes)
				mpeg2video_match_refframes(video);
			match_refframes = 0;
			}
		}
	else if(video->frame_seek >= 0)
		{
		// Seek to a frame
		frame_number = video->frame_seek;
		video->frame_seek = -1;
		if(frame_number < 0) frame_number = 0;
		if(frame_number > video->maxframe) frame_number = video->maxframe;

		// Seek to start of file
		if(frame_number < 16)
			{
			video->repeat_count = video->current_repeat = 0;
			mpeg2bits_seek_start(vstream);
			video->framenum = 0;
			result = mpeg2video_drop_frames(video, frame_number - video->framenum);
			}
		else
			{
			// Seek to an I frame.
			if((frame_number < video->framenum || frame_number - video->framenum > MPEG2_SEEK_THRESHOLD))
				{
				// Elementary stream
				if(file->is_video_stream)
					{	
					mpeg2_t *file = (mpeg2_t *)video->file;
					mpeg2_vtrack_t *track = (mpeg2_vtrack_t *)video->track;
					long byte = (long)((float)(mpeg2demuxer_total_bytes(vstream->demuxer) / 
						track->total_frames) * 
						frame_number);
					long minimum = 65535;
					int done = 0;

					//printf("seek elementary %d\n", frame_number);
					// Get GOP just before frame 
					do	{
						result = mpeg2bits_seek_byte(vstream, byte);
						mpeg2bits_start_reverse(vstream);
						if(!result) result = mpeg2video_prev_code(vstream, MPEG2_GOP_START_CODE);
						mpeg2bits_start_forward(vstream);
						mpeg2bits_getbits(vstream, 8);
						if(!result) result = mpeg2video_getgophdr(video);
						this_gop_start = mpeg2video_goptimecode_to_frame(video);

						//printf("wanted %ld guessed %ld byte %ld result %d\n", frame_number, this_gop_start, byte, result);
						if(labs(this_gop_start - frame_number) >= labs(minimum)) 
							done = 1;
						else
							{
							minimum = this_gop_start - frame_number;
							byte += (long)((float)(frame_number - this_gop_start) * 
								(float)(mpeg2demuxer_total_bytes(vstream->demuxer) / 
								track->total_frames));
							if(byte < 0) byte = 0;
							}
						} while(!result && !done);

					//printf("wanted %d guessed %d\n", frame_number, this_gop_start);
					if(!result)
						{
						video->framenum = this_gop_start;
						result = mpeg2video_drop_frames(video, frame_number - video->framenum);
						}
					}
				else
					{
					// System stream
					mpeg2bits_seek_time(vstream, (double)frame_number / video->frame_rate);
					percentage = mpeg2bits_tell_percentage(vstream);
					//printf("seek frame %ld percentage %f byte %ld\n", frame_number, percentage, mpeg2bits_tell(vstream));
					mpeg2bits_start_reverse(vstream);
					mpeg2video_prev_code(vstream, MPEG2_GOP_START_CODE);
					mpeg2bits_getbits_reverse(vstream, 32);
					mpeg2bits_start_forward(vstream);
					//printf("seek system 1 %f\n", (double)frame_number / video->frame_rate);

					while(!result && mpeg2bits_tell_percentage(vstream) < percentage)
						{
						result = mpeg2video_read_frame_backend(video, 0);
						if(match_refframes)
							mpeg2video_match_refframes(video);

						//printf("seek system 2 %f %f\n", mpeg2bits_tell_percentage(vstream) / percentage);
						match_refframes = 0;
						}
					//printf("seek system 3 %f\n", (double)frame_number / video->frame_rate);
					}
				video->framenum = frame_number;
				}
			else
				{
				// Drop frames
				mpeg2video_drop_frames(video, frame_number - video->framenum);
				}
			}
		}
	return result;
	}

int mpeg2video_drop_frames(mpeg2video_t *video, long frames)
	{
	int result = 0;
	long frame_number = video->framenum + frames;

	// Read the selected number of frames and skip b-frames
	while(!result && frame_number > video->framenum)
		{
		result = mpeg2video_read_frame_backend(video, frame_number - video->framenum);
		}
	return result;
	}
