
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include <windows.h>

#include "mpeg_player.h"

#include "mpglib/mpeg_video.h"
#include "mpglib/mpeg_video_bitstream.h"

#include "mpegdisplay.h"

// begin_audio
#include "mpeg_container.h"
#include "wave_out_device.h"
// end_audio

#include "../common/thread.h"

#include <math.h>

class video_thread : public Thread
	{
	public:
	video_thread(mpeg_video& decoder)
	:	m_decoder(decoder),
		m_hPlaybackEvent(CreateEvent(NULL, TRUE, FALSE, NULL))
		{
		}

	~video_thread()
		{
		if(m_hPlaybackEvent) CloseHandle(m_hPlaybackEvent);
		}

	void suspend_playback()
		{
		ResetEvent(m_hPlaybackEvent);
		}

	void resume_playback()
		{
		SetEvent(m_hPlaybackEvent);
		}

	protected:
	virtual DWORD Run();

	private:
	mpeg_video& m_decoder;
	HANDLE m_hPlaybackEvent;
	};

DWORD video_thread::Run()
	{
	HANDLE handles[] = {GetStopHandle(), m_hPlaybackEvent};
	DWORD wres = WaitForMultipleObjects(2, handles, FALSE, INFINITE);
	if(wres == WAIT_OBJECT_0) return 0;

	double rate = m_decoder.get_frame_rate();
	long msecs = (long)floor(0.5+1000.0/rate);

	m_decoder.reset_framenum();
	
	DWORD t0 = GetTickCount();
	m_decoder.decode_picture();
	long dt = (long)(GetTickCount() - t0);
	long wait = msecs - dt;
	if(wait>0) Sleep(wait);

	wres = WaitForMultipleObjects(2, handles, FALSE, INFINITE);
	if(wres == WAIT_OBJECT_0) return 0;

	m_decoder.update_framenum();

	while(m_decoder.get_header())
		{
		DWORD t0 = GetTickCount();
		m_decoder.decode_picture();
		long dt = (long)(GetTickCount() - t0);
		long wait = msecs - dt;
		if(wait>0) Sleep(wait);
		
		wres = WaitForMultipleObjects(2, handles, FALSE, INFINITE);
		if(wres == WAIT_OBJECT_0) return 0;

		m_decoder.update_framenum();
		}
	m_decoder.write_last_sequence_frame();
	SetEvent(GetStopHandle());
	return 0;
	}

//////////////////////////////
mpeg_player::mpeg_player()
:	pinstream(0),
	pvbitstream(0), 
	decoder(0), 
	display(0), 
	di(0), 
	pVideoThread(0),
	pwavout(0)
	{
	di = new display_info;
	memset(di, 0, sizeof(display_info));
	}

mpeg_player::~mpeg_player()
	{
	close();
	if(di != 0) delete di;
	}

bool mpeg_player::set_input_stream(mpeg_input_stream *in_stream)
	{
	pvbitstream = new mpeg_video_bitstream(in_stream);
	if(!pvbitstream->is_valid())
		{
		_tprintf(TEXT("Cant parse stream\n"));
		delete pvbitstream;
		pvbitstream = 0;
		return false;
		}
	decoder = new mpeg_video(pvbitstream);
	if(!decoder->get_header())
		{
		_tprintf(TEXT("get_header() failed\n"));
		delete decoder;
		decoder = 0;
		delete pvbitstream;
		pvbitstream = 0;
		return false;
		}
	pinstream = in_stream; // become owner
	set_audio_input_stream(pinstream);
	decoder->initialize_sequence();
	decoder->get_display_info(*di);
	return true;
	}

bool mpeg_player::set_audio_input_stream(mpeg_input_stream *in_stream)
	{
	mpeg_container mpeg2;
	if(!mpeg2.open(in_stream->get_pathname()))
		return false;
	if(mpeg2.has_audio())
		{
		pwavout = new wave_out_device();
		if(!pwavout->open(mpeg2.get_sample_rate()))
			{
			delete pwavout;
			pwavout = 0;
			return false;
			}
		mpeg2.read_audio(pwavout->get_data_ref());
		if(!pwavout->prepare_playback())
			{
			delete pwavout;
			pwavout = 0;
			return false;
			}
		}
	return true;
	}

double mpeg_player::get_duration()
	{
	if(decoder == 0) return 0.0;
	decoder->reset_framenum();
	decoder->decode_picture();
	decoder->update_framenum();
	while(decoder->get_header())
		{
		decoder->decode_picture();
		decoder->update_framenum();
		}
	decoder->write_last_sequence_frame();
	double rate = decoder->get_frame_rate();
	int nframes = decoder->get_frames_size();
	return nframes/rate;
	}

void mpeg_player::close()
	{
	if(pVideoThread != 0) 
		{
		pVideoThread->Stop();
		delete pVideoThread;
		pVideoThread = 0;
		}
	if(decoder != 0) 
		{
		decoder->finalize_sequence();
		delete decoder;
		decoder = 0;
		if(pvbitstream != 0) 
			{
			delete pvbitstream;
			pvbitstream = 0;
			}
		if(pinstream != 0)
			{
			pinstream->close();
			delete pinstream;
			pinstream = 0;
			}
		}
	if(display != 0) 
		{
		delete display;
		display = 0;
		}
	if(pwavout != 0)
		delete pwavout;
	}

int mpeg_player::get_width() const
	{
	return di->horizontal_size;
	}

int mpeg_player::get_height() const
	{
	return di->vertical_size;
	}

double mpeg_player::get_frame_rate() const
	{
	if(decoder != 0)
		return decoder->get_frame_rate();
	return 1.0;
	}

double mpeg_player::get_bit_rate() const
	{
	if(decoder != 0)
		return decoder->get_bit_rate();
	return 10000.0;
	}

void mpeg_player::prepare_playback(surface<color_repr_t> *psurf)
	{
	if(decoder != 0)
		{
		MpegDisplay *surf_display = new MpegDisplay(*di);
		decoder->set_display(surf_display);
		surf_display->set_surface(psurf);
		display = surf_display;

		pVideoThread = new video_thread(*decoder);
		pVideoThread->Start();
		}
	}

void mpeg_player::suspend_playback()
	{
	if(pVideoThread != 0)
		pVideoThread->suspend_playback();
	if(pwavout != 0) 
		pwavout->suspend();
	}

void mpeg_player::resume_playback()
	{
	if(pVideoThread != 0)
		pVideoThread->resume_playback();
	if(pwavout != 0) 
		pwavout->resume();
	}

bool mpeg_player::finished_playback()
	{
	if(pVideoThread == 0) return true;
	return WaitForSingleObject(pVideoThread->GetStopHandle(), 0) == WAIT_OBJECT_0;
	}

void mpeg_player::lock_surface()
	{
	if(display != 0) display->lock();
	}

void mpeg_player::unlock_surface()
	{
	if(display != 0) display->unlock();
	}

void mpeg_player::set_direct_update_box(int x, int y, int w, int h)
	{
	if(display != 0) display->set_direct_update_box(x, y, w, h);
	}

