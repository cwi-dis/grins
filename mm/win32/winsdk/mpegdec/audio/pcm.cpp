#include "pcm.h"

#include "streams/bitstream.h"

int mpeg2audio_read_pcm_header(mpeg2audio_t *audio)
{
	unsigned int code;
	
	code = mpeg2bits_getbits(audio->astream, 16);
	while(!mpeg2bits_eof(audio->astream) && code != MPEG2_PCM_START_CODE)
	{
		code <<= 8;
		code &= 0xffff;
		code |= mpeg2bits_getbits(audio->astream, 8);
	}

	audio->framesize = 0x7db;
	audio->avg_framesize = (float)audio->framesize;
	audio->channels = 2;
	
	return mpeg2bits_eof(audio->astream);
}

int mpeg2audio_do_pcm(mpeg2audio_t *audio)
{
	int i, j, k;
	MPEG2_INT16 sample;
	int frame_samples = (audio->framesize - 3) / audio->channels / 2;

	if(mpeg2bits_read_buffer(audio->astream, audio->ac3_buffer, frame_samples * audio->channels * 2))
		return 1;

/* Need more room */
	if(audio->pcm_point / audio->channels >= audio->pcm_allocated - MPEG2AUDIO_PADDING * audio->channels)
	{
		mpeg2audio_replace_buffer(audio, audio->pcm_allocated + MPEG2AUDIO_PADDING * audio->channels);
	}

	k = 0;
	for(i = 0; i < frame_samples; i++)
	{
		for(j = 0; j < audio->channels; j++)
		{
			sample = ((MPEG2_INT16)(audio->ac3_buffer[k++])) << 8;
			sample |= audio->ac3_buffer[k++];
			audio->pcm_sample[audio->pcm_point + i * audio->channels + j] = 
				(float)sample / 32767;
		}
	}
	audio->pcm_point += frame_samples * audio->channels;
	return 0;
}
