**********************************************************************
                            Readme File for
 Microsoft Windows Media Format Software Development Kit version 4.1
                      Last updated: December 1999
**********************************************************************
         (c) 1999 Microsoft Corporation. All rights reserved.

This document provides complementary or late-breaking information to 
supplement the Microsoft Windows Media Format Software Development Kit
(SDK) documentation.


======================================================================
HOW TO USE THIS DOCUMENT
======================================================================

To view the Windows Media Format SDK Readme.txt file on-screen in 
Microsoft Notepad, maximize the Notepad window.

To print Readme.txt, open it in Notepad or another word 
processor, and then on the File menu, click Print.


======================================================================
CONTENTS
======================================================================

1.0  SETUP ISSUES

2.0  KNOWN ISSUES

3.0  DOCUMENTATION ISSUES

4.0  WHAT HAS CHANGED SINCE THE BETA RELEASE

5.0  LEGAL NOTICE

======================================================================
1.0 SETUP ISSUES 
======================================================================


1.1 Windows Media Format SDK system requirements
------------------------------------------------
You can run Windows Media Format SDK version 4.1 on
* Microsoft Windows 95 OSR2 with DCOM95 installed
* Microsoft Windows 98 and Windows 98 Second Edition
* Microsoft Windows NT version 4.0 with Service Pack (SP) 3, 4, 5, or 6
* Microsoft Windows 2000 Professional, Windows 2000 Server

NOTE: Microsoft has not tested the portable media Service Provider 
with compact flash readers on Windows 2000 because drivers are not 
yet available.

To view the SDK documentation, you also need Microsoft
Internet Explorer version 4.01 or later, and the latest version 
of Hhctrl.ocx. For more information, see the Documentation Issues 
section of this readme file.

1.2 Microsoft Visual C++ 6.0
----------------------------
The sample projects have been built and tested only with Microsoft 
Visual C++ version 6.0 on Windows 98 Second Edition, Windows NT 
version 4.0 with SP6, and Windows 2000.


1.3 WMDMREDIST.EXE Setup Details
--------------------------------

The Windows Media Device Manager interfaces installed by the 
WMDMRedist.exe redistribution packages require DCOM95 to be 
present on the system. An application developer who includes this 
package should determine whether DCOM is present on the system. If 
DCOM is not found, block the application setup from proceeding, 
and display a warning message to the user. 

DCOM packages can be found on the Downloads and CD-ROMs page at the 
Microsoft Web site at:
http://www.microsoft.com/com/resources/downloads.asp 

The following registry key can be used to detect whether DCOM has 
been installed on a Windows 95 system.

HkeyClassesRoot\CLSID\{bdc67890-4fc0-11d0-a805-00aa006d2ea4}
\InstalledVersion = "a,b,c,d" 

This key exists only if DCOM95 has been successfully installed. 
The minimum version of DCOM95 is sufficient, and you can replace 
the "a,b,c,d" above with "4,71,0,1120" regardless of what is 
actually installed. Or you can check the actual version numbers 
by checking the registry using Visual Basic.

DCOM is present on Windows 98 , Windows 98 Second Edition, 
Windows NT4 with SP3, and Windows 2000.


1.4 Including redistribution packages in an application setup
-----------------------------------------------------------------------

When including the redistribution packages in your application, you can 
use the /Q:A /R:N parameter when you invoke the redistribution package in 
your setup routine to supress the user interface (UI) of the redistribution 
packages. (For more information, see the Software Redistribution Setup 
section of the documentation.) 

The following sample code can be used in your setup routine to run the 
redistribution packages in quiet mode and notify your setup routine when 
the computer must be restarted. 


#define MAX_TIMEOUT_MS 30 * 60 * 1000
#define TIME_INCREMENT 250

///////////////////////////////////////////////////////////////////////
BOOL SystemNeedsReboot( )
///////////////////////////////////////////////////////////////////////
{
    BOOL fNeedExists = FALSE;
    OSVERSIONINFO osvi;

    osvi.dwOSVersionInfoSize = sizeof( OSVERSIONINFO );
    GetVersionEx( &osvi );

    if( VER_PLATFORM_WIN32_NT != osvi.dwPlatformId )
    {
        TCHAR szIniPath[MAX_PATH];

        GetWindowsDirectory(szIniPath, sizeof(szIniPath)/sizeof(TCHAR));
        AppendSlash( szIniPath );
        _tcscat( szIniPath, _T("wininit.ini") );

        if( 0xFFFFFFFF != GetFileAttributes( szIniPath ) )
        {
            HFILE hFile;

            if( (hFile = _lopen( szIniPath, OF_READ|OF_SHARE_DENY_NONE))
                                                        != HFILE_ERROR )
            {
                fNeedExists = ( 0 != _llseek(hFile, 0L, FILE_END) );
                _lclose(hFile);
            }
        }
    }
    else
    {
        HKEY hKey = NULL;

        if( ERROR_SUCCESS == RegOpenKeyEx( HKEY_LOCAL_MACHINE, 
_T("System\\CurrentControlSet\\Control\\Session Manager"), 0, KEY_READ,
                                                              &hKey ) )
        {
            if( ERROR_SUCCESS == RegQueryValueEx( hKey, 
_T("PendingFileRenameOperations"), NULL, NULL, NULL, NULL ) )
            {
                fNeedExists = TRUE;
            }

            RegCloseKey( hKey );
        }
    }

    return( fNeedExists );
}

///////////////////////////////////////////////////////////////////////
BOOL GoInstallWMRedist( BOOL fWaitForCompletion )
///////////////////////////////////////////////////////////////////////
{
    STARTUPINFO StartUpInfo;
    PROCESS_INFORMATION ProcessInfo;

    StartUpInfo.cb = sizeof( StartUpInfo );
    StartUpInfo.lpReserved = NULL;
    StartUpInfo.dwFlags = 0;
    StartUpInfo.cbReserved2 = 0;
    StartUpInfo.lpReserved2 = NULL; 
    StartUpInfo.lpDesktop = NULL;
    StartUpInfo.lpTitle = NULL;
    StartUpInfo.dwX = 0;
    StartUpInfo.dwY = 0;
    StartUpInfo.dwXSize = 0;
    StartUpInfo.dwYSize = 0;
    StartUpInfo.dwXCountChars = 0;
    StartUpInfo.dwYCountChars = 0;
    StartUpInfo.dwFillAttribute = 0;
    StartUpInfo.dwFlags = 0;
    StartUpInfo.wShowWindow = 0;
    StartUpInfo.hStdInput = NULL;
    StartUpInfo.hStdOutput = NULL;
    StartUpInfo.hStdError = NULL;

    // Run the installer with the Quiet for All dialogs and Reboot:Never 
    // flags. The installation should be silent, and the setup routine  
    // will be notified whether the computer must be restarted.

    if( !CreateProcess( "c:\\temp\\WMFRedist.exe", "c:\\temp\\WMFRedist.exe 
/Q:A /R:N", NULL, FALSE, 0, NULL, NULL, &StartUpInfo, &ProcessInfo ) )
    {
        DWORD myError = GetLastError();
        return( FALSE );
    }

    CloseHandle( ProcessInfo.hThread );

    if( fWaitForCompletion )
    {
        DWORD dwTimePassed = 0;

        while( TRUE )
        {
           
            if( WAIT_TIMEOUT != WaitForMultipleObjects( 1, 
                  &ProcessInfo.hProcess, FALSE, TIME_INCREMENT ) )
            {
                break;
            }
    
            if( dwTimePassed > MAX_TIMEOUT_MS )
            {
                TerminateProcess( ProcessInfo.hProcess, E_FAIL );
                break;
            }

            dwTimePassed += TIME_INCREMENT;
        }
    }

    CloseHandle( ProcessInfo.hProcess);

    if( SystemNeedsReboot() )
    {
       // Write some code here to ensure your application will 
       // restart the computer, and delay dll registrations and so on 
       // until after the restart, where possible. For example, 
       // set a global flag for use by the application.
    }

    return( TRUE );
}


======================================================================
2.0 KNOWN ISSUES
======================================================================


2.1 The writer must be called from a single thread
----------------------------------------------------------------------
Using WriteSample and/or WriteStreamSample from more than one thread 
fails. Applications must call these methods from a single thread. 
This restriction does not apply to the reader.


2.2 Input video frames to IWMWriter must match the frame rate in 
the profile
------------------------------------------------------------------
When video frames are passed to IWMWriter, they must be passed in 
at or below the frame rate specified in the profile for that video 
stream. If not, video frames can be dropped in the Windows Media 
file that is produced.


2.3 An incomplete URL is returned if the caller does not have a license
--------------------------------------------------------------------
If the caller does not have a license to play the requested file, then 
the callback function OnStatus returns the WMT_NO_RIGHTS member of the 
WMT_STATUS enumeration type. In addition to returning this value, 
OnStatus returns a URL that can be used to request a license. This URL 
is not complete. The following code must be appended to it:

&filename=URL_or_File_Name&embedded=false

where URL_or_File_Name is the URL or file name of the current file 
in URL format, for example, mms://www.domain_name.com/file.wma, or 
file://file.wma.

The file name should point to the location of the file being played. 
This can be an http:// link (for a remote file) or a file:// link for a 
local one. The license server passes this link back to the client, so it 
must be a link that the client browser can execute to access the content.

These URLs cannot contain spaces and certain characters such as the 
backslash. A space must be replaced in a URL as %20, and a backslash 
as %5C. For example: filename=file://c:\My Documents\file.wma must be 
sent as filename=file://c:%5CMy%20Documents%5file.wma. For code that 
makes this substitution, see the samples. 


2.4 Installing the Microsoft Windows Media Format SDK disables 
the Windows Media Audio codec version 1.0 compressor
----------------------------------------------------------------------
Sonic Foundry Vegas version 1.0 and Microsoft Mobile Audio Player 
Manager contain the earlier version of the Windows Media 
Audio codec. Installing the final-release version of Windows Media 
Tools, the Windows Media Format Software Development Kit, or Windows 
Media On-Demand Producer updates the Windows Media Audio codec 
to a later version that causes applications that are only compatible 
with earlier versions of the Windows Media Audio codec to stop working. 

Vegas Pro version 1.0a and newer support the newer version of the codec. 
To download an update of Vegas, go to the Sonic Foundry Web site: 

http://www.sonicfoundry.com/

If you have Mobile Audio Manager 4.0 installed on your computer and use 
it with a Casio E-100 or E-105 device, get an update to the Mobile Audio 
Manager version 4.0a or newer from the Casio Web site:

http://www.casio.com/hpc/detail.cfm?PID=1182


2.5 PCMCIA adapters are not supported for portable media
--------------------------------------------------------
This version of the Windows Media Device Manager redistribution package 
does not read or write data to a PCMCIA adapter.


2.6 The WMDM Initialize method is not implemented
--------------------------------------------------
It is not possible to format a CompactFlash card using this SDK.


2.7 The WMDM_SCP_EXAMINE_EXTENSION flag does not work properly
--------------------------------------------------------------
If you are writing a Secure Content Provider (SCP), always demand 
data from Windows Media Device Manager to determine whether it is 
responsible for a specified piece of content.


2.8 An SCP must set pfuFlags before exiting from 
calls to GetDataDemands
--------------------------------------------------
If this is not done, Windows Media Device Manager can enter an 
infinite loop.


2.9 The Iomega.vxd file is not automatically included in a 
redistribution package
------------------------------------------------------------------
If ISVs require the Iomega.vxd file included in a redistribution package, 
they must copy it manually from the redistribution directory included 
with this SDK. This is only required when running Windows 95 and 
Windows 98. To transfer SDMI content to Iomega drives, users must 
install Iomega Tools that come with their Iomega drive. Alternatively, 
they can manually copy Iomega.vxd to the Windows System\Iosubsys 
directory and restart the computer.


2.10 The SDK returns an error code if the appropriate codec is 
not installed
---------------------------------------------------------------------
This SDK is not designed to download a codec automatically. The 
SDK returns an error code if the required codec is not installed 
on the target computer. This only applies if the file is a Windows 
Media file. The application must download the codec, if needed.


2.11 Video samples must be encoded to sizes that are multiples of four
-----------------------------------------------------------------------
Video content does not play correctly unless it is encoded to a size that 
is a multiple of four. Both width and height must be multiples of four. 
RGB uncompressed video can be any size. 

If you try to set a size that is not a multiple of four (usually through 
a call to SetMediaType()), you produce an NS_E_INVALID_INPUT_FORMAT, 
NS_E_INVALID_OUTPUT_FORMAT, or NS_E_INVALIDPROFILE error code.


2.12 The function SetUserProvidedClock sometimes fails
------------------------------------------------------
Trying to enable the user clock with SetUserProvidedClock( TRUE ) on 
the IWMReaderAdvanced interface fails if it is called after the content 
has been played for some time. The failed call returns the 
NS_E_INVALID_REQUEST error code.

To work around this, call Start(0,0,1.0,NULL) immediately before calling
SetUserProvidedClock:

Start( 0, 0, 1.0, NULL );
SetUserProvidedClock( TRUE ); 


2.13 To use DRM with samples, add SUPPORT_DRM to preprocessor definitions
-------------------------------------------------------------------------
To use the digital rights management (DRM) functionality of the Windows 
Media Format SDK in your sample, in addition to following the steps 
listed in the Acquiring Certificates and Licenses section of the SDK 
documentation, you also must add SUPPORT_DRM to the preprocessor 
definitions in the Project/Settings menu of Microsoft Visual C++.


2.14  A file with audio and script streams is not seekable by default
----------------------------------------------------------------------
In this release, seeking sometimes does not work properly in files with 
audio and script streams. It is necessary to post-process the files by 
running the index object on them.


2.15 Problems when sending large amounts of script data
-------------------------------------------------------
On average, authoring software should not send more than the equivalent 
of 30 percent of the allocated bit rate of a script stream, or send a 
single script command larger than approximately one second of data (or the 
equivalent of the bit rate divided by 8). If these limits are exceeded, 
Windows Media files with script commands that have later-than-expected 
presentation times may be created, or the script commands may not appear 
in the Windows Media file at all.  If either problem occurs, the allocated 
script stream bandwidth should be increased or less data should be 
transmitted through the script stream by the authoring software.


2.16 Calling Open concurrently over a network can fail
------------------------------------------------------
Calling Open concurrently, either on one reader or on multiple readers,
may not work correctly when opening files over a network. In particular,
proxy settings may not be detected, causing the Open to fail. 
To avoid this issue, after calling Open, follow one of two steps before
opening another file: either (i) wait for the WMT_OPENED or WMT_ERROR
OnStatus callback, or (ii) call Close and wait for the close to complete.


2.17 Running on multi-processor systems may lead to extra threads being
created
-----------------------------------------------------------------------
Using the reader or writer on a multi-processor system may result in extra 
threads being created that do not exit until the application ends. This 
only occurs when reading or writing files with video. This could lead to 
the application failing after running for extended periods of time.


2.18 WMAPlay sample never unprepares audio buffers
--------------------------------------------------
The WMAPlay sample does not call waveOutUnprepareHeader as it should. 
This leads to resource leaks as files are played. This should not lead 
to any problems with WMAPlay because the sample only plays one file 
and then ends. In addition, any code based on WMAPlay should call 
waveOutUnprepareHeader for every audio buffer prepared with 
waveOutPrepareHeader.


======================================================================
3.0 DOCUMENTATION ISSUES 
======================================================================


3.1 SDK documentation
------------------------------------------------------
The documentation for this SDK is provided in the form of a compiled 
Microsoft HTML Help (.chm) file. To view this file, you need Internet 
Explorer 4.01 with SP1 or later, and the latest version of 
the Hhctrl.ocx file and its associated DLLs. 

If you receive a sequence of error messages when you open this file, 
you can still read it, but it will not be rendered correctly. This 
indicates you have an earlier version of the Hhctrl.ocx file. You 
can download a newer version of this file from the HTML Help Download 
page at the Microsoft Web site:

http://msdn.microsoft.com/workshop/author/htmlhelp/download.asp


3.2 Methods missing from Windows Media Device Manager Logger documentation
--------------------------------------------------------------------------
IWMDMLogger::Enable
The Enable method enables or disables logging. By default, logging is disabled.
Syntax
HRESULT Enable( BOOL fEnable );
Parameters
fEnable
[in] Boolean to enable or disable logging.
Return Values
If the method succeeds, it returns S_OK. If it fails, it returns an 
HRESULT error code.

IWMDMLogger::IsEnabled
The IsEnable method checks whether logging is enabled.
Syntax
HRESULT IsEnabled( BOOL *pfEnable );
Parameters
pfEnable
[out] True if logging is enabled.
Return Values
If the method succeeds, it returns S_OK. If it fails, it returns an 
HRESULT error code.


3.3 Undocumented Secure Authenticated Channel functions
-------------------------------------------------------
CSecureChannelClient::EncryptParam(BYTE *pbData, DWORD dwDataLen)
       Encrypts input data with SAC session key.

CSecureChannelClient::DecryptParam(BYTE *pbData, DWORD dwDataLen)
       Decrypts input data with SAC session key.

CSecureChannelClient::MACInit(HMAC *phMAC)
       Acquires a MAC channel.

CSecureChannelClient::MACUpdate(HMAC hMAC, BYTE *pbData, DWORD dwDataLen)
       Updates the MAC value with a parameter value.

CSecureChannelClient::MACFinal(BYTE abData[SAC_MAC_LEN])
       Releases the MAC channel and returns a final MAC value.


3.4 WMDM functions containing the message authentication code 
for the output parameter data
------------------------------------------------------
	IWMDMDevice::GetSerialNumber
	IWMDMStorage::GetRights
When the application returns after calling the preceding methods, it can 
use MAC methods to calculate the MAC value of parameters and compare 
them with output MAC values to ensure the parameters have not been 
tampered with.

Sample code:

     CSecureChannelClient *pSCClient;
     IWMDMStorage	*pStorgae;

     HMAC hMAC;
     BYTE  abMAC[WMDM_MAC_LENGTH];
     BYTE  abMACVerify[WMDM_MAC_LENGTH];
    
     // pSCClient and pStorage creation code shipped

     hr = pStorage->GetRights(&pRights, &nRightsCount, abMAC);
     if ( SUCCEEDED(hr))
     {
          pSCClient->MACInit(&hMAC);
          pSCClient->MACUpdate(hMAC, (BYTE*)(pRights), 
                                 sizeof(WMDMRIGHTS) * nRightsCount);
          pSCClient->MACUpdate(hMAC, (BYTE*)(&nRightsCount), 
                                 sizeof(nRightsCount));
          pSCClient->MACFinal(hMAC, (BYTE*)abMACVerify);
          if (memcmp(abMACVerify, abMAC, sizeof(abMAC)) != 0)
          {
		hr = WMDM_E_MAC_CHECK_FAILED;
          }
    }


3.5 IMDSPObject::Move has incorrect parameter information
---------------------------------------------------------
The pProgress parameter of IMDSPObject::Move, a Windows Media Device 
Manager Service Provider method, is listed in the reference as an output 
parameter. It is actually an input parameter.


======================================================================
4.0 WHAT HAS CHANGED SINCE THE BETA 
======================================================================


4.1 The following changes have been made to the Windows Media 
Device Manager interfaces since the beta release:
------------------------------------------------------
ADDED:
  New method: IWMDMStorage::SetAttributes
  New method: IWMDMStorageGlobals::GetTotalSize
  New method: IMDSPStorage::SetAttributes
  New method: IMDSPStorageGlobals::GetTotalSize
  New structure: WMDMDATETIME
  New error code for most methods of SCP: WMDM_E_MAC_CHECK_FAILED
  New error code for IWMDMOperation and IWMDMProgress: WMDM_E_USER_CANCELLED
  New mode flag for IWMDMStorageControl::Delete and IMDSPObject::Delete:
                                            WMDM_MODE_RECURSIVE
  New attributes for IWMDMStorage::GetAttributes and 
                     IMDSPStorage::GetAttributes: 
                                            WMDM_STORAGE_ATTR_HAS_FOLDERS
                                        and WMDM_STORAGE_ATTR_HAS_FILES

CHANGED:
  The WMDMRIGHTS structure now contains a WMDMDATETIME structure.
  IMDSPObject::Delete now takes a UINT instead of a boolean.

REMOVED:
  Old method: ISCPSecureExchange::ObjectName
  Old method: ISCPSecureExchange::ObjectTotalSize
  Old flags from ISCPSecureExchange::TransferContainerData:
                     WMDM_SCP_TRANSFER_NAME and WMDM_SCP_TRANSFER_TOTALSIZE


4.2 The following changes have been made to the rest 
of the SDK since the beta release:
------------------------------------------------------
This release of the SDK includes a number of new methods and functions,
as well as some small changes to methods exposed by the beta release of 
this SDK. This section describes the differences, and is for application 
developers who have written an application using an earlier release of 
this SDK.

The new interface IWMIndexer along with the creation function 
WMCreateIndexer have been added to handle indexing.

The WMT_INDEX_PROGRESS message has been added to the WMT_STATUS 
enumeration type.

The value WMT_TYPE_GUID has been added to the WMT_ATTR_DATATYPE 
enumeration type.

A new interface, IWMStatusCallback, now handles the OnStatus call that 
used to be in the IWMReaderCallback interface. However IWMReaderCallback 
now inherits from IWMStatusCallback, so the method is still available 
through this interface.

There are two new methods in the IWMWriterAdvanced interface called 
SetSyncTolerance and GetSyncTolerance.

The SetStreamSelected method has been renamed SetStreamsSelected, 
and the parameters have been changed to handle multiple streams.

The methods GetMaxOutputSampleSize, GetMaxStreamSampleSize, and 
NotifyLateDelivery have been added to IWMReaderAdvanced.

Keying has been removed. This has caused the following changes:

1. WMCreateReader and WMCreateWriter are used differently. The number 
   of parameters for these two functions has changed.

    In the beta, to create a non-DRM reader, you used:

                WMCreateReader( &pReader );

    and to create a DRM reader, you used:

                WMCreateDRMReader( NULL, dwRights, &pReader );

    This has changed to a singe function:

                WMCreateReader( NULL, dwRights, &pReader ); // For DRM
                WMCreateReader( NULL, 0, &pReader );       // For Non DRM

    Writer calls in beta were:

             WMCreateDRMWriter( NULL, &pWriter );
             WMCreateWriter(&pWriter);

    These have changed to a single call for both DRM and non-DRM cases: 

            WMCreateWriter( NULL, &pWriter ); 

2. The libraries to use for DRM functionality and non-DRM functionality 
are different. Wmstub.lib is used for non-DRM and Wmstubdrm.lib is used 
for DRM. For more information, see the Acquiring Certificates and Libraries 
section in the SDK documentation.

3. The header files Wmsdkdrm.h and Wmkey.h no longer exist.

Many of these changes were based on developer feedback. They were designed 
to make it easier to use the Windows Media Format SDK by handling 
functions within the SDK where possible, so your application does not 
need to make unnecessary calls.


================
5.0 LEGAL NOTICE
================

Information in this document, including URL and other Internet Web site 
references, is subject to change without notice.  Unless otherwise noted, 
the example companies, organizations, products, people and events depicted 
herein are fictitious and no association with any real company, organization, 
product, person or event is intended or should be inferred.  Complying with 
all applicable copyright laws is the responsibility of the user.  Without 
limiting the rights under copyright, no part of this document may be 
reproduced, stored in or introduced into a retrieval system, or transmitted 
in any form or by any means (electronic, mechanical, photocopying, recording, 
or otherwise), or for any purpose, without the express written permission of 
Microsoft Corporation. 

Microsoft may have patents, patent applications, trademarks, copyrights, or 
other intellectual property rights covering subject matter in this document. 
Except as expressly provided in any written license agreement from Microsoft, 
the furnishing of this document does not give you any license to these patents, 
trademarks, copyrights, or other intellectual property.

(c) 1999 Microsoft Corporation.  All rights reserved.

Microsoft, MS-DOS, Windows, Windows NT, WIndows Media, Visual Basic, and 
Visual C++ are either registered trademarks or trademarks of Microsoft 
Corporation in the United States and/or other countries/regions.

The names of actual companies and products mentioned herein may be the 
trademarks of their respective owners.



======================================================================
*	End
======================================================================


