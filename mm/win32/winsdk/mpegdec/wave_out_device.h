#ifndef INC_WAVE_OUT_DEVICE
#define INC_WAVE_OUT_DEVICE

#ifndef _WINDOWS_
#include <windows.h>
#endif

#ifndef _INC_MMSYSTEM
#include <mmsystem.h>
#endif

#ifndef _WIN32_WCE
#pragma comment (lib,"winmm.lib")
#endif

#pragma warning(disable: 4018) // signed/unsigned mismatch
#include <string>

class wave_out_device
	{
	public:

	wave_out_device()
	:	m_hWaveOut(NULL),
		m_hDoneEvent(CreateEvent(NULL, TRUE, TRUE, NULL)),
		m_needs_unprepare(false)
		{
		memset(&m_waveHdr, 0, sizeof(WAVEHDR));
		}
	
	~wave_out_device()
		{
		if(m_needs_unprepare) stop();
		if(is_open()) close();
		if(m_hDoneEvent!=NULL) CloseHandle(m_hDoneEvent);
		}
	
	bool open(int nSamplesPerSec, int nChannels)
		{
		int wBitsPerSample = 16; 
		int nBlockAlign = nChannels*wBitsPerSample/8; 
		long nAvgBytesPerSec = nBlockAlign*nSamplesPerSec;
		WAVEFORMATEX wf = {WAVE_FORMAT_PCM, 
			WORD(nChannels), 
			DWORD(nSamplesPerSec), 
			DWORD(nAvgBytesPerSec),
			WORD(nBlockAlign),
			WORD(wBitsPerSample),
			WORD(0) 
			};
		MMRESULT mmres = waveOutOpen(&m_hWaveOut, WAVE_MAPPER, &wf, (DWORD)wave_out_device::callback, (DWORD)this, CALLBACK_FUNCTION);
		if(mmres != MMSYSERR_NOERROR)
			{
			if(mmres == MMSYSERR_INVALHANDLE)
				seterror("waveOutOpen", "MMSYSERR_INVALHANDLE, Specified device handle is invalid.");
			else if(mmres == MMSYSERR_BADDEVICEID)
				seterror("waveOutOpen", "MMSYSERR_BADDEVICEID, Specified device identifier is out of range.");
			else if(mmres == MMSYSERR_NODRIVER)
				seterror("waveOutOpen", "MMSYSERR_NODRIVER, No device driver is present");
			else if(mmres == MMSYSERR_NOMEM)
				seterror("waveOutOpen", "MMSYSERR_NOMEM, Unable to allocate or lock memory.");
			else if(mmres == WAVERR_BADFORMAT)
				seterror("waveOutOpen", "WAVERR_BADFORMAT, Attempted to open with an unsupported waveform-audio format.");
			else if(mmres == WAVERR_SYNC)
				seterror("waveOutOpen", "WAVERR_SYNC, Device is synchronous but waveOutOpen was called without using the WAVE_ALLOWSYNC flag");
			return false;
			}
		return true;
		}

	void close()
		{
		if(m_hWaveOut != NULL)
			{
			waveOutClose(m_hWaveOut);
			m_hWaveOut = NULL;
			}
		}

	bool reset() 
		{ 
		if(m_hWaveOut == NULL) return false;
		return waveOutReset(m_hWaveOut) == MMSYSERR_NOERROR;
		}

	bool suspend() 
		{ 
		if(m_hWaveOut == NULL) return false;
		return waveOutPause(m_hWaveOut) == MMSYSERR_NOERROR;
		}

	bool resume() 
		{ 
		if(m_hWaveOut == NULL) return false;
		return waveOutRestart(m_hWaveOut) == MMSYSERR_NOERROR;
		}

	bool prepare_playback()
		{
		if(m_audio_data.empty()) return false;

		m_waveHdr.lpData = const_cast<char*>(m_audio_data.data());
		m_waveHdr.dwBufferLength = m_audio_data.length();
		MMRESULT mmres = waveOutPrepareHeader(m_hWaveOut, &m_waveHdr, sizeof(WAVEHDR));
		if(mmres != MMSYSERR_NOERROR)
			return false;
		m_needs_unprepare = true;
		suspend();
		mmres = waveOutWrite(m_hWaveOut, &m_waveHdr, sizeof(WAVEHDR));
		return (mmres == MMSYSERR_NOERROR);
		}

	bool play()
		{
		if(!m_needs_unprepare) 
			{
			if(!prepare_playback())
				return false;
			}
		return resume();
		}

	void stop()
		{
		reset();
		waveOutUnprepareHeader(m_hWaveOut, &m_waveHdr, sizeof(WAVEHDR));
		m_needs_unprepare = false;
		memset(&m_waveHdr, 0, sizeof(WAVEHDR));
		}

	void seterror(const char *funcname, const char *msg)
		{
		printf("%s failed, %s", funcname, msg);
		}

	static void __stdcall callback(HWAVEOUT hwo, UINT uMsg, DWORD dwInstance, DWORD dwParam1, DWORD dwParam2)
		{
		wave_out_device *wout = (wave_out_device*)dwInstance;
		if(uMsg == WOM_DONE)
			SetEvent(wout->m_hDoneEvent);
		}

	bool is_open() const { return (m_hWaveOut != NULL);}
	std::basic_string<char>& get_data_ref() { return m_audio_data;}
	operator HWAVEOUT() { return m_hWaveOut;}
	HANDLE get_done_event() const { return m_hDoneEvent;}

	private:
	HWAVEOUT m_hWaveOut;
	std::basic_string<char> m_audio_data;
	WAVEHDR m_waveHdr;
	HANDLE m_hDoneEvent;
	bool m_needs_unprepare;
	};

#endif INC_WAVE_OUT_DEVICE
