#ifndef INC_MP3_DECODER
#define INC_MP3_DECODER

#include "..\..\CE\mp3lib\mp3lib.h"

class mp3_decoder
	{
	public:
	mp3_decoder()
	:	m_is_initialized(false)
		{
		initialize();
		}

	~mp3_decoder()
		{
		finalize();
		}

	void initialize()
		{
		if(!m_is_initialized)
			{
			int equalizer = 0;
			char *eqfactors = NULL;
			mp3_lib_init(equalizer, eqfactors);
			m_is_initialized = true;
			}
		}

	void finalize()
		{
		if(m_is_initialized)
			{
			mp3_lib_finalize();
			m_is_initialized = false;
			}
		}

	void reset()
		{
		finalize();
		initialize();
		}

	void get_wave_format(const std::basic_string<BYTE>& data, WAVEFORMATEX& wfx) 
		{
		int nSamplesPerSec = wfx.nSamplesPerSec;
		int nChannels, BitRate;
		mp3_lib_decode_header(const_cast<BYTE*>(data.data()), data.size(), &nSamplesPerSec, &nChannels, &BitRate);
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
		wfx = wf;
		}
	
	int decode_buffer(const std::basic_string<BYTE>& data, 
		BYTE *decoded_data, size_t decoded_data_size, size_t& bytes_produced);
	int decode_buffer(BYTE *decoded_data, size_t decoded_data_size, size_t& bytes_produced);

	bool m_is_initialized;
	int m_inputpos;
	};


inline int mp3_decoder::decode_buffer(const std::basic_string<BYTE>& data, 
		BYTE *decoded_data, size_t decoded_data_size, size_t& bytes_produced)
	{
	m_inputpos = 0;
	bytes_produced = 0;
	int status = mp3_lib_decode_buffer(const_cast<BYTE*>(data.data()), data.size(), 
		(char*)decoded_data, decoded_data_size, (int*)&bytes_produced, &m_inputpos);
	return status;
	}

inline int mp3_decoder::decode_buffer(BYTE *decoded_data, size_t decoded_data_size, size_t& bytes_produced)
	{
	bytes_produced = 0;
	int lostsync = 0;
	int status = mp3_lib_decode_buffer(NULL, 0, (char*)decoded_data, decoded_data_size, (int*)&bytes_produced, &m_inputpos);
	return status;
	}

#endif // INC_MP3_DECODER