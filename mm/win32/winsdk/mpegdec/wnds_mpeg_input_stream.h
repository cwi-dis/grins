
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#ifndef INC_WNDS_MPEG_INPUT_STREAM
#define INC_WNDS_MPEG_INPUT_STREAM

#ifndef INC_MPEG_INPUT_STREAM
#include "mpeg_input_stream.h"
#endif

#ifndef _INC_TCHAR
#include <tchar.h>
#endif

#ifndef _STRING_
#pragma warning(disable: 4786) // long names trunc (debug)
#include <string>
#endif

#ifndef _WINDOWS_
#include <windows.h>
#endif

class wnds_mpeg_input_stream : public mpeg_input_stream
	{
	public:
	wnds_mpeg_input_stream(TCHAR *path)
	:	m_hf(INVALID_HANDLE_VALUE), m_css(NULL), m_path(path), m_current_byte(0), m_total_bytes(0)
		{
		m_hf = ::CreateFile(path,  
			GENERIC_READ,  
			FILE_SHARE_READ,  // 0 = not shared or FILE_SHARE_READ  
			0,  // lpSecurityAttributes 
			OPEN_EXISTING,  
			FILE_ATTRIBUTE_READONLY,  
			NULL); 
		if(m_hf != INVALID_HANDLE_VALUE)
			{
			m_total_bytes =::GetFileSize(m_hf, NULL);
			if(m_total_bytes == 0)
				{
				CloseHandle(m_hf);
				m_hf = INVALID_HANDLE_VALUE;
				}
			}
		}

	virtual ~wnds_mpeg_input_stream()
		{
		if(m_css != NULL) delete m_css;
		if(m_hf != INVALID_HANDLE_VALUE)
			CloseHandle(m_hf);
		}

	virtual bool is_valid() const { return m_hf != INVALID_HANDLE_VALUE;}
	virtual size_t get_total_bytes() const { return m_total_bytes;}
	virtual size_t tell() const { return m_current_byte;}
	virtual bool is_eof() const { return m_current_byte >= m_total_bytes;}
	virtual bool is_bof() const { return m_current_byte == 0;}
	virtual const TCHAR *get_pathname() const { return m_path.c_str();}

	virtual void close()
		{
		//_tprintf(TEXT("close_mpeg_input_stream\n"));
		if(m_hf != INVALID_HANDLE_VALUE)
			{
			CloseHandle(m_hf);
			m_total_bytes = 0;
			m_hf = INVALID_HANDLE_VALUE;
			}
		}

	virtual size_t read(unsigned char *buffer, size_t bytes)
		{
		unsigned long nread = 0;
		if(ReadFile(m_hf, buffer, bytes, &nread, NULL) != 0)
			{
			//printf("read %ld bytes\n", nread);
			m_current_byte += nread;
			return nread;
			}
		return 0;
		}

	virtual unsigned int read_char()
		{
		unsigned char buffer[4];
		unsigned long nread = 0;
		if(ReadFile(m_hf, buffer, 1, &nread, NULL) == 0 || nread == 0)
			return EOF;
		m_current_byte++;
		return buffer[0];
		}

	virtual unsigned int read_int32()
		{
		unsigned char buffer[4];
		unsigned long nread = 0;
		if(ReadFile(m_hf, buffer, 1, &nread, NULL) == 0 || nread < 4)
			return EOF;
		unsigned int result = ((int)buffer[0] << 24) |
						((int)buffer[1] << 16) |
						((int)buffer[2] << 8) |
						((int)buffer[3]);
		m_current_byte += 4;
		return result;
		}

	virtual bool seek(size_t byte)
		{
		m_current_byte = byte;
		if(SetFilePointer(m_hf, byte, 0, FILE_BEGIN) == 0xFFFFFFFF)
			return false;
		return true;
		}

	virtual bool seek_relative(long bytes)
		{
		if(bytes<0 && size_t(-bytes) > m_current_byte)
			{
			m_current_byte = 0;
			seek(0);
			return false;
			}
		m_current_byte += bytes;
		if(m_current_byte>m_total_bytes)
			{
			m_current_byte = m_total_bytes;
			seek(m_total_bytes);
			return false;
			}
		return seek(m_current_byte);
		}

	private:
	HANDLE m_hf;
	void *m_css;
	std::basic_string<TCHAR> m_path;
	size_t m_current_byte;
	size_t m_total_bytes;
	};

#endif // INC_WNDS_MPEG_INPUT_STREAM
