/****************************************************************************
 * 
 *	rmaedit.h
 *
 *	$Id$
 *
 *  Copyright (C) 1998,1999 RealNetworks.
 *  All rights reserved.
 *  
 *  http://www.real.com/devzone
 *
 *  This program contains proprietary information of RealNetworks, Inc., 
 *  and is licensed subject to restrictions on use and distribution.
 *
 *
 *  Main interfaces used for the RealProducer G2 RMEditor SDK.
 */

#ifndef _RMAEDIT_H_
#define _RMAEDIT_H_

struct	IRMAValues;
struct	IRMAPacket;
struct  IRMABuffer;

/*
 * Forward declarations of some interfaces defined here-in.
 */

typedef _INTERFACE IRMARMFileSink			IRMARMFileSink;

/****************************************************************************
 *  Function:
 *		RMACreateRMEdit
 *
 *  Purpose:
 *		Creates an instance of a G2 RMEditor object. 
 */
STDAPI RMACreateRMEdit(IUnknown**  /*OUT*/	ppIUnknown);

typedef PN_RESULT (PNEXPORT_PTR FPCREATEINSTANCE) (IUnknown** /*OUT*/ ppIUnknown);

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMARMEdit
 *
 *  Purpose:
 *
 *	Interface to G2 RMEditor module
 *
 *  IRMARMEdit
 *
 *  {7010AF10-0B86-11d2-A1BD-0060083BE563}
 *
 */

DEFINE_GUID(IID_IRMARMEdit, 
0x7010af10, 0xb86, 0x11d2, 0xa1, 0xbd, 0x0, 0x60, 0x8, 0x3b, 0xe5, 0x63);


#define CLSID_IRMARMEdit IID_IRMARMEdit

#undef  INTERFACE
#define INTERFACE   IRMARMEdit

DECLARE_INTERFACE_(IRMARMEdit, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(ULONG32,AddRef)	(THIS) PURE;

    STDMETHOD_(ULONG32,Release)	(THIS) PURE;

    /***********************************************************************/
    /*
     *	IRMARMEdit methods
     */
 
    /************************************************************************
     *	Method:
     *	    IRMARMEdit::GetFileVersion
     *	Purpose:
     *	    returns the version number of the input file. 
     *		1 == .rm1 file (Single Rate)
     *		2 == .rm2 file (Sure Stream)
     *
     *	Parameters:
     *	    pulVersion - [out] address of UINT32 that will hold the version
     */
	STDMETHOD(GetFileVersion) (THIS_
				UINT32* pulVersion) PURE;                   

    /************************************************************************
     *	Method:
     *	    IRMARMEdit::GetErrorString
     *	Purpose:
     *	    returns the error string associated with the specified PN_RESULT
     *
     *	Parameters:
     *	    res - [in] the PN_RESULT you want an error string for
     *		szErrString - [out] a preallocated buffer to hold the error string
     *		unMaxSize - the size of the szErrString buffer
     */
	STDMETHOD(GetErrorString) (THIS_
				PN_RESULT res, char* szErrString, UINT16 unMaxSize) PURE;                   

    /************************************************************************
     *	Method:
     *	    IRMARMEdit::SetTitle
     *	Purpose:
     *	    sets the title string
     *
     *	Parameters:
     *		szTitle - [in] the Title string for the file
     */
	STDMETHOD(SetTitle) (THIS_
				const char* szTitle) PURE;                   

    /************************************************************************
     *	Method:
     *	    IRMARMEdit::SetAuthor
     *	Purpose:
     *	    sets the author string
     *
     *	Parameters:
     *		szAuthor - [in] the Author string for the file
     */
	STDMETHOD(SetAuthor) (THIS_
				const char* szAuthor) PURE;                   

    /************************************************************************
     *	Method:
     *	    IRMARMEdit::SetCopyright
     *	Purpose:
     *	    sets the copyright string
     *
     *	Parameters:
     *		szCopyright - [in] the Copyright string for the file
     */
	STDMETHOD(SetCopyright) (THIS_
				const char* szCopyright) PURE;                   

    /************************************************************************
     *	Method:
     *	    IRMARMEdit::SetComment
     *	Purpose:
     *	    sets the comment string
     *
     *	Parameters:
     *		szComment - [in] the Comment string for the file
     */
	STDMETHOD(SetComment) (THIS_
				const char* szComment) PURE;                   

    /************************************************************************
     *	Method:
     *	    IRMARMEdit::SetSelectiveRecord
     *	Purpose:
     *	    enables/disables the Selective Record (Allow Recording) flag
     *
     *	Parameters:
     *		bEnable - [in] TRUE enable Allow Recording
     *					   FALSE disable Allow Recording 
	 */
	STDMETHOD(SetSelectiveRecord) (THIS_
				BOOL bEnable) PURE;                   

    /************************************************************************
     *	Method:
     *	    IRMARMEdit::SetMobilePlayback
     *	Purpose:
     *	    enables/disables the Mobile Playback (Allow Download) flag
     *
     *	Parameters:
     *		bEnable - [in] TRUE enable Allow Download
     *					   FALSE disable Allow Download 
	 */
	STDMETHOD(SetMobilePlayback) (THIS_
				BOOL bEnable) PURE;                   

    /************************************************************************
     *	Method:
     *	    IRMARMEdit::SetPerfectPlay
     *	Purpose:
     *	    enables/disables the Perfect Play (Buffered Playback) flag
     *
     *	Parameters:
     *		bEnable - [in] TRUE enable Buffered Playback
     *					   FALSE disable Buffered Playback 
	 */
	STDMETHOD(SetPerfectPlay) (THIS_
				BOOL bEnable) PURE;                   

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::SetStartTime
     *	Purpose:
     *	    specifes the start time in milliseconds for the edit operation.
     *
     *	Parameters:
     *		ulStartTime - [in] the start time in milliseconds.
	 *
	 *  Note: If you do not call this method, the default start time will be
	 *		  start of the file.
	 */
	STDMETHOD(SetStartTime) (THIS_
				UINT32 ulStartTime) PURE;             

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::SetStartTime
     *	Purpose:
     *	    specifes the start time in Days:Hours:Minutes:Seconds:Milliseconds format
	 *	    for the edit operation.
     *
     *	Parameters:
     *		szStartTime - [in] the start time in Days:Hours:Minutes:Seconds:Milliseconds format.
	 *		i.e. 0:0:0:0:0
	 *
	 *  Note: If you do not call this method, the default start time will be
	 *		  start of the file.
	 */
	STDMETHOD(SetStartTime) (THIS_
				const char* szStartTime) PURE;             

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::SetEndTime
     *	Purpose:
     *	    specifes the end time in milliseconds for the edit operation.
     *
     *	Parameters:
     *		ulEndTime - [in] the end time in milliseconds.
	 *
	 *  Note: If you do not call this method, the default end time will be
	 *		  the end of the file (EOF).
	 */
	STDMETHOD(SetEndTime) (THIS_
				UINT32 ulEndTime) PURE;                 

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::SetEndTime
     *	Purpose:
     *	    specifes the end time in Days:Hours:Minutes:Seconds:Milliseconds format
	 *	    for the edit operation.
     *
     *	Parameters:
     *		szEndTime - [in] the end time in Days:Hours:Minutes:Seconds:Milliseconds format.
	 *		i.e. 0:0:0:0:0
	 *
	 *  Note: If you do not call this method, the default end time will be
	 *		  the end of the file (EOF).
	 */	
	STDMETHOD(SetEndTime) (THIS_
				const char* szEndTime) PURE;             

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::SetInputFile
     *	Purpose:
     *	    specifies the file name of the input .rm file. If you are pasting several
	 *		.rm files, call SetInputFile() with the name of the first file and AddInputFile()
	 *		for the remaining files.
     *
     *	Parameters:
     *		szFileName - [in] the path to the input file.
	 *		bLoadFileInfo - [in] Set bLoadFileInfo to TRUE if you want the Edit SDK to load the 
	 *		input file's Content info (Title, Author, Copyright, Comment) and Property Flags 
	 *		(Selective Record, Mobile Play, etc.) You can then access this info using the 
	 *		Get methods (i.e. GetTitle(), etc.)
	 */	
	STDMETHOD(SetInputFile) (THIS_
				const char* szFileName,BOOL bLoadFileInfo) PURE;  

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::AddInputFile
     *	Purpose:
     *	    specifies the file name of a .rm file to paste to the end of the input file
	 *		specified in SetInputFile().SetInputFile() should be called before this method.
     *
     *	Parameters:
     *		szFileName - [in] the path to the .rm file to be pasted to the end of the file
	 *		specified with SetInputFile().
	 */	
	STDMETHOD(AddInputFile) (THIS_
				const char* szFileName) PURE;  

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::SetOutputFile
     *	Purpose:
     *	    specifies the file name of the output file. This .rm file will contain the results
	 *		of the edit operation.
     *
     *	Parameters:
     *		szFileName - [in] the path to the output .rm file. If the file already exists, it 
	 *		will be replaced. If the file does not exist it will be created.
	 */	
	STDMETHOD(SetOutputFile) (THIS_
				const char* szFileName) PURE; 

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::GetTitle
     *	Purpose:
     *	    returns the current title string.
     *
     *	Parameters:
     *		szTitle - [out] the title string will be returned in szTitle. szTitle must be 
	 *		preallocated by the caller.
	 *		ulSize - [in] the size of the szTitle buffer.
	 */	
	STDMETHOD(GetTitle) (THIS_
				char* szTitle, UINT32 ulSize) PURE; 

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::GetAuthor
     *	Purpose:
     *	    returns the current author string.
     *
     *	Parameters:
     *		szAuthor - [out] the author string will be returned in szAuthor. szAuthor must be 
	 *		preallocated by the caller.
	 *		ulSize - [in] the size of the szAuthor buffer.
	 */	
	STDMETHOD(GetAuthor) (THIS_
				char* szAuthor, UINT32 ulSize) PURE; 

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::GetCopyright
     *	Purpose:
     *	    returns the current copyright string.
     *
     *	Parameters:
     *		szAuthor - [out] the Copyright string will be returned in szCopyright. szCopyright must be 
	 *		preallocated by the caller.
	 *		ulSize - [in] the size of the szCopyright buffer.
	 */	
	STDMETHOD(GetCopyright) (THIS_
				char* szCopyright, UINT32 ulSize) PURE; 

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::GetComment
     *	Purpose:
     *	    returns the current comment string.
     *
     *	Parameters:
     *		szComment - [out] the Comment string will be returned in szComment. szComment must be 
	 *		preallocated by the caller.
	 *		ulSize - [in] the size of the szComment buffer.
	 */	
	STDMETHOD(GetComment) (THIS_
				char* szComment, UINT32 ulSize) PURE; 

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::GetSelectiveRecord
     *	Purpose:
     *	    returns the returns the current state of the Selective Record 
	 *		(Allow Recording) flag.
     *
     *	Parameters:
     *		bEnabled - [out] the state of the selective record flag will be returned in bEnabled. 
	 */	
	STDMETHOD(GetSelectiveRecord) (THIS_
				BOOL* bEnabled) PURE;                   

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::GetMobilePlayback
     *	Purpose:
     *	    returns the returns the current state of the Mobile Playback
	 *		(Allow Download) flag.
	 *
     *	Parameters:
     *		bEnabled - [out] the state of the mobile playback flag will be returned in bEnabled. 
	 */	
	STDMETHOD(GetMobilePlayback) (THIS_
				BOOL* bEnabled) PURE;                   

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::GetPerfectPlay
     *	Purpose:
     *	    returns the returns the current state of the PerfectPlay
	 *		(Buffered Playback) flag.
	 *
     *	Parameters:
     *		bEnabled - [out] the state of the PerfectPlay flag will be returned in bEnabled. 
	 */	
	STDMETHOD(GetPerfectPlay) (THIS_
				BOOL* bEnabled) PURE;                   

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::GetStartTime
     *	Purpose:
     *	    returns the current start time in milliseconds
	 *
     *	Parameters:
     *		pulStartTime - [out] the current start time will be returned in pulStartTime. 
	 */	
	STDMETHOD(GetStartTime) (THIS_
				UINT32* pulStartTime) PURE;                   

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::GetEndTime
     *	Purpose:
     *	    returns the current end time in milliseconds
	 *
     *	Parameters:
     *		pulEndTime - [out] the current end time will be returned in pulEndTime. 
	 */	
	STDMETHOD(GetEndTime) (THIS_
				UINT32* pulEndTime) PURE;                                       

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::GetNumInputFiles
     *	Purpose:
     *	    returns the number of input files that have be added via the 
	 *		SetInputFile() and AddInputFile() methods.
	 *
     *	Parameters:
     *		pulNumInputFiles - [out] the current number of input files. 
	 */	
	STDMETHOD(GetNumInputFiles) (THIS_
				UINT32* pulNumInputFiles) PURE;        

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::GetIndexedInputFile
     *	Purpose:
     *		returns the file name of the input file specified by index. 
	 *		Use GetNumInputFiles() to determine how many files have been added to
	 *		theRMEditor interface.
	 *
     *	Parameters:
     *		index - [in] the index of the required input file. Must be in the
	 *		range of 0 to GetNumInputFiles() - 1.
	 *		szFileName - [out] the path to the input file. This buffer must be preallocated.
     *		ulMaxBufSize - [in] the size of the buffer szFileName. 
	 */	
	STDMETHOD(GetIndexedInputFile) (THIS_
				UINT32 index, char* szFileName, UINT32 ulMaxBufSize) PURE;        

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::GetOutputFile
     *	Purpose:
     *		returns the file name of the output file.
	 *
     *	Parameters:
 	 *		szFileName - [out] the path to the output file. This buffer must be preallocated.
     *		ulMaxBufSize - [in] the size of the buffer szFileName. 
	 */	
	STDMETHOD(GetOutputFile) (THIS_
				char* szFileName, UINT32 ulMaxBufSize) PURE;        

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::SetRMFileSink
     *	Purpose:
     *		Adds an IRMARMFileSink interface to the RMEditor interface. The IRMARMFileSink 
	 *		interface will be notified whenever a media properties header or data
	 *		packet is written to the output file.
	 *
     *	Parameters:
 	 *		pRMFileSink - [in] a pointer to a IRMARMFileSink interface.
	 */	
	STDMETHOD(SetRMFileSink)	(THIS_
				IRMARMFileSink* pRMFileSink) PURE;

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::RemoveRMFileSink
     *	Purpose:
     *		removes the specified IRMARMFileSink from the RMEditor interface.
	 *
     *	Parameters:
 	 *		pRMFileSink - [in] a pointer to a IRMARMFileSink interface..
	 */	
	STDMETHOD(RemoveRMFileSink)	(THIS_
				IRMARMFileSink* pRMFileSink) PURE;

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::CreateIRMABuffer
     *	Purpose:
     *		creates an instance of an IRMABuffer.
	 *
     *	Parameters:
 	 *		pBuffer - a handle to an IRMABuffer.
	 */	
	STDMETHOD(CreateIRMABuffer)	(THIS_
				IRMABuffer** pBuffer) PURE;

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::OpenLogFile
     *	Purpose:
     *		opens the specified file for logging. All status and error messages will be
	 *		logged to this file.
	 *
     *	Parameters:
 	 *		pFileName - [in] the path to the log file.
	 */	
	STDMETHOD(OpenLogFile)	(THIS_
				const char* pFileName) PURE;

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::CloseLogFile
     *	Purpose:
     *		closes the log file
	 *
     *	Parameters:
 	 *		None
	 */	
	STDMETHOD(CloseLogFile)	(THIS) PURE;

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::Log
     *	Purpose:
     *		logs the string to the log file
	 *
     *	Parameters:
 	 *		pLogString - [in] the string to be logged to the log file.
	 */	
	STDMETHOD(Log)	(THIS_
				const char* pLogString) PURE;

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::Process
     *	Purpose:
     *		processes the edit using the current settings. Creates and writes to the output file.
	 *
     *	Parameters:
 	 *		None
	 */	
	STDMETHOD(Process) (THIS) PURE; 

};

#endif //_RMAEDIT_H_