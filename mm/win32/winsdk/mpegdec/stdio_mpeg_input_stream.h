#ifndef INC_STDIO_MPEG_INPUT_STREAM
#define INC_STDIO_MPEG_INPUT_STREAM

#ifndef INC_MPEG_INPUT_STREAM
#include "mpeg_input_stream.h"
#endif

#ifndef _INC_STDIO
#include <stdio.h>
#endif

#ifndef _INC_TCHAR
#include <tchar.h>
#endif

#ifndef _STRING_
#include <string>
#endif

class stdio_mpeg_input_stream : public mpeg_input_stream
	{
	public:
	stdio_mpeg_input_stream(TCHAR *path)
	:	m_fd(NULL), m_css(NULL), m_path(path), m_current_byte(0), m_total_bytes(0)
		{
		m_fd = _tfopen(path, TEXT("rb"));
		if(m_fd != NULL)
			{
			fseek(m_fd, 0, SEEK_END);
			m_total_bytes = ftell(m_fd);
			fseek(m_fd, 0, SEEK_SET);
			if(m_total_bytes == 0)
				{
				fclose(m_fd);
				m_fd = NULL;
				}
			}
		}

	virtual ~stdio_mpeg_input_stream()
		{
		if(m_css != NULL) delete m_css;
		if(m_fd != NULL)
			fclose(m_fd);
		}

	virtual bool is_valid() const { return m_fd != NULL;}
	virtual size_t get_total_bytes() const { return m_total_bytes;}
	virtual size_t tell() const { return m_current_byte;}
	virtual bool is_eof() const { return m_current_byte >= m_total_bytes;}
	virtual bool is_bof() const { return m_current_byte == 0;}

	virtual void close()
		{
		//_tprintf(TEXT("close_mpeg_input_stream\n"));
		if(m_fd != NULL)
			{
			fclose(m_fd);
			m_total_bytes = 0;
			m_fd = NULL;
			}
		}

	virtual size_t read(unsigned char *buffer, size_t bytes)
		{
		size_t nread = fread(buffer, 1, bytes, m_fd);
		m_current_byte += nread;
		return nread;
		}

	virtual unsigned int read_char()
		{
		m_current_byte++;
		return fgetc(m_fd);
		}

	virtual unsigned int read_int32()
		{
		int a = (unsigned char)fgetc(m_fd);
		int b = (unsigned char)fgetc(m_fd);
		int c = (unsigned char)fgetc(m_fd);
		int d = (unsigned char)fgetc(m_fd);
		unsigned int result = ((int)a << 24) |
						((int)b << 16) |
						((int)c << 8) |
						((int)d);
		m_current_byte += 4;
		return result;
		}

	virtual bool seek(size_t byte)
		{
		m_current_byte = byte;
		return (fseek(m_fd, byte, SEEK_SET) == 0);
		}

	virtual bool seek_relative(long bytes)
		{
		if(bytes<0 && size_t(-bytes) > m_current_byte)
			{
			m_current_byte = 0;
			fseek(m_fd, 0, SEEK_SET);
			return false;
			}
		m_current_byte += bytes;
		if(m_current_byte>m_total_bytes)
			{
			m_current_byte = m_total_bytes;
			fseek(m_fd, m_total_bytes, SEEK_SET);
			return false;
			}
		return (fseek(m_fd, m_current_byte, SEEK_SET) == 0);
		}

	private:
	FILE *m_fd;
	void *m_css;
	std::basic_string<TCHAR> m_path;
	size_t m_current_byte;
	size_t m_total_bytes;
	};

#endif // INC_STDIO_MPEG_INPUT_STREAM
