# Microsoft Developer Studio Project File - Name="rma" - Package Owner=<4>
# Microsoft Developer Studio Generated Build File, Format Version 6.00
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Dynamic-Link Library" 0x0102

CFG=rma - Win32 Debug
!MESSAGE This is not a valid makefile. To build this project using NMAKE,
!MESSAGE use the Export Makefile command and run
!MESSAGE 
!MESSAGE NMAKE /f "rma.mak".
!MESSAGE 
!MESSAGE You can specify a configuration when running NMAKE
!MESSAGE by defining the macro CFG on the command line. For example:
!MESSAGE 
!MESSAGE NMAKE /f "rma.mak" CFG="rma - Win32 Debug"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "rma - Win32 Release" (based on "Win32 (x86) Dynamic-Link Library")
!MESSAGE "rma - Win32 Debug" (based on "Win32 (x86) Dynamic-Link Library")
!MESSAGE 

# Begin Project
# PROP AllowPerConfigDependencies 0
# PROP Scc_ProjName ""
# PROP Scc_LocalPath ""
CPP=cl.exe
MTL=midl.exe
RSC=rc.exe

!IF  "$(CFG)" == "rma - Win32 Release"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir "Release"
# PROP BASE Intermediate_Dir "Release"
# PROP BASE Target_Dir ""
# PROP Use_MFC 2
# PROP Use_Debug_Libraries 0
# PROP Output_Dir "Release"
# PROP Intermediate_Dir "Release"
# PROP Ignore_Export_Lib 0
# PROP Target_Dir ""
F90=df.exe
# ADD BASE CPP /nologo /MT /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_WINDOWS" /D "_MBCS" /D "_USRDLL" /D "rma_EXPORTS" /Yu"stdafx.h" /FD /c
# ADD CPP /nologo /MD /W3 /GX /O2 /I "./include" /I "./win32" /D "NDEBUG" /D "WIN32" /D "_WINDOWS" /D "_MBCS" /D "_USRDLL" /D "PY_EXPORTS" /D "_WINDLL" /D "_AFXDLL" /FR /Yu"std.h" /FD /c
# ADD BASE MTL /nologo /D "NDEBUG" /mktyplib203 /win32
# ADD MTL /nologo /D "NDEBUG" /mktyplib203 /win32
# ADD BASE RSC /l 0x408 /d "NDEBUG"
# ADD RSC /l 0x408 /d "NDEBUG" /d "_AFXDLL"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /dll /machine:I386
# ADD LINK32 advapi32.lib version.lib kernel32.lib user32.lib gdi32.lib winmm.lib vfw32.lib /nologo /dll /machine:I386 /out:"Release/rma.pyd"
# Begin Custom Build
OutDir=.\Release
InputPath=.\Release\rma.pyd
SOURCE="$(InputPath)"

"$(OutDir)\log.txt" : $(SOURCE) "$(INTDIR)" "$(OUTDIR)"
	copy $(OutDir)\rma.pyd d:\ufs\mm\cmif\bin\win32

# End Custom Build

!ELSEIF  "$(CFG)" == "rma - Win32 Debug"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 1
# PROP BASE Output_Dir "Debug"
# PROP BASE Intermediate_Dir "Debug"
# PROP BASE Target_Dir ""
# PROP Use_MFC 2
# PROP Use_Debug_Libraries 1
# PROP Output_Dir "Debug"
# PROP Intermediate_Dir "Debug"
# PROP Ignore_Export_Lib 0
# PROP Target_Dir ""
F90=df.exe
# ADD BASE CPP /nologo /MTd /W3 /Gm /GX /ZI /Od /D "WIN32" /D "_DEBUG" /D "_WINDOWS" /D "_MBCS" /D "_USRDLL" /D "rma_EXPORTS" /Yu"stdafx.h" /FD /GZ /c
# ADD CPP /nologo /MDd /W3 /Gm /GX /ZI /Od /I "./include" /D "_DEBUG" /D "WIN32" /D "_WINDOWS" /D "_MBCS" /D "_USRDLL" /D "PY_EXPORTS" /D "_WINDLL" /D "_AFXDLL" /FR /Yu"std.h" /FD /GZ /c
# ADD BASE MTL /nologo /D "_DEBUG" /mktyplib203 /win32
# ADD MTL /nologo /D "_DEBUG" /mktyplib203 /win32
# ADD BASE RSC /l 0x408 /d "_DEBUG"
# ADD RSC /l 0x408 /d "_DEBUG" /d "_AFXDLL"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /dll /debug /machine:I386 /pdbtype:sept
# ADD LINK32 advapi32.lib version.lib kernel32.lib user32.lib gdi32.lib winmm.lib vfw32.lib /nologo /dll /debug /machine:I386 /out:"Debug/rma_d.pyd" /pdbtype:sept
# Begin Custom Build
OutDir=.\Debug
InputPath=.\Debug\rma_d.pyd
SOURCE="$(InputPath)"

"$(OutDir)\log.txt" : $(SOURCE) "$(INTDIR)" "$(OUTDIR)"
	copy $(OutDir)\rma_d.pyd d:\ufs\mm\cmif\bin

# End Custom Build

!ENDIF 

# Begin Target

# Name "rma - Win32 Release"
# Name "rma - Win32 Debug"
# Begin Group "Source Files"

# PROP Default_Filter "cpp;c;cxx;rc;def;r;odl;idl;hpj;bat"
# Begin Source File

SOURCE=.\Engine.cpp
# End Source File
# Begin Source File

SOURCE=.\InitGUID.cpp

!IF  "$(CFG)" == "rma - Win32 Release"

# SUBTRACT CPP /YX /Yc /Yu

!ELSEIF  "$(CFG)" == "rma - Win32 Debug"

!ENDIF 

# End Source File
# Begin Source File

SOURCE=.\Player.cpp
# End Source File
# Begin Source File

SOURCE=.\PyCppApi.cpp

!IF  "$(CFG)" == "rma - Win32 Release"

# ADD CPP /Yu"std.h"

!ELSEIF  "$(CFG)" == "rma - Win32 Debug"

!ENDIF 

# End Source File
# Begin Source File

SOURCE=.\rma.cpp
# End Source File
# Begin Source File

SOURCE=.\Std.cpp
# ADD CPP /Yc"Std.h"
# End Source File
# End Group
# Begin Group "Header Files"

# PROP Default_Filter "h;hpp;hxx;hm;inl"
# Begin Source File

SOURCE=.\Engine.h
# End Source File
# Begin Source File

SOURCE=.\mt.h
# End Source File
# Begin Source File

SOURCE=.\PyCppApi.h
# End Source File
# Begin Source File

SOURCE=.\Std.h
# End Source File
# Begin Source File

SOURCE=.\StdApp.h
# End Source File
# Begin Source File

SOURCE=.\StdRma.h
# End Source File
# End Group
# Begin Group "Rma Template Files"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\exadvsnk.cpp

!IF  "$(CFG)" == "rma - Win32 Release"

# SUBTRACT CPP /YX /Yc /Yu

!ELSEIF  "$(CFG)" == "rma - Win32 Debug"

!ENDIF 

# End Source File
# Begin Source File

SOURCE=.\exaumgr.cpp

!IF  "$(CFG)" == "rma - Win32 Release"

# SUBTRACT CPP /YX /Yc /Yu

!ELSEIF  "$(CFG)" == "rma - Win32 Debug"

!ENDIF 

# End Source File
# Begin Source File

SOURCE=.\excontxt.cpp

!IF  "$(CFG)" == "rma - Win32 Release"

# SUBTRACT CPP /YX /Yc /Yu

!ELSEIF  "$(CFG)" == "rma - Win32 Debug"

!ENDIF 

# End Source File
# Begin Source File

SOURCE=.\exerror.cpp

!IF  "$(CFG)" == "rma - Win32 Release"

# SUBTRACT CPP /YX /Yc /Yu

!ELSEIF  "$(CFG)" == "rma - Win32 Debug"

!ENDIF 

# End Source File
# Begin Source File

SOURCE=.\exsitsup.cpp

!IF  "$(CFG)" == "rma - Win32 Release"

# SUBTRACT CPP /YX /Yc /Yu

!ELSEIF  "$(CFG)" == "rma - Win32 Debug"

!ENDIF 

# End Source File
# Begin Source File

SOURCE=.\fivemlist.cpp

!IF  "$(CFG)" == "rma - Win32 Release"

# SUBTRACT CPP /YX /Yc /Yu

!ELSEIF  "$(CFG)" == "rma - Win32 Debug"

!ENDIF 

# End Source File
# Begin Source File

SOURCE=.\fivemmap.cpp

!IF  "$(CFG)" == "rma - Win32 Release"

# SUBTRACT CPP /YX /Yc /Yu

!ELSEIF  "$(CFG)" == "rma - Win32 Debug"

!ENDIF 

# End Source File
# End Group
# Begin Group "RMA Template Headers"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\exadvsnk.h
# End Source File
# Begin Source File

SOURCE=.\exaumgr.h
# End Source File
# Begin Source File

SOURCE=.\excontxt.h
# End Source File
# Begin Source File

SOURCE=.\exerror.h
# End Source File
# Begin Source File

SOURCE=.\exsitsup.h
# End Source File
# Begin Source File

SOURCE=.\fivemlist.h
# End Source File
# Begin Source File

SOURCE=.\fivemmap.h
# End Source File
# End Group
# Begin Group "RMASDK"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\include\pnbastsd.h
# End Source File
# Begin Source File

SOURCE=.\include\pncom.h
# End Source File
# Begin Source File

SOURCE=.\include\pnresult.h
# End Source File
# Begin Source File

SOURCE=.\include\pntypes.h
# End Source File
# Begin Source File

SOURCE=.\include\pnwintyp.h
# End Source File
# Begin Source File

SOURCE=.\include\pxresult.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaaconf.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaallow.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaasm.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaausvc.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaauth.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaauthn.h
# End Source File
# Begin Source File

SOURCE=.\include\rmacfg.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaclsnk.h
# End Source File
# Begin Source File

SOURCE=.\include\rmacmenu.h
# End Source File
# Begin Source File

SOURCE=.\include\rmacomm.h
# End Source File
# Begin Source File

SOURCE=.\include\rmacore.h
# End Source File
# Begin Source File

SOURCE=.\include\rmadb.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaencod.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaengin.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaerror.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaevent.h
# End Source File
# Begin Source File

SOURCE=.\include\rmafiles.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaformt.h
# End Source File
# Begin Source File

SOURCE=.\include\rmagroup.h
# End Source File
# Begin Source File

SOURCE=.\include\rmahyper.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaiids.h
# End Source File
# Begin Source File

SOURCE=.\include\rmalvpix.h
# End Source File
# Begin Source File

SOURCE=.\include\rmalvtxt.h
# End Source File
# Begin Source File

SOURCE=.\include\rmamon.h
# End Source File
# Begin Source File

SOURCE=.\include\rmapckts.h
# End Source File
# Begin Source File

SOURCE=.\include\rmapends.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaphook.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaplgns.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaplugn.h
# End Source File
# Begin Source File

SOURCE=.\include\rmappv.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaprefs.h
# End Source File
# Begin Source File

SOURCE=.\include\rmapsink.h
# End Source File
# Begin Source File

SOURCE=.\include\rmarendr.h
# End Source File
# Begin Source File

SOURCE=.\include\rmasite2.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaslta.h
# End Source File
# Begin Source File

SOURCE=.\include\rmasrc.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaupgrd.h
# End Source File
# Begin Source File

SOURCE=.\include\rmavsurf.h
# End Source File
# Begin Source File

SOURCE=.\include\rmawin.h
# End Source File
# End Group
# Begin Group "Resource Files"

# PROP Default_Filter "ico;cur;bmp;dlg;rc2;rct;bin;rgs;gif;jpg;jpeg;jpe"
# End Group
# Begin Source File

SOURCE=.\ReadMe.txt
# End Source File
# Begin Source File

SOURCE=.\testdata\rmacom.py
# End Source File
# Begin Source File

SOURCE=.\testdata\rmatest.py
# End Source File
# Begin Source File

SOURCE=.\testdata\rmawin.py
# End Source File
# End Target
# End Project
