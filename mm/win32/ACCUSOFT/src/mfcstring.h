#ifndef INC_MFCSTRING
#define INC_MFCSTRING

#include <TCHAR.H>

#include <assert.h>
#define ASSERT assert


class CArchive;
class CDumpContext;

struct StringData
	{
	long nRefs;     
	int nDataLength;
	int nAllocLength;
	TCHAR* data()
		{ return (TCHAR*)(this+1); }
	};

class String
	{
	public:
	String();
	String(const String& stringSrc);
	String(TCHAR ch, int nRepeat = 1);
	String(LPCSTR lpsz);
	String(LPCWSTR lpsz);
	String(LPCTSTR lpch, int nLength);
	String(const unsigned char* psz);

	// Attributes & Operations
	// as an array of characters
	int GetLength() const;
	BOOL IsEmpty() const;
	void Empty();                       // free up the data

	TCHAR GetAt(int nIndex) const;      // 0 based
	TCHAR operator[](int nIndex) const; // same as GetAt
	void SetAt(int nIndex, TCHAR ch);
	operator LPCTSTR() const;           // as a C string

	// overloaded assignment
	const String& operator=(const String& stringSrc);
	const String& operator=(TCHAR ch);
#ifdef _UNICODE
	const String& operator=(char ch);
#endif
	const String& operator=(LPCSTR lpsz);
	const String& operator=(LPCWSTR lpsz);
	const String& operator=(const unsigned char* psz);

	// string concatenation
	const String& operator+=(const String& string);
	const String& operator+=(TCHAR ch);
#ifdef _UNICODE
	const String& operator+=(char ch);
#endif
	const String& operator+=(LPCTSTR lpsz);

	friend String  operator+(const String& string1,
			const String& string2);
	friend String  operator+(const String& string, TCHAR ch);
	friend String  operator+(TCHAR ch, const String& string);
#ifdef _UNICODE
	friend String  operator+(const String& string, char ch);
	friend String  operator+(char ch, const String& string);
#endif
	friend String  operator+(const String& string, LPCTSTR lpsz);
	friend String  operator+(LPCTSTR lpsz, const String& string);

	// string comparison
	int Compare(LPCTSTR lpsz) const;         // straight character
	int CompareNoCase(LPCTSTR lpsz) const;   // ignore case
	int Collate(LPCTSTR lpsz) const;         // NLS aware

	// simple sub-string extraction
	String Mid(int nFirst, int nCount) const;
	String Mid(int nFirst) const;
	String Left(int nCount) const;
	String Right(int nCount) const;

	String SpanIncluding(LPCTSTR lpszCharSet) const;
	String SpanExcluding(LPCTSTR lpszCharSet) const;

	// upper/lower/reverse conversion
	void MakeUpper();
	void MakeLower();
	void MakeReverse();

	// trimming whitespace (either side)
	void TrimRight();
	void TrimLeft();

	// searching (return starting index, or -1 if not found)
	// look for a single character match
	int Find(TCHAR ch) const;               // like "C" strchr
	int ReverseFind(TCHAR ch) const;
	int FindOneOf(LPCTSTR lpszCharSet) const;

	// look for a specific sub-string
	int Find(LPCTSTR lpszSub) const;        // like "C" strstr

	// simple formatting
	void __cdecl Format(LPCTSTR lpszFormat, ...);
	void __cdecl Format(UINT nFormatID, ...);

#ifndef _MAC
	// formatting for localization (uses FormatMessage API)
	void __cdecl FormatMessage(LPCTSTR lpszFormat, ...);
	void __cdecl FormatMessage(UINT nFormatID, ...);
#endif

	// input and output
#ifdef _DEBUG
	friend CDumpContext&  operator<<(CDumpContext& dc,
				const String& string);
#endif
	friend CArchive&  operator<<(CArchive& ar, const String& string);
	friend CArchive&  operator>>(CArchive& ar, String& string);

	// Windows support
	BOOL LoadString(UINT nID);          // load from string resource
										// 255 chars max
#ifndef _UNICODE
	// ANSI <-> OEM support (convert string in place)
	void AnsiToOem();
	void OemToAnsi();
#endif

#ifndef _AFX_NO_BSTR_SUPPORT
	// OLE BSTR support (use for OLE automation)
	BSTR AllocSysString() const;
	BSTR SetSysString(BSTR* pbstr) const;
#endif

	// Access to string implementation buffer as "C" character array
	LPTSTR GetBuffer(int nMinBufLength);
	void ReleaseBuffer(int nNewLength = -1);
	LPTSTR GetBufferSetLength(int nNewLength);
	void FreeExtra();

	// Use LockBuffer/UnlockBuffer to turn refcounting off
	LPTSTR LockBuffer();
	void UnlockBuffer();

// Implementation
public:
	~String();
	int GetAllocLength() const;

protected:
	LPTSTR m_pchData;   // pointer to ref counted string data

	// implementation helpers
	StringData* GetData() const;
	void Init();
	void AllocCopy(String& dest, int nCopyLen, int nCopyIndex, int nExtraLen) const;
	void AllocBuffer(int nLen);
	void AssignCopy(int nSrcLen, LPCTSTR lpszSrcData);
	void ConcatCopy(int nSrc1Len, LPCTSTR lpszSrc1Data, int nSrc2Len, LPCTSTR lpszSrc2Data);
	void ConcatInPlace(int nSrcLen, LPCTSTR lpszSrcData);
	void FormatV(LPCTSTR lpszFormat, va_list argList);
	void CopyBeforeWrite();
	void AllocBeforeWrite(int nLen);
	void Release();
	static void PASCAL Release(StringData* pData);
	static int PASCAL SafeStrlen(LPCTSTR lpsz);

	
	static int initData[];
	static StringData* dataNil;
	static LPCTSTR pchNil;
	static const String& GetEmptyString()
		{return *(String*)&pchNil;}

	};

inline StringData* String::GetData() const
	{ ASSERT(m_pchData != NULL); return ((StringData*)m_pchData)-1; }
inline void String::Init()
	{ m_pchData = GetEmptyString().m_pchData; }
inline String::String(const unsigned char* lpsz)
	{ Init(); *this = (LPCSTR)lpsz; }
inline int String::GetLength() const
	{ return GetData()->nDataLength; }
inline int String::GetAllocLength() const
	{ return GetData()->nAllocLength; }
inline BOOL String::IsEmpty() const
	{ return GetData()->nDataLength == 0; }
inline String::operator LPCTSTR() const
	{ return m_pchData; }
inline const String& String::operator=(const unsigned char* lpsz)
	{ *this = (LPCSTR)lpsz; return *this; }
#ifdef _UNICODE
inline const String& String::operator+=(char ch)
	{ *this += (TCHAR)ch; return *this; }
inline const String& String::operator=(char ch)
	{ *this = (TCHAR)ch; return *this; }
inline String operator+(const String& string, char ch)
	{ return string + (TCHAR)ch; }
inline String operator+(char ch, const String& string)
	{ return (TCHAR)ch + string; }
#endif

inline int PASCAL String::SafeStrlen(LPCTSTR lpsz)
	{ return (lpsz == NULL) ? 0 : lstrlen(lpsz); }

// String support (windows specific)
inline int String::Compare(LPCTSTR lpsz) const
	{ return _tcscmp(m_pchData, lpsz); }    // MBCS/Unicode aware
inline int String::CompareNoCase(LPCTSTR lpsz) const
	{ return _tcsicmp(m_pchData, lpsz); }   // MBCS/Unicode aware
// String::Collate is often slower than Compare but is MBSC/Unicode
//  aware as well as locale-sensitive with respect to sort order.
inline int String::Collate(LPCTSTR lpsz) const
	{ return _tcscoll(m_pchData, lpsz); }   // locale sensitive

inline TCHAR String::GetAt(int nIndex) const
	{
	ASSERT(nIndex >= 0);
	ASSERT(nIndex < GetData()->nDataLength);
	return m_pchData[nIndex];
	}
inline TCHAR String::operator[](int nIndex) const
	{
	// same as GetAt
	ASSERT(nIndex >= 0);
	ASSERT(nIndex < GetData()->nDataLength);
	return m_pchData[nIndex];
	}
inline bool operator==(const String& s1, const String& s2)
	{ return s1.Compare(s2) == 0; }
inline bool operator==(const String& s1, LPCTSTR s2)
	{ return s1.Compare(s2) == 0; }
inline bool operator==(LPCTSTR s1, const String& s2)
	{ return s2.Compare(s1) == 0; }
inline bool operator!=(const String& s1, const String& s2)
	{ return s1.Compare(s2) != 0; }
inline bool operator!=(const String& s1, LPCTSTR s2)
	{ return s1.Compare(s2) != 0; }
inline bool operator!=(LPCTSTR s1, const String& s2)
	{ return s2.Compare(s1) != 0; }
inline bool operator<(const String& s1, const String& s2)
	{ return s1.Compare(s2) < 0; }
inline bool operator<(const String& s1, LPCTSTR s2)
	{ return s1.Compare(s2) < 0; }
inline bool operator<(LPCTSTR s1, const String& s2)
	{ return s2.Compare(s1) > 0; }
inline bool operator>(const String& s1, const String& s2)
	{ return s1.Compare(s2) > 0; }
inline bool operator>(const String& s1, LPCTSTR s2)
	{ return s1.Compare(s2) > 0; }
inline bool operator>(LPCTSTR s1, const String& s2)
	{ return s2.Compare(s1) < 0; }
inline bool operator<=(const String& s1, const String& s2)
	{ return s1.Compare(s2) <= 0; }
inline bool operator<=(const String& s1, LPCTSTR s2)
	{ return s1.Compare(s2) <= 0; }
inline bool operator<=(LPCTSTR s1, const String& s2)
	{ return s2.Compare(s1) >= 0; }
inline bool operator>=(const String& s1, const String& s2)
	{ return s1.Compare(s2) >= 0; }
inline bool operator>=(const String& s1, LPCTSTR s2)
	{ return s1.Compare(s2) >= 0; }
inline bool operator>=(LPCTSTR s1, const String& s2)
	{ return s2.Compare(s1) <= 0; }

#endif
