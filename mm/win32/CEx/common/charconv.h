
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#ifndef INC_CHARCONV
#define INC_CHARCONV

#ifdef UNICODE

// UNICODE
#define text_strchr wcschr
#define text_strrchr wcsrchr
#define text_strtok wcstok
#define text_strlen wcslen

#else // UNICODE

// MB (not UNICODE)
#define text_strchr strchr
#define text_strrchr strrchr
#define text_strtok strtok
#define text_strlen strlen

#endif // UNICODE

// this class works for both UNICODE and MB
class TextPtr
	{
	public:
	typedef WCHAR* wchar_ptr;
	typedef const WCHAR* const_wchar_ptr;
	
	typedef char* char_ptr;
	typedef const char* const_char_ptr;

	TextPtr(const char *pb) 
	:	m_pcb(pb), m_pcw(NULL), m_pb(NULL), m_pw(NULL), m_length(-1) {}

	TextPtr(const WCHAR *pw) 
	:	m_pcb(NULL), m_pcw(pw), m_pb(NULL), m_pw(NULL), m_length(-1) {}

	~TextPtr()
		{
		if(m_pw != NULL) delete[] m_pw;
		if(m_pb != NULL) delete[] m_pb;
		}
	
	wchar_ptr wstr()
		{
		if(m_pcw != NULL) return const_cast<wchar_ptr>(m_pcw);
		if(m_pw != NULL) return m_pw;
		if(m_pcb == NULL) return NULL;
		m_length = strlen(m_pcb);
		int n = m_length + 1;
		m_pw = new WCHAR[n];
		MultiByteToWideChar(CP_ACP, 0, m_pcb, n, m_pw, n);
		return m_pw;
		}
	const_wchar_ptr c_wstr() { return wstr();}

	char_ptr str()
		{
		if(m_pcb != NULL) return const_cast<char_ptr>(m_pcb);
		if(m_pb != NULL) return m_pb;
		if(m_pcw == NULL) return NULL;
		m_length = wcslen(m_pcw);
		int n = m_length + 1;
		m_pb = new char[n];
		WideCharToMultiByte(CP_ACP, 0, m_pcw, n, m_pb, n, NULL, NULL);
		return m_pb;
		}
	const_char_ptr c_str() { return str();}

	operator wchar_ptr() { return wstr();}
	operator const_wchar_ptr() { return c_wstr();}

	operator char_ptr() { return str();}
	operator const_char_ptr() { return c_str();}

	size_t length() 
		{
		if(m_length>=0) return m_length;
		const_char_ptr pb = (m_pcb!=NULL)?m_pcb:m_pb;
		if(pb != NULL) 
			return (m_length = strlen(pb));
		const_wchar_ptr pw = (m_pcw!=NULL)?m_pcw:m_pw;
		if(pw != NULL) 
			return (m_length = wcslen(pw));
		return (m_length = 0);
		}

	private:
	const_char_ptr m_pcb;
	const_wchar_ptr m_pcw;
	char_ptr m_pb;
	wchar_ptr m_pw;
	int m_length;
	};

#endif  // INC_CHARCONV

