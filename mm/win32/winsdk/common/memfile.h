#ifndef INC_MEMFILE
#define INC_MEMFILE

#ifndef _WINDOWS_
#include <windows.h>
#endif

#ifndef INC_MEMMAN
#include "memman.h"
#endif

class memfile
	{
	public:
	memfile();
	~memfile();

	bool open(LPCTSTR szFileName);

	BYTE* data() const { return m_begin;}
	DWORD size() const { return m_end - m_begin;}
	DWORD capacity() const { return m_capacity;}
	BYTE* rdata() const {return m_gnext;}
	
	DWORD sizeg() const { return m_end-m_gnext;}
	void seekg(int pos) { m_gnext = m_begin + pos;}
	bool emptyg(){ return m_gnext == m_end;}

	// file type read/write support
	int read(BYTE *b, int nb)
		{
		int nr = m_end - m_gnext;
		int nt = (nr>=nb)?nb:nr;
		if(nt>0)
			{
			memcpy(b, m_gnext, nt);
			m_gnext += nt;
			}
		return nt;
		}

	bool safe_read(BYTE *b, int nb) 
		{ return read(b, nb) == nb;}

	BYTE get_byte()
		{
		if(m_gnext == m_end) throw_range_error();
		return *m_gnext++;
		}

	WORD get_be_ushort()
		{
		BYTE b[2];
		if(!safe_read(b, 2)) throw_range_error();
		return (b[1]<<8)| b[0];
		}

	void skip(int nb)
		{
		int nr = m_end - m_gnext;
		int nt = (nr>=nb)?nb:nr;
		if(nt>0)
			m_gnext += nt;
		if(nt!=nb) throw_range_error();
		}

	private:
	void throw_range_error()
		{
		#ifdef STD_CPP
		throw std::range_error("index out of range");
		#else
		assert(0);
		#endif
		}

	BYTE *m_begin;
	BYTE *m_end;
	DWORD m_capacity;

	// file type read support
	BYTE *m_gnext;
	};

/////////////////////
struct file_reader
	{
	size_t (*read_file)(void *p, void *buf, unsigned long sizeofbuf);

	static size_t read_file_impl(void *p, void *buf, unsigned long sizeofbuf)
		{
		return ((file_reader*)p)->m_mf.read((BYTE*)buf, sizeofbuf);
		}

	file_reader(memfile& mf) : m_mf(mf)
		{
		m_mf.seekg(0);
		read_file = &file_reader::read_file_impl;
		}
	memfile& m_mf;
	};

/////////////////////
inline memfile::memfile()
:	m_begin(0), m_end(0), m_capacity(0),
	m_gnext(0)
	{
	}

inline memfile::~memfile()
	{
	if(m_begin)
		memman::free(m_begin, m_capacity);
	}

inline bool memfile::open(LPCTSTR szFileName)
	{
	HANDLE hf = CreateFile(szFileName,  
		GENERIC_READ,  
		FILE_SHARE_READ,  // 0 = not shared or FILE_SHARE_READ  
		0,  // lpSecurityAttributes 
		OPEN_EXISTING,  
		FILE_ATTRIBUTE_READONLY,  
		NULL); 

	if(hf == INVALID_HANDLE_VALUE) 
		return false;
	
	DWORD dwSize =::GetFileSize(hf, NULL);
	if (dwSize == 0xFFFFFFFF)
		{
		CloseHandle(hf);
		hf = INVALID_HANDLE_VALUE;
		return false;
		}
	m_capacity = dwSize;
	m_gnext = m_begin = memman::alloc(m_capacity);
	if(m_capacity < dwSize)
		return false; // memman::alloc failed
	m_end = m_begin + dwSize;
	DWORD bytesRead = 0;
	if(!ReadFile(hf, m_begin, dwSize, &bytesRead, 0)) 
		return false;
	CloseHandle(hf);
	m_end = m_begin + bytesRead;
	return bytesRead == dwSize;
	}

#endif

