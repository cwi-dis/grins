
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include <windows.h>

#include "mpeg_player.h"

#include "libglobals.h"
#include "mpegdecoder.h"
#include "mpegdisplay.h"

#include "../common/thread.h"

class VideoThread : public Thread
	{
	public:
	VideoThread(MpegDecoder& decoder)
	:	m_decoder(decoder),
		m_hPlaybackEvent(CreateEvent(NULL, TRUE, FALSE, NULL))
		{
		}

	~VideoThread()
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
	MpegDecoder& m_decoder;
	HANDLE m_hPlaybackEvent;
	};

DWORD VideoThread::Run()
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

	while(m_decoder.parse_picture_header())
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
MpegPlayer::MpegPlayer()
:	decoder(0), display(0), pVideoThread(0)
	{
	clear_options();
	initialize_decoder();
	di = new display_info;
	memset(di, 0, sizeof(display_info));
	}

MpegPlayer::~MpegPlayer()
	{
	close();
	delete di;
	}

bool MpegPlayer::can_decode(int handle)
	{
	decoder = new MpegDecoder();
	if(!decoder->check(handle) || !decoder->parse_picture_header())
		{
		decoder->detach_file_handle();
		delete decoder;
		decoder = 0;
		return false;
		}
	decoder->initialize_sequence();
	decoder->get_display_info(*di);
	return true;
	}

double MpegPlayer::get_duration()
	{
	if(decoder == 0) return 0.0;
	decoder->reset_framenum();
	decoder->decode_picture();
	decoder->update_framenum();
	while(decoder->parse_picture_header())
		{
		decoder->decode_picture();
		decoder->update_framenum();
		}
	decoder->write_last_sequence_frame();
	double rate = decoder->get_frame_rate();
	int nframes = decoder->get_sequence_framenum() + 1;
	return nframes/rate;
	}

void MpegPlayer::close()
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
		}
	if(display != 0) 
		{
		delete display;
		display = 0;
		}
	finalize_decoder();
	}

int MpegPlayer::get_width() const
	{
	return di->horizontal_size;
	}

int MpegPlayer::get_height() const
	{
	return di->vertical_size;
	}

double MpegPlayer::get_frame_rate() const
	{
	if(decoder != 0)
		return decoder->get_frame_rate();
	return 1.0;
	}

double MpegPlayer::get_bit_rate() const
	{
	if(decoder != 0)
		return decoder->get_bit_rate();
	return 10000.0;
	}

void MpegPlayer::prepare_playback(surface<color_repr_t> *psurf)
	{
	if(decoder != 0)
		{
		display = new MpegDisplay(*di);
		decoder->set_display(display);
		display->set_surface(psurf);
		pVideoThread = new VideoThread(*decoder);
		pVideoThread->Start();
		}
	}

void MpegPlayer::suspend_playback()
	{
	if(pVideoThread != 0)
		pVideoThread->suspend_playback();
	}

void MpegPlayer::resume_playback()
	{
	if(pVideoThread != 0)
		pVideoThread->resume_playback();
	}

bool MpegPlayer::finished_playback()
	{
	if(pVideoThread == 0) return true;
	return WaitForSingleObject(pVideoThread->GetStopHandle(), 0) == WAIT_OBJECT_0;
	}

void MpegPlayer::lock_surface()
	{
	if(display != 0) display->lock();
	}

void MpegPlayer::unlock_surface()
	{
	if(display != 0) display->unlock();
	}

void MpegPlayer::set_direct_update_box(int x, int y, int w, int h)
	{
	if(display != 0) display->set_direct_update_box(x, y, w, h);
	}

