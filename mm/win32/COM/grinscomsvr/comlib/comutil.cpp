#include "stdafx.h"

#include "comutil.h"

void SetComErrorMessage(HRESULT hr)
	{
	LPTSTR pMsgBuf;
	::FormatMessage( 
		FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
		NULL,
		hr,
		MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
		(LPTSTR)&pMsgBuf,
		0,
		NULL);

	//cout << "Error " << hex << hr << " : " << pMsgBuf << endl;
	LocalFree(pMsgBuf) ;
	}
