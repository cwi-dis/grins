#include <windows.h>

#include <tchar.h>

#include "mpeg_container.h"


#include "mpglib/mpeg_video_bitstream.h"
#include "mpeg_player.h"

///////////////
int main(int argc, char *argv[])
	{
	TCHAR filename[] = TEXT("D:\\ufs\\mm\\cmif\\win32\\winsdk\\mpegdec\\bin\\test.mpg");

	mpeg_container mpeg2;
	if(!mpeg2.open(filename))
		{
		_tprintf(TEXT("Failed to open %s\n"), filename);
		return 1;
		}

	if(mpeg2.has_video()) 
		{
		_tprintf(TEXT("VIDEO =====================\n"));
		_tprintf(TEXT("%d video stream(s)\n"), mpeg2.get_video_streams_size());
		_tprintf(TEXT("video %d %d\n"), mpeg2.get_video_width(), mpeg2.get_video_height());
		_tprintf(TEXT("frame_rate %f\n"), mpeg2.get_frame_rate());
		}
	else _tprintf(TEXT("no video streams\n"));


	if(mpeg2.has_audio()) 
		{
		_tprintf(TEXT("AUDIO =====================\n"));
		_tprintf(TEXT("%d audio stream(s)\n"), mpeg2.get_audio_streams_size());
		_tprintf(TEXT("audio channels %d\n"), mpeg2.get_audio_channels());
		_tprintf(TEXT("sample rate %d\n"), mpeg2.get_sample_rate());
		}
	else _tprintf(TEXT("no audio streams\n"));

	_tprintf(TEXT("\nOK\n"));

	
	///////////////////////////////
	_tprintf(TEXT("using std video decoder\n"));

	mpeg_input_stream *is = open_mpeg_input_stream(filename);
	if(is == NULL)
		{
		_tprintf(TEXT("Failed to open %s\n"), filename);
		return 1;
		}

	mpeg_player player;
	if(!player.set_input_stream(is))
		{
		printf("player.can_decode() failed\n");
		is->close();
		delete is;
		return 1;
		}
	surface<color_repr_t> *psurf = new surface<color_repr_t>(player.get_width(), player.get_height());
	player.prepare_playback(psurf);
	printf("%d %d %f\n", player.get_width(), player.get_height(), player.get_frame_rate());
	
	int i = 0;
	player.resume_playback();
	while(!player.finished_playback() && ++i<=2)
		{
		printf(".");
		Sleep(500);
		}
	printf("\n");
	player.close();
	delete psurf;

	_tprintf(TEXT("\nOK\n"));
	return 0;
	}
