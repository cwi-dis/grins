
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

	size_t pos = m_decoder.get_stream_pos();
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

class audio_thread : public Thread
	{
	public:
	audio_thread(const TCHAR *filename)
	:	m_filename(filename),
		m_pwavout(NULL),
		m_hPlaybackEvent(CreateEvent(NULL, TRUE, FALSE, NULL)),
		m_ready(false),
		m_data_read(false)
		{
		}

	~audio_thread()
		{
		if(m_pwavout != 0) delete m_pwavout;
		if(m_hPlaybackEvent) CloseHandle(m_hPlaybackEvent);
		}

	void suspend_playback()
		{
		if(m_pwavout != 0) m_pwavout->suspend();
		ResetEvent(m_hPlaybackEvent);
		}

	void resume_playback()
		{
		if(m_pwavout != 0) m_pwavout->resume();
		SetEvent(m_hPlaybackEvent);
		}
	
	bool is_ready() const {return m_ready;}
	bool is_running() const
		{return WaitForSingleObject(GetStopHandle(), 0) != WAIT_OBJECT_0;}
	void wait_ready()
		{
		while(is_running() && !is_ready()) 
			Sleep(50);
		}

	protected:
	virtual DWORD Run();

	void write_audio_chunks(mpeg_container& mpeg2);

	private:
	std::basic_string<TCHAR> m_filename;
	wave_out_device *m_pwavout;
	HANDLE m_hPlaybackEvent;
	bool m_ready;
	bool m_data_read;
	enum {buffers_init = 4, buffers_low = 8, buffers_hi = 10};
	};

void audio_thread::write_audio_chunks(mpeg_container& mpeg2)
	{
#ifdef USE_AUDIO_STREAM
	while(!m_data_read && m_pwavout->get_audio_data_size()<buffers_hi)
		{
		char *audio_data = 0;
		int nr = mpeg2.read_audio_chunk(&audio_data);
		if(nr == 0)
			{
			if(audio_data != 0) delete audio_data;
			m_data_read = true;
			break;
			}
		if(!m_pwavout->write_audio_chunk(audio_data, nr))
			break;
		}
#endif
	}

DWORD audio_thread::Run()
	{
	mpeg_container mpeg2;
	if(!mpeg2.open(m_filename.c_str()))
		{
		SetEvent(GetStopHandle());
		return 1;
		}

	if(!mpeg2.has_audio())
		{
		SetEvent(GetStopHandle());
		return 1;
		}

	m_pwavout = new wave_out_device();
	if(!m_pwavout->open(mpeg2.get_sample_rate(), 16, 1))
		{
		delete m_pwavout;
		m_pwavout = 0;
		SetEvent(GetStopHandle());
		return 1;
		}

	write_audio_chunks(mpeg2);
	m_ready = true;

	HANDLE handles[] = {GetStopHandle(), m_hPlaybackEvent};
	DWORD wres = WaitForMultipleObjects(2, handles, FALSE, INFINITE);
	if(wres == WAIT_OBJECT_0) return 0;
	
	while(WaitForSingleObject(GetStopHandle(), 0) != WAIT_OBJECT_0)
		{
		WaitForMultipleObjects(2, handles, FALSE, INFINITE);
		if(m_pwavout->get_audio_data_size()<buffers_low)
			write_audio_chunks(mpeg2);
		}

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
	pAudioThread(0)
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
	decoder->initialize_sequence();
	decoder->get_display_info(*di);
	return true;
	}

double mpeg_player::get_duration()
	{
	if(pinstream == 0) return 0.0;
	
	mpeg_container mpeg2;
	if(!mpeg2.open(pinstream->get_pathname(), false))
		return 0.0;

	return mpeg2.get_duration();
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
	if(pAudioThread != 0)
		{
		pAudioThread->Stop();
		delete pAudioThread;
		pAudioThread = 0;
		}
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
		
		/*
		if(pAudioThread == 0)
			{
			pAudioThread = new audio_thread(pinstream->get_pathname());
			pAudioThread->Start();
			pAudioThread->wait_ready();
			}
		*/

		pVideoThread = new video_thread(*decoder);
		pVideoThread->Start();
		}
	}

void mpeg_player::suspend_playback()
	{
	if(pVideoThread != 0)
		pVideoThread->suspend_playback();
	if(pAudioThread != 0) 
		pAudioThread->suspend_playback();
	}

void mpeg_player::resume_playback()
	{
	if(pVideoThread != 0)
		pVideoThread->resume_playback();

	if(pAudioThread != 0) 
		pAudioThread->resume_playback();
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

