/****************************************************************************
 * 
 *  $Id$
 *
 *  Copyright (C) 1995,1996,1997 RealNetworks, Inc.
 *  All rights reserved.
 *
 *  http://www.real.com/devzone
 *
 *  This program contains proprietary information of RealNetworks, Inc.,
 *  and is licensed subject to restrictions on use and distribution.
 *
 *  Operating System Dependant defines, functions, and includes
 *
 */

#include "os.h"

int 
stricmp(const char *first, const char *last)
{ 
	int f=0,l=0;
	do 
	{
		if ( ((f = (unsigned char) (*(first++))) >= 'A') &&
				(f <= 'Z') )
			f -= 'A' - 'a';
			
		if ( ((l = (unsigned char) (*(last++))) >= 'A') &&
				(l <= 'Z') )
			l -= 'A' - 'a';
	} while (f && (f == l) );
	return ( f - l );
}

int
strnicmp(const char *first, const char *last, size_t count) 
{
	int f,l;
	if (count)
	{
		do 
		{
			if ( ((f = (unsigned char) (*(first++))) >= 'A') &&
					(f <= 'Z') )
				f -= 'A' - 'a';
				
			if ( ((l = (unsigned char) (*(last++))) >= 'A') &&
					(l <= 'Z') )
				l -= 'A' - 'a';
		} while ( --count && f && (f == l) );
		return ( f - l );
	}
	return 0;
}

/////////////////////////////////////////////////////////////////////////////
//
//	Function:
//
//		LoadLibrary()
//
//	Purpose:
//
//		Called to load a Mac Shared Library given the library's fragment name.
//
//	Parameters:
//
//		char* dllname
//		The fragment name of the library.
//
//	Return:
//
//		ULONG32
//		Returns the ConnectionID
//
HINSTANCE LoadLibrary(const char* dllname)
{
	CFragConnectionID	connID = 0; //reference ID to shared lib
	Ptr			mainAddr = nil;
	Str255 			errMsg;
	FSSpec			fileSpec;
	Boolean			tmpBool = false;
	OSErr			theErr;
	Str255			strLibName;

	strcpy((char*)&strLibName[1], dllname);
	strLibName[0] = strlen(dllname);
	theErr = FSMakeFSSpec (0, 0, strLibName, &fileSpec);
	theErr = ResolveAliasFile (&fileSpec, true, &tmpBool, &tmpBool);
	theErr = GetDiskFragment (&fileSpec, 0, kCFragGoesToEOF, fileSpec.name, kLoadCFrag, &connID, &mainAddr, errMsg);
	if (theErr)
	{
	    theErr = GetSharedLibrary (fileSpec.name, kPowerPCCFragArch, kLoadCFrag, &connID, &mainAddr, errMsg);
	}

	return (HINSTANCE)connID;
}

/////////////////////////////////////////////////////////////////////////////
//
//	Function:
//
//		FreeLibrary()
//
//	Purpose:
//
//		Called to free a Mac Shared Library. If this is not called the library
//		will be freed when the application quits.
//
//	Parameters:
//
//		HMODULE lib
//		This is actually the ConnectionID.
//
//	Return:
//
//		none
//
void FreeLibrary(HINSTANCE lib)
{
	CFragConnectionID	connID = (CFragConnectionID)lib;

	CloseConnection(&connID);
}


/////////////////////////////////////////////////////////////////////////////
//
//	Function:
//
//		GetProcAddress()
//
//	Purpose:
//
//		Called to get a function pointer in a Mac Shared Library.
//
//	Parameters:
//
//		HMODULE lib
//		This is the ConnectionID that is returned from LoadLibrary
//
//		char* function
//		The function name
//
//	Return:
//
//		void*
//		The address of the function.
//
void* GetProcAddress(HMODULE lib, char* function)
{
	OSErr err;
	Ptr					symAddr = nil;
	CFragSymbolClass	symClass;
	CFragConnectionID	connID = (CFragConnectionID)lib;
	
	Str255 strFuncName;
	strcpy((char *)&strFuncName[1], function);
	strFuncName[0] = strlen(function);


//		FindSymbol doesn't actually return the address of the function;
//		it returns a pointer to a TOC entry in the code fragment
	err = FindSymbol(connID, (ConstStr63Param)((Str255*)strFuncName), &symAddr, &symClass);

	return symAddr;
}
