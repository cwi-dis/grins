
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

// xxx: take into account frame rate
DWORD VideoThread::Run()
	{
	HANDLE handles[] = {GetStopHandle(), m_hPlaybackEvent};
	DWORD wres = WaitForMultipleObjects(2, handles, FALSE, INFINITE);
	if(wres == WAIT_OBJECT_0) return 0;

	m_decoder.decode_picture();
	wres = WaitForMultipleObjects(2, handles, FALSE, INFINITE);
	if(wres == WAIT_OBJECT_0) return 0;
	m_decoder.update_framenum();

	while(m_decoder.parse_picture_header())
		{
		m_decoder.decode_picture();
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
	if(!decoder->check(handle))
		{
		decoder->detach_file_handle();
		return false;
		}
	if(!decoder->parse_picture_header())
		{
		decoder->detach_file_handle();
		return false;
		}
	decoder->initialize_sequence();
	decoder->get_display_info(*di);
	display = new MpegDisplay(*di);
	decoder->set_display(display);
	decoder->reset_framenum();
	return true;
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
		if(display != 0)
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

double MpegPlayer::get_duration() const
	{
	// not implemented yet
	return 10.0;
	}

void MpegPlayer::prepare_playback(surface<color_repr_t> *psurf)
	{
	if(decoder != 0 && display != 0)
		{
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


