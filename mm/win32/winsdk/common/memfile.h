#ifndef INC_MEMFILE
#define INC_MEMFILE

#ifndef _WINDOWS_
#include <windows.h>
#endif

class memfile
	{
	public:
	memfile();
	~memfile();

	// file-mem and mem-file transfer
	bool open(LPCTSTR szFileName);

	bool fillBuffer(DWORD nRead);
	bool fill();

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

	int write(const BYTE *b, int nb)
   		{
		memcpy(m_pnext, b, nb);
		m_gnext += nb;
		return nb;
		}
	int write(int v){return write((BYTE*)&v, sizeof(int));}

	HANDLE get_handle() const { return m_hf;}
	void reset_file_pointer() 
		{ 
		//assert(m_hf != INVALID_HANDLE_VALUE); 
		SetFilePointer(m_hf, 0, NULL, FILE_BEGIN);
		}

	private:
	void throw_range_error()
		{
		#ifdef STD_CPP
		throw std::range_error("index out of range");
		#else
		//throw "index out of range";
		#endif
		}
	void reserve(DWORD dwBytes);

	BYTE *m_begin;
	BYTE *m_end;
	DWORD m_capacity;

	// file type read support
	BYTE *m_gnext;

	// file type write support
	BYTE *m_pnext;

	// in place processing
	HANDLE m_hf;
	TCHAR *m_pfname;
	};

inline memfile::memfile():
	m_begin(NULL), m_end(NULL),
	m_capacity(0),
	m_gnext(NULL),
	m_pnext(NULL),
	m_hf(INVALID_HANDLE_VALUE)
	{
	}

inline memfile::~memfile()
	{
	if(m_hf != INVALID_HANDLE_VALUE)
		CloseHandle(m_hf);

	if(m_begin)
		::HeapFree(GetProcessHeap(), 0, m_begin);

	if(m_pfname)
		delete[] m_pfname;
	}

inline void memfile::reserve(DWORD dwBytes)
	{
	if(m_begin==NULL)
		{
		m_begin= (BYTE*)::HeapAlloc(GetProcessHeap(), 0, dwBytes);
		//assert(m_begin != NULL);
		m_capacity= ::HeapSize(GetProcessHeap(), 0, m_begin);
		}
	else
		{
		if(dwBytes>m_capacity)
			{
			m_begin = (BYTE*)::HeapReAlloc(GetProcessHeap(), 0, m_begin, dwBytes); 
			m_capacity = ::HeapSize(GetProcessHeap(), 0, m_begin);
			}
		}
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
	
	// keep a copy of filename
	m_pfname = new TCHAR[lstrlen(szFileName)+1];
	lstrcpy(m_pfname, szFileName);

	DWORD dwSize =::GetFileSize(hf, NULL);
	if (dwSize == 0xFFFFFFFF)
		{
		CloseHandle(hf);
		hf = INVALID_HANDLE_VALUE;
		return false;
		}
	m_hf = hf;
	reserve(dwSize);
	m_pnext = m_gnext = m_begin;
	m_end = m_begin + dwSize;
	return true;
	}

inline bool memfile::fillBuffer(DWORD nRead)
	{
	DWORD bytesRead = 0;
	if(!ReadFile(m_hf, m_pnext, nRead, &bytesRead, 0)) 
		return false;
	m_pnext += bytesRead;
	return nRead == bytesRead;
	}

inline bool memfile::fill()
	{
	DWORD nRead = m_end - m_pnext;
	DWORD bytesRead = 0;
	if(!ReadFile(m_hf, m_pnext, nRead, &bytesRead, 0)) 
		return false;
	m_pnext += bytesRead;
	return nRead == bytesRead;
	}

#endif

