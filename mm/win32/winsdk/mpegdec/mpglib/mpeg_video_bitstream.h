#ifndef INC_MPEG_VIDEO_BITSTREAM
#define INC_MPEG_VIDEO_BITSTREAM


#ifndef INC_MPEG_INPUT_STREAM
#include "mpeg_input_stream.h"
#endif

#ifndef INC_MPEG2CON
#include "mpeg2con.h"
#endif

#include <stdio.h> // temp printf()
#include <stdlib.h> // temp exit()

class mpeg_video_bitstream
	{
	public:
	typedef unsigned char uchar_t;

	mpeg_video_bitstream(mpeg_input_stream *istream);
	~mpeg_video_bitstream();

	bool is_valid() const { return m_is_valid;}

	void initialize_buffer();
	void fill_buffer();
	void advance_bit_stream(int N);
	void advance_bit_stream32();

	unsigned int next_bits(int N);
	void next_code();
	int get_byte();
	int get_word();
	unsigned int get_bits(int N);
	unsigned int get_bits32();
	unsigned int get_bits1();
	int get_long();

	void next_packet();

	void flush_buffer32() { advance_bit_stream32();}
	void flush_buffer(int N) { advance_bit_stream(N);}
	void next_start_code() {next_code();}
	
	bool validate_stream();
	size_t read(unsigned char *buffer, size_t bytes);
	bool seek(size_t pos);

	mpeg_input_stream *m_istream;

	unsigned char *m_Rdbfr;
	unsigned char *m_Rdptr;
	unsigned char m_Inbfr[16];
  
	unsigned int m_Bfr;
	unsigned char *m_Rdmax;
	int m_Incnt;
	int m_Bitcnt;

	bool m_is_system_stream;
	bool m_is_valid;

	size_t m_curpos;
	size_t m_save_stream;

	typedef unsigned char uchar_t;
	enum {buffer_size = 2048};
	};

inline mpeg_video_bitstream::mpeg_video_bitstream(mpeg_input_stream *istream)
:	m_istream(istream), 
	m_Rdbfr(new uchar_t[buffer_size]),
	m_is_system_stream(false),
	m_save_stream(false),
	m_curpos(0)
	{
	m_is_valid = validate_stream();
	}

inline size_t mpeg_video_bitstream::read(unsigned char *buffer, size_t bytes)
	{
	if(!m_save_stream)
		{
		int nread = m_istream->read(buffer, bytes);
		m_curpos += nread;
		return nread;
		}
	size_t pos = m_istream->tell();
	m_istream->seek(m_curpos);
	int nread = m_istream->read(buffer, bytes);
	m_curpos += nread;
	m_istream->seek(pos);
	return nread;
	}

inline bool mpeg_video_bitstream::seek(size_t pos)
	{
	if(!m_save_stream)
		m_istream->seek(pos);
	else
		m_curpos = pos;
	return true;
	}

inline bool mpeg_video_bitstream::validate_stream()
	{
	seek(0);
	initialize_buffer(); 
    if(next_bits(8) == 0x47)
		{
		printf("Decoder currently does not parse transport streams\n");
		return false;
		}

	next_code();
	int code = next_bits(32);
    switch(code)
		{
		case MPEG2_SEQUENCE_START_CODE:
			//printf("MPEG2_SEQUENCE_START_CODE\n");
			break;
		case MPEG2_PACK_START_CODE:
			//printf("PACK_START_CODE\n");
			m_is_system_stream = true;
			break;
		case VIDEO_ELEMENTARY_STREAM:
			printf("VIDEO_ELEMENTARY_STREAM\n");
			//m_is_system_stream = true;
			break;
		default:
			printf("Unable to recognize stream type (0x%08x)\n", code);
			return false;
		}
	seek(0);
    initialize_buffer();
	return true;
	}

inline mpeg_video_bitstream::~mpeg_video_bitstream()
	{
	if(m_Rdbfr != NULL) 
		delete[] m_Rdbfr;
	}
inline void mpeg_video_bitstream::initialize_buffer()
	{
	m_Incnt = 0;
	m_Rdptr = m_Rdbfr + buffer_size;
	m_Rdmax = m_Rdptr;
	m_Bfr = 0;
	advance_bit_stream(0);
	}

// return next n bits (right adjusted) without advancing
inline unsigned int mpeg_video_bitstream::next_bits(int N) 
	{ 
	return m_Bfr >> (32-N);
	}

inline unsigned int mpeg_video_bitstream::get_bits32()
	{
	unsigned int l = next_bits(32);
	advance_bit_stream32();
	return l;
	}

inline void mpeg_video_bitstream::next_code()
	{
	// byte align
	advance_bit_stream(m_Incnt & 7);
	while (next_bits(24) != 0x01L)
		advance_bit_stream(8);
	}

// read
inline int mpeg_video_bitstream::get_byte()
	{
	while(m_Rdptr >= m_Rdbfr+buffer_size)
		{
		int nread = read(m_Rdbfr, buffer_size);
		m_Rdptr -= buffer_size;
		m_Rdmax -= buffer_size;
		}
	return *m_Rdptr++;
	}

// extract a 16-bit word from the bitstream buffer
inline int mpeg_video_bitstream::get_word()
	{
	int Val = get_byte();
	return (Val<<8) | get_byte();
	}


// return next n bits (right adjusted)
inline unsigned int mpeg_video_bitstream::get_bits(int N)
	{
	unsigned int val = next_bits(N);
	advance_bit_stream(N);
	return val;
	}

// return next bit
inline unsigned int mpeg_video_bitstream::get_bits1() { return get_bits(1);}

inline int mpeg_video_bitstream::get_long()
	{
	int i = get_word();
	return (i<<16) | get_word();
	}

inline void mpeg_video_bitstream::fill_buffer()
	{
	int nread = read(m_Rdbfr, buffer_size);
	m_Rdptr = m_Rdbfr;

	if (m_is_system_stream)
		m_Rdmax -= buffer_size;

  
	// end of the bitstream file
	if (nread < buffer_size)
		{
		// just to be safe
		if (nread < 0)
			nread = 0;

		// pad until the next to the next 32-bit word boundary
		while (nread & 3)
			m_Rdbfr[nread++] = 0;

		// pad the buffer with sequence end codes
		while (nread < buffer_size)
			{
			m_Rdbfr[nread++] = MPEG2_SEQUENCE_END_CODE >> 24;
			m_Rdbfr[nread++] = MPEG2_SEQUENCE_END_CODE >> 16;
			m_Rdbfr[nread++] = MPEG2_SEQUENCE_END_CODE >> 8;
			m_Rdbfr[nread++] = MPEG2_SEQUENCE_END_CODE & 0xff;
			}
		}
	}

// advance by n bits (Flush_Buffer)
inline void mpeg_video_bitstream::advance_bit_stream(int N)
	{
	m_Bfr <<= N;
	int Incnt = m_Incnt -= N;
	if(Incnt <= 24)
		{
		if(m_is_system_stream && (m_Rdptr >= m_Rdmax-4))
			{
			do	{
				if (m_Rdptr >= m_Rdmax)
					next_packet();
				m_Bfr |= get_byte() << (24 - Incnt);
				Incnt += 8;
				} while (Incnt <= 24);
			}
		else if (m_Rdptr < m_Rdbfr+2044)
			{
			do	{
				m_Bfr |= *m_Rdptr++ << (24 - Incnt);
				Incnt += 8;
				} while (Incnt <= 24);
			}
		else
			{
			do	{
				if(m_Rdptr >= m_Rdbfr+buffer_size)
					fill_buffer();
				m_Bfr |= *m_Rdptr++ << (24 - Incnt);
				Incnt += 8;
				} while (Incnt <= 24);
			}
		m_Incnt = Incnt;
		}
	}

// Flush_Buffer32
// advance by 32 bits 
inline void mpeg_video_bitstream::advance_bit_stream32()
	{
	int Incnt;

	m_Bfr = 0;

	Incnt = m_Incnt;
	Incnt -= 32;

	if (m_is_system_stream && (m_Rdptr >= m_Rdmax-4))
		{
		while (Incnt <= 24)
			{
			if(m_Rdptr >= m_Rdmax)
				next_packet();
			m_Bfr |= get_byte() << (24 - Incnt);
			Incnt += 8;
			}
		}
	else
		{
		while (Incnt <= 24)
			{
			if (m_Rdptr >= m_Rdbfr+2048)
				fill_buffer();
			m_Bfr |= *m_Rdptr++ << (24 - Incnt);
			Incnt += 8;
			}
		}
	m_Incnt = Incnt;
	}

// initialize buffer, call once before first getbits or showbits
// parse system layer, ignore everything we don't need
inline void mpeg_video_bitstream::next_packet()
	{
	int l = 0;
	unsigned int code;
	for(;;)
		{
		code = get_long();

		// remove system layer byte stuffing
		while ((code & 0xffffff00) != 0x100)
			code = (code<<8) | get_byte();

		switch(code)
			{
			case MPEG2_PACK_START_CODE: // pack header
				// skip pack header (system_clock_reference and mux_rate)
				m_Rdptr += 8;
				break;
			case VIDEO_ELEMENTARY_STREAM:   
				code = get_word();             // packet_length
				m_Rdmax = m_Rdptr + code;

				code = get_byte();

				if((code>>6)==0x02)
					{
					m_Rdptr++;
					code=get_byte();  // parse PES_header_data_length
					m_Rdptr+=code;    // advance pointer by PES_header_data_length
					printf("MPEG-2 PES packet\n");
					return;
					}
				else if(code == 0xff)
					{
					// parse MPEG-1 packet header
					while((code=get_byte())== 0xFF);
					}
       
				  // stuffing bytes
				  if(code>=0x40)
					{
					if(code>=0x80)
						{
						fprintf(stderr,"Error in packet header\n");
						exit(1);
						}
					// skip STD_buffer_scale
					m_Rdptr++;
					code = get_byte();
					}

				  if(code>=0x30)
					{
					if(code>=0x40)
						{
						fprintf(stderr,"Error in packet header\n");
						exit(1);
						}
					// skip presentation and decoding time stamps
					m_Rdptr += 9;
				  }
				  else if(code>=0x20)
					{
					// skip presentation time stamps
					m_Rdptr += 4;
					}
				  else if(code!=0x0f)
					{
					fprintf(stderr,"Error in packet header\n");
					exit(1);
					}
				  return;
			case ISO_END_CODE: // end
				// simulate a buffer full of sequence end codes
				while (l<2048)
					{
					m_Rdbfr[l++] = MPEG2_SEQUENCE_END_CODE>>24;
					m_Rdbfr[l++] = MPEG2_SEQUENCE_END_CODE>>16;
					m_Rdbfr[l++] = MPEG2_SEQUENCE_END_CODE>>8;
					m_Rdbfr[l++] = MPEG2_SEQUENCE_END_CODE&0xff;
					}
				  m_Rdptr = m_Rdbfr;
				  m_Rdmax = m_Rdbfr + 2048;
				  return;
			default:
				if(code >= MPEG2_SYSTEM_START_CODE)
					{
					// skip system headers and non-video packets
					code = get_word();
					m_Rdptr += code;
					}
				else
					{
					fprintf(stderr,"Unexpected startcode %08x in system layer\n",code);
					exit(1);
					}
				  break;
			}
		}
	}


#endif // INC_MPEG_VIDEO_BITSTREAM






