# Microsoft Developer Studio Project File - Name="vaud2rm" - Package Owner=<4>
# Microsoft Developer Studio Generated Build File, Format Version 6.00
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Dynamic-Link Library" 0x0102

CFG=vaud2rm - Win32 Release
!MESSAGE This is not a valid makefile. To build this project using NMAKE,
!MESSAGE use the Export Makefile command and run
!MESSAGE 
!MESSAGE NMAKE /f "aud2rm.mak".
!MESSAGE 
!MESSAGE You can specify a configuration when running NMAKE
!MESSAGE by defining the macro CFG on the command line. For example:
!MESSAGE 
!MESSAGE NMAKE /f "aud2rm.mak" CFG="vaud2rm - Win32 Release"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "vaud2rm - Win32 Release" (based on "Win32 (x86) Dynamic-Link Library")
!MESSAGE "vaud2rm - Win32 Debug" (based on "Win32 (x86) Dynamic-Link Library")
!MESSAGE 

# Begin Project
# PROP AllowPerConfigDependencies 0
# PROP Scc_ProjName ""
# PROP Scc_LocalPath ""
CPP=cl.exe
MTL=midl.exe
RSC=rc.exe

!IF  "$(CFG)" == "vaud2rm - Win32 Release"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir "Release"
# PROP BASE Intermediate_Dir "Release"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 0
# PROP Output_Dir ""
# PROP Intermediate_Dir "Release"
# PROP Ignore_Export_Lib 0
# PROP Target_Dir ""
F90=df.exe
# ADD BASE CPP /nologo /MT /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_WINDOWS" /YX /FD /c
# ADD CPP /nologo /Gz /MD /W3 /Gy /I "..\..\classes\base" /I "..\..\include" /I "..\..\..\..\mmpython\producer\include" /D DBG=0 /D WINVER=0x400 /D _X86_=1 /D "_DLL" /D "_MT" /D "_WIN32" /D "WIN32" /D "STRICT" /D "INC_OLE2" /D try=__try /D except=__except /D leave=__leave /D finally=__finally /Oxs /GF /D_WIN32_WINNT=-0x0400 /c
# ADD BASE MTL /nologo /D "NDEBUG" /mktyplib203 /o "NUL" /win32
# ADD MTL /nologo /D "NDEBUG" /mktyplib203 /o "NUL" /win32
# ADD BASE RSC /l 0x409 /d "NDEBUG"
# ADD RSC /l 0x409 /d "NDEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /machine:I386
# ADD LINK32 ..\..\lib\strmbase.lib ..\..\lib\quartz.lib msvcrtd.lib vfw32.lib winmm.lib kernel32.lib advapi32.lib version.lib largeint.lib user32.lib gdi32.lib comctl32.lib ole32.lib olepro32.lib oleaut32.lib uuid.lib /nologo /base:"0x1d1c0000" /entry:"DllEntryPoint@12" /dll /pdb:none /machine:I386 /nodefaultlib /out:"..\..\bin\aud2rm.ax" /subsystem:windows,4.0 /align:0x1000 /opt:ref /release /debug:none

!ELSEIF  "$(CFG)" == "vaud2rm - Win32 Debug"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 1
# PROP BASE Output_Dir "Debug"
# PROP BASE Intermediate_Dir "Debug"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 1
# PROP Output_Dir ""
# PROP Intermediate_Dir "Debug"
# PROP Ignore_Export_Lib 0
# PROP Target_Dir ""
F90=df.exe
# ADD BASE CPP /nologo /MTd /W3 /Gm /GX /Zi /Od /D "WIN32" /D "_DEBUG" /D "_WINDOWS" /YX /FD /c
# ADD CPP /nologo /Gz /MDd /W3 /Z7 /Gy /I "..\..\classes\base" /I "..\..\include" /I "..\..\..\..\mmpython\producer\include" /D "INC_OLE2" /D "STRICT" /D _WIN32_WINNT=0x0400 /D "WIN32" /D "_WIN32" /D "_MT" /D "_DLL" /D _X86_=1 /D WINVER=0x0400 /D DBG=1 /D "DEBUG" /D "_DEBUG" /D try=__try /D except=__except /D leave=__leave /D finally=__finally /Oid /c
# ADD BASE MTL /nologo /D "_DEBUG" /mktyplib203 /o "NUL" /win32
# ADD MTL /nologo /D "_DEBUG" /mktyplib203 /o "NUL" /win32
# ADD BASE RSC /l 0x409 /d "_DEBUG"
# ADD RSC /l 0x409 /d "_DEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /debug /machine:I386 /pdbtype:sept
# ADD LINK32 ..\..\lib\strmbasd.lib ..\..\lib\quartz.lib msvcrtd.lib vfw32.lib winmm.lib kernel32.lib advapi32.lib version.lib largeint.lib user32.lib gdi32.lib comctl32.lib ole32.lib olepro32.lib oleaut32.lib uuid.lib /nologo /base:"0x1d1c0000" /entry:"DllEntryPoint@12" /dll /pdb:none /machine:I386 /nodefaultlib /out:"..\..\bin\aud2rm_d.ax" /align:0x1000 /debug:mapped,full /subsystem:windows,4.0

!ENDIF 

# Begin Target

# Name "vaud2rm - Win32 Release"
# Name "vaud2rm - Win32 Debug"
# Begin Source File

SOURCE=.\aud2rm.cpp
DEP_CPP_AUD2R=\
	"..\..\classes\base\amextra.h"\
	"..\..\classes\base\amfilter.h"\
	"..\..\classes\base\cache.h"\
	"..\..\classes\base\combase.h"\
	"..\..\classes\base\cprop.h"\
	"..\..\classes\base\ctlutil.h"\
	"..\..\classes\base\dllsetup.h"\
	"..\..\classes\base\fourcc.h"\
	"..\..\classes\base\measure.h"\
	"..\..\classes\base\msgthrd.h"\
	"..\..\classes\base\mtype.h"\
	"..\..\classes\base\outputq.h"\
	"..\..\classes\base\pstream.h"\
	"..\..\classes\base\refclock.h"\
	"..\..\classes\base\reftime.h"\
	"..\..\classes\base\renbase.h"\
	"..\..\classes\base\Schedule.h"\
	"..\..\classes\base\source.h"\
	"..\..\classes\base\streams.h"\
	"..\..\classes\base\strmctl.h"\
	"..\..\classes\base\sysclock.h"\
	"..\..\classes\base\transfrm.h"\
	"..\..\classes\base\transip.h"\
	"..\..\classes\base\videoctl.h"\
	"..\..\classes\base\vtrans.h"\
	"..\..\classes\base\winctrl.h"\
	"..\..\classes\base\winutil.h"\
	"..\..\classes\base\wxdebug.h"\
	"..\..\classes\base\wxlist.h"\
	"..\..\classes\base\wxutil.h"\
	".\aud2rm.h"\
	
# End Source File
# Begin Source File

SOURCE=.\aud2rm.def
# End Source File
# Begin Source File

SOURCE=.\aud2rm.h
# End Source File
# Begin Source File

SOURCE=..\..\..\..\mmpython\wmsdk\aud2rm.py
# End Source File
# Begin Source File

SOURCE=.\aud2rm.rc
# End Source File
# Begin Source File

SOURCE=.\rprod.cpp
DEP_CPP_RPROD=\
	"..\..\..\..\mmpython\producer\include\engcodec.h"\
	"..\..\..\..\mmpython\producer\include\engtargs.h"\
	"..\..\..\..\mmpython\producer\include\engtypes.h"\
	"..\..\..\..\mmpython\producer\include\pncom.h"\
	"..\..\..\..\mmpython\producer\include\pnwintyp.h"\
	"..\..\..\..\mmpython\producer\include\progsink.h"\
	"..\..\..\..\mmpython\producer\include\rmaenum.h"\
	"..\..\..\..\mmpython\producer\include\rmapckts.h"\
	"..\..\..\..\mmpython\producer\include\rmbldeng.h"\
	"..\..\..\..\mmpython\producer\include\rmmetain.h"\
	
NODEP_CPP_RPROD=\
	".\mavalue.h"\
	".\nbastsd.h"\
	".\nresult.h"\
	".\ntypes.h"\
	
# End Source File
# End Target
# End Project
