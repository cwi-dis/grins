#ifndef INC_MPEG_INPUT_STREAM
#define INC_MPEG_INPUT_STREAM

#ifndef _INC_TCHAR
#include <tchar.h>
#endif

class mpeg_input_stream
	{
	public:
	virtual ~mpeg_input_stream(){}
	
	virtual void close() = 0;

	virtual bool is_valid() const = 0;
	virtual size_t get_total_bytes() const = 0;
	virtual size_t tell() const = 0;
	virtual bool is_eof() const = 0;
	virtual bool is_bof() const = 0;

	virtual size_t read(unsigned char *buffer, size_t bytes) = 0;
	virtual unsigned int read_char() = 0;
	virtual unsigned int read_int32() = 0;

	virtual bool seek(size_t byte) = 0;
	virtual bool seek_relative(long bytes) = 0;
	};


extern mpeg_input_stream *open_mpeg_input_stream(TCHAR *path);

#endif // INC_MPEG_INPUT_STREAM
