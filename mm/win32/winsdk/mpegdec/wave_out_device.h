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
#pragma warning(disable: 4786) 
#include <string>
#include <deque>

class wave_out_device
	{
	public:

	wave_out_device()
	:	m_hWaveOut(NULL),
		m_hDoneEvent(CreateEvent(NULL, TRUE, TRUE, NULL))
		{
		}
	
	~wave_out_device()
		{
		if(is_open()) close();
		clear_data();
		if(m_hDoneEvent != NULL) CloseHandle(m_hDoneEvent);
		}
	
	bool open(int nSamplesPerSec, int nChannels)
		{
		int wBitsPerSample = 16; 
		int nBlockAlign = nChannels*wBitsPerSample/8; 
		long nAvgBytesPerSec = nBlockAlign*nSamplesPerSec;
		WAVEFORMATEX wf = {WAVE_FORMAT_PCM, 
			WORD(nChannels), 
			DWORD(nSamplesPerSec/nChannels), 
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
		waveOutPause(m_hWaveOut);
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

	bool play()
		{
		return resume();
		}

	void stop()
		{
		reset();
		}

	void seterror(const char *funcname, const char *msg)
		{
		printf("%s failed, %s\n", funcname, msg);
		}
	void seterror(const char *funcname)
		{
		printf("%s failed\n", funcname);
		}

	static void __stdcall callback(HWAVEOUT hwo, UINT uMsg, DWORD dwInstance, DWORD dwParam1, DWORD dwParam2)
		{
		wave_out_device *wout = (wave_out_device*)dwInstance;
		if(uMsg == WOM_OPEN)
			{
			;//printf("WOM_OPEN\n");
			}
		else if(uMsg == WOM_DONE)
			{
			//printf("WOM_DONE\n");
			wout->unprepare_front_chunk();
			if(!wout->has_audio_data())
				SetEvent(wout->m_hDoneEvent);
			}
		else if(uMsg == WOM_CLOSE)
			{
			//printf("WOM_CLOSE\n");
			wout->clear_data();
			SetEvent(wout->m_hDoneEvent);
			}
		}

	bool is_open() const { return (m_hWaveOut != NULL);}
	operator HWAVEOUT() { return m_hWaveOut;}
	HANDLE get_done_event() const { return m_hDoneEvent;}

	bool write_audio_chunk(char *data, int len)
		{
		m_audio_data.push_back(WAVEHDR());
		WAVEHDR& waveHdr = m_audio_data.back();
		memset(&waveHdr, 0, sizeof(WAVEHDR));
		waveHdr.lpData = data;
		waveHdr.dwBufferLength = len;
		MMRESULT mmres = waveOutPrepareHeader(m_hWaveOut, &waveHdr, sizeof(WAVEHDR));
		if(mmres != MMSYSERR_NOERROR)
			seterror("waveOutPrepareHeader()");
		mmres = waveOutWrite(m_hWaveOut, &waveHdr, sizeof(WAVEHDR));
		if(mmres != MMSYSERR_NOERROR)
			seterror("waveOutWrite()");
		return (mmres == MMSYSERR_NOERROR);
		}

	void unprepare_front_chunk()
		{
		if(!m_audio_data.empty())
			{
			WAVEHDR& waveHdr = m_audio_data.front();
			if(m_hWaveOut) waveOutUnprepareHeader(m_hWaveOut, &waveHdr, sizeof(WAVEHDR));
			delete[] waveHdr.lpData;
			m_audio_data.pop_front();
			}

		}
	bool has_audio_data() const { return !m_audio_data.empty();}
	void clear_data()
		{
		while(has_audio_data()) unprepare_front_chunk();
		}
	size_t get_audio_data_size() const { return m_audio_data.size();}
	private:
	HWAVEOUT m_hWaveOut;
	std::deque<WAVEHDR> m_audio_data;
	HANDLE m_hDoneEvent;
	};

#endif // INC_WAVE_OUT_DEVICE
