#include <windows.h>

#include <tchar.h>

#include "mpglib/mpeg_video_bitstream.h"
#include "mpeg_player.h"

#include "../common/profiler.h"

///////////////
int main(int argc, char *argv[])
	{
	//TCHAR filename[] = TEXT("D:\\ufs\\mm\\cmif\\win32\\winsdk\\mpegdec\\bin\\test_audio_video.mpg");
	TCHAR filename[] = TEXT("D:\\ufs\\mm\\cmif\\win32\\winsdk\\mpegdec\\bin\\test.mpg");

	mpeg_input_stream *is = open_mpeg_input_stream(filename);
	if(is == NULL)
		{
		_tprintf(TEXT("Failed to open %s\n"), filename);
		return 1;
		}

	// video frames will be stored in ./data
	// video sound should play normally

	mpeg_player player;
	if(!player.set_input_stream(is))
		{
		printf("player.can_decode() failed\n");
		is->close();
		delete is;
		return 1;
		}
	
	{
	profiler pf("get_duration");
	printf("duration = %f\n", player.get_duration());
	}


	surface<color_repr_t> *psurf = new surface<color_repr_t>(player.get_width(), player.get_height());
	player.prepare_playback(psurf);
	printf("%d %d %f\n", player.get_width(), player.get_height(), player.get_frame_rate());
	
	player.resume_playback();
	int i = 0;
	while(!player.finished_playback())
		{
		printf(".");
		Sleep(50);
		}
	printf("\n");
	player.close();
	delete psurf;

	_tprintf(TEXT("\nOK\n"));
	return 0;
	}
