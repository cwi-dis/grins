#include "stdafx.h"

#include "sockapi.h"

bool sockapi::startup()
	{
	WSADATA wsaData;
	WORD wVersionRequested = MAKEWORD(2,0);
	int err = WSAStartup(wVersionRequested,&wsaData);
	if (err!=0) 
		{
		if(err==WSAVERNOTSUPPORTED)
			cout << "WinSock DLL Version is not supported" << endl;
		else if(err==WSASYSNOTREADY)
			cout << "Network not ready" << endl;
		else
			cout << "WSAStartup failed with error code " << err << endl;
		return false;
		}

	int low = (int)LOBYTE(wsaData.wVersion);
	int hi = (int)HIBYTE(wsaData.wVersion);
	//cout << "Using windows sockets version " << low << "." << hi << endl;
	
	if(LOBYTE(wsaData.wVersion) != 2 || HIBYTE(wsaData.wVersion) != 0) 
		{
		cout << "WinSock DLL does not support the version requested. Exiting..." << endl;
		WSACleanup();
		return false; 
		}	
	return true;
	}

void sockapi::cleanup()
	{
	WSACleanup();
	}