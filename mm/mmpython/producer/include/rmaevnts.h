/****************************************************************************
 * 
 *	rmaevnts.h
 *
 *	$Id$
 *
 *	Copyright ©1998 RealNetworks.
 *	All rights reserved.
 *
 *	Definition of the Interfaces for the RMEvents SDK.
 *
 */

#ifndef _RMAEVNTS_H_
#define _RMAEVNTS_H_

struct IRMAProgressSink;


// Prototype to create instance of RMEvents object and 
// typedef to get a pointer to this function from the dll
typedef PN_RESULT (PNEXPORT_PTR FPCREATEINSTANCE) (IUnknown** /*OUT*/ ppIUnknown);
STDAPI RMACreateRMEvents(IUnknown**  /*OUT*/	ppIUnknown);

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMARMEvents
 *
 *  Purpose:
 *
 *	Interface to rmevents module
 *
 *  IRMARMEvents
 *
 *  {3EE719E0-5307-11d2-A1D1-0060083BE563}
 *
 */

DEFINE_GUID(IID_IRMARMEvents, 
0x3ee719e0, 0x5307, 0x11d2, 0xa1, 0xd1, 0x0, 0x60, 0x8, 0x3b, 0xe5, 0x63);

#define CLSID_IRMARMEvents IID_IRMARMEvents

#undef  INTERFACE
#define INTERFACE   IRMARMEvents

DECLARE_INTERFACE_(IRMARMEvents, IUnknown)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(ULONG32,AddRef)	(THIS) PURE;

    STDMETHOD_(ULONG32,Release)	(THIS) PURE;

    // *** IRMARMEvents methods ***
 
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
     *	    IRMARMEdit::SetInputFile
     *	Purpose:
     *	    specifies the file name of the input .rm file. 
     *
     *	Parameters:
     *		szFileName - [in] the path to the input file.
	 */	
	STDMETHOD(SetInputFile) (THIS_
				const char* szFileName) PURE;  

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::SetOutputFile
     *	Purpose:
     *	    specifies the file name of the output file. This .rm file will contain the results
	 *		of the merge operation.
     *
     *	Parameters:
     *		szFileName - [in] the path to the output .rm file. If the file already exists, it 
	 *		will be replaced. If the file does not exist it will be created.
	 */	
	STDMETHOD(SetOutputFile) (THIS_
				const char* szFileName) PURE; 

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::SetEventFile
     *	Purpose:
     *	    specifies the file name of the event text file. 
     *
     *	Parameters:
     *		szFileName - [in] the path to the event text file. 
	 */	
	STDMETHOD(SetEventFile) (THIS_
				const char* szFileName) PURE; 

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::SetImageMapFile
     *	Purpose:
     *	    specifies the file name of the image map text file. 
     *
     *	Parameters:
     *		szFileName - [in] the path to the image map text file. 
	 */	
	STDMETHOD(SetImageMapFile) (THIS_
				const char* szFileName) PURE; 

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::SetDumpFile
     *	Purpose:
     *	    specifies the root file name of the Dump file. 
     *		All events in the input file will be dumped into szFileName_evt.txt
     *		All image maps in the input file will be dumped into szFileName_imap.txt
     *
     *	Parameters:
     *		szFileName - [in] the path to dump file root. 
	 */	
	STDMETHOD(SetDumpFile) (THIS_
				const char* szFileName) PURE; 

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::GetInputFile
     *	Purpose:
     *	     returns the file name of the input file
     *
     *	Parameters:
 	 *		szFileName - [out] the path to the input file. This buffer must be preallocated.
     *		ulMaxBufSize - [in] the size of the buffer szFileName. 
     */
	STDMETHOD(GetInputFile) (THIS_
				char* szFileName, UINT32 ulMaxBufSize) PURE;        

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::GetOutputFile
     *	Purpose:
     *	     returns the file name of the output file
     *
     *	Parameters:
 	 *		szFileName - [out] the path to the output file. This buffer must be preallocated.
     *		ulMaxBufSize - [in] the size of the buffer szFileName. 
     */
	STDMETHOD(GetOutputFile) (THIS_
				char* szFileName, UINT32 ulMaxBufSize) PURE;        

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::GetEventFile
     *	Purpose:
     *	     returns the file name of the event text file
     *
     *	Parameters:
 	 *		szFileName - [out] the path to the event text file. This buffer must be preallocated.
     *		ulMaxBufSize - [in] the size of the buffer szFileName. 
     */
	STDMETHOD(GetEventFile) (THIS_
				char* szFileName, UINT32 ulMaxBufSize) PURE;        

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::GetImageMapFile
     *	Purpose:
     *	     returns the file name of the image map text file
     *
     *	Parameters:
 	 *		szFileName - [out] the path to the image map text file. This buffer must be preallocated.
     *		ulMaxBufSize - [in] the size of the buffer szFileName. 
     */
	STDMETHOD(GetImageMapFile) (THIS_
				char* szFileName, UINT32 ulMaxBufSize) PURE;        

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::GetDumpFile
     *	Purpose:
     *	     returns the name of the dump file root name
     *
     *	Parameters:
 	 *		szFileName - [out] the path to the dump file root name. This buffer must be preallocated.
     *		ulMaxBufSize - [in] the size of the buffer szFileName. 
     */
	STDMETHOD(GetDumpFile) (THIS_
				char* szFileName, UINT32 ulMaxBufSize) PURE;        

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
	STDMETHOD(Log)	(THIS_ const char* pLogString) PURE;

	/************************************************************************
     *	Method:
     *	    IRMARMEdit::Process
     *	Purpose:
     *		merges the events and image maps with the input file. Create and writes the output file
	 *
     *	Parameters:
 	 *		None
	 */	
	STDMETHOD(Process) (THIS) PURE; 

};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMARMEvents2
 *
 *  Purpose:
 *
 *	Interface to rmevents module
 *
 *  {2AF82001-ADC6-11d3-8660-42525E000000}
 *
 */

DEFINE_GUID(IID_IRMARMEvents2, 
0x2af82001, 0xadc6, 0x11d3, 0x86, 0x60, 0x42, 0x52, 0x5e, 0x0, 0x0, 0x0);

#define CLSID_IRMARMEvents2 IID_IRMARMEvents2

#undef  INTERFACE
#define INTERFACE   IRMARMEvents2

DECLARE_INTERFACE_(IRMARMEvents2, IRMARMEvents)
{
	/************************************************************************
     *	Method:
     *	    IRMARMEvents2::AddSaveProgressSink
     *	Purpose:
     *		Add sink which receives callbacks with save progress
	 */	
    STDMETHOD(AddSaveProgressSink)(IRMAProgressSink* pProgressSink) PURE;
    
	/************************************************************************
     *	Method:
     *	    IRMARMEvents2::RemoveSaveProgressSink
     *	Purpose:
     *		Remove progress-during-save sink
	 */	
    STDMETHOD(RemoveSaveProgressSink)(IRMAProgressSink* pProgressSink) PURE;
};

#endif //_RMAEVNTS_H_