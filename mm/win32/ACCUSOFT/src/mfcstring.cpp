#include <windows.h>
#include <limits.h>

#include "mfcstring.h"

TCHAR afxChNil = '\0';

/////////////////////////////////////////////
int String::initData[] = { -1, 0, 0, 0 };
StringData* String::dataNil = (StringData*)&initData;
LPCTSTR String::pchNil = (LPCTSTR)(((BYTE*)&initData)+sizeof(StringData));

String::String()
	{
	Init();
	}

String::String(const String& stringSrc)
	{
	ASSERT(stringSrc.GetData()->nRefs != 0);
	if (stringSrc.GetData()->nRefs >= 0)
		{
		ASSERT(stringSrc.GetData() != dataNil);
		m_pchData = stringSrc.m_pchData;
		InterlockedIncrement(&GetData()->nRefs);
		}
	else
		{
		Init();
		*this = stringSrc.m_pchData;
		}
	}

String::~String()
	{
	if (GetData() != dataNil)
		{
		if (InterlockedDecrement(&GetData()->nRefs) <= 0)
			delete[] (BYTE*)GetData();
		}
	}

void String::AllocBuffer(int nLen)
	{
	ASSERT(nLen >= 0);
	ASSERT(nLen <= INT_MAX-1);    // max size (enough room for 1 extra)

	if (nLen == 0)
		Init();
	else
		{
		StringData* pData =
			(StringData*)new BYTE[sizeof(StringData) + (nLen+1)*sizeof(TCHAR)];
		pData->nRefs = 1;
		pData->data()[nLen] = '\0';
		pData->nDataLength = nLen;
		pData->nAllocLength = nLen;
		m_pchData = pData->data();
		}
	}

void String::Release()
	{
	if (GetData() != dataNil)
		{
		ASSERT(GetData()->nRefs != 0);
		if (InterlockedDecrement(&GetData()->nRefs) <= 0)
			delete[] (BYTE*)GetData();
		Init();
		}
	}	

void PASCAL String::Release(StringData* pData)
	{
	if (pData != dataNil)
		{
		ASSERT(pData->nRefs != 0);
		if (InterlockedDecrement(&pData->nRefs) <= 0)
			delete[] (BYTE*)pData;
		}
	}

void String::Empty()
	{
	if (GetData()->nDataLength == 0)
		return;
	if (GetData()->nRefs >= 0)
		Release();
	else
		*this = &afxChNil;
	ASSERT(GetData()->nDataLength == 0);
	ASSERT(GetData()->nRefs < 0 || GetData()->nAllocLength == 0);
	}

void String::AllocCopy(String& dest, int nCopyLen, int nCopyIndex,int nExtraLen) const
	{
	int nNewLen = nCopyLen + nExtraLen;
	if (nNewLen == 0)
		{
		dest.Init();
		}
	else
		{
		dest.AllocBuffer(nNewLen);
		memcpy(dest.m_pchData, m_pchData+nCopyIndex, nCopyLen*sizeof(TCHAR));
		}
	}
void String::AllocBeforeWrite(int nLen)
{
	if (GetData()->nRefs > 1 || nLen > GetData()->nAllocLength)
	{
		Release();
		AllocBuffer(nLen);
	}
	ASSERT(GetData()->nRefs <= 1);
}

String::String(LPCTSTR lpsz)
	{
	Init();
	int nLen = SafeStrlen(lpsz);
	if (nLen != 0)
		{
		AllocBuffer(nLen);
		memcpy(m_pchData, lpsz, nLen*sizeof(TCHAR));
		}
	}

//////////////////////////////////////////////////////////////////////////////
// Assignment operators
//  All assign a new value to the string
//      (a) first see if the buffer is big enough
//      (b) if enough room, copy on top of old buffer, set size and type
//      (c) otherwise free old string data, and create a new one
//
//  All routines return the new string (but as a 'const String&' so that
//      assigning it again will cause a copy, eg: s1 = s2 = "hi there".
//

void String::AssignCopy(int nSrcLen, LPCTSTR lpszSrcData)
	{
	AllocBeforeWrite(nSrcLen);
	memcpy(m_pchData, lpszSrcData, nSrcLen*sizeof(TCHAR));
	GetData()->nDataLength = nSrcLen;
	m_pchData[nSrcLen] = '\0';
	}

const String& String::operator=(const String& stringSrc)
	{
	if (m_pchData != stringSrc.m_pchData)
		{
		if ((GetData()->nRefs < 0 && GetData() != dataNil) ||
			stringSrc.GetData()->nRefs < 0)
			{
			// actual copy necessary since one of the strings is locked
			AssignCopy(stringSrc.GetData()->nDataLength, stringSrc.m_pchData);
			}
		else
			{
			// can just copy references around
			Release();
			ASSERT(stringSrc.GetData() != dataNil);
			m_pchData = stringSrc.m_pchData;
			InterlockedIncrement(&GetData()->nRefs);
			}
		}
	return *this;
	}

const String& String::operator=(LPCTSTR lpsz)
	{
	ASSERT(lpsz != NULL);
	AssignCopy(SafeStrlen(lpsz), lpsz);
	return *this;
	}

//////////
void String::ConcatCopy(int nSrc1Len, LPCTSTR lpszSrc1Data,
	int nSrc2Len, LPCTSTR lpszSrc2Data)
{
  // -- master concatenation routine
  // Concatenate two sources
  // -- assume that 'this' is a new CString object

	int nNewLen = nSrc1Len + nSrc2Len;
	if (nNewLen != 0)
	{
		AllocBuffer(nNewLen);
		memcpy(m_pchData, lpszSrc1Data, nSrc1Len*sizeof(TCHAR));
		memcpy(m_pchData+nSrc1Len, lpszSrc2Data, nSrc2Len*sizeof(TCHAR));
	}
}

String operator+(const String& string1, const String& string2)
{
	String s;
	s.ConcatCopy(string1.GetData()->nDataLength, string1.m_pchData,
		string2.GetData()->nDataLength, string2.m_pchData);
	return s;
}

String operator+(const String& string, LPCTSTR lpsz)
{
	ASSERT(lpsz != NULL);
	String s;
	s.ConcatCopy(string.GetData()->nDataLength, string.m_pchData,
		String::SafeStrlen(lpsz), lpsz);
	return s;
}

String operator+(LPCTSTR lpsz, const String& string)
{
	ASSERT(lpsz != NULL);
	String s;
	s.ConcatCopy(String::SafeStrlen(lpsz), lpsz, string.GetData()->nDataLength,
		string.m_pchData);
	return s;
}
