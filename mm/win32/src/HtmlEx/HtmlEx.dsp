# Microsoft Developer Studio Project File - Name="HtmlEx" - Package Owner=<4>
# Microsoft Developer Studio Generated Build File, Format Version 5.00
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Dynamic-Link Library" 0x0102

CFG=HtmlEx - Win32 Release
!MESSAGE This is not a valid makefile. To build this project using NMAKE,
!MESSAGE use the Export Makefile command and run
!MESSAGE 
!MESSAGE NMAKE /f "HtmlEx.mak".
!MESSAGE 
!MESSAGE You can specify a configuration when running NMAKE
!MESSAGE by defining the macro CFG on the command line. For example:
!MESSAGE 
!MESSAGE NMAKE /f "HtmlEx.mak" CFG="HtmlEx - Win32 Release"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "HtmlEx - Win32 Release" (based on "Win32 (x86) Dynamic-Link Library")
!MESSAGE "HtmlEx - Win32 Debug" (based on "Win32 (x86) Dynamic-Link Library")
!MESSAGE 

# Begin Project
# PROP Scc_ProjName ""
# PROP Scc_LocalPath ""
CPP=cl.exe
MTL=midl.exe
RSC=rc.exe

!IF  "$(CFG)" == "HtmlEx - Win32 Release"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir ".\Release"
# PROP BASE Intermediate_Dir ".\Release"
# PROP BASE Target_Dir ""
# PROP Use_MFC 2
# PROP Use_Debug_Libraries 0
# PROP Output_Dir "..\Build"
# PROP Intermediate_Dir "..\Build\Temp\HtmlEx\Release"
# PROP Ignore_Export_Lib 0
# PROP Target_Dir ""
F90=df.exe
# ADD BASE CPP /nologo /MT /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_WINDOWS" /YX /c
# ADD CPP /nologo /MD /W3 /GX /O2 /I "..\GRiNSRes" /D LEAVE=__LEAVE /D FINALLY=__FINALLY /D EXCEPT=__EXCEPT /D CRTAPI1=_cdecl /D CRTAPI2=_cdecl /D _X86=1 /D WINVER=0x0400 /D "_WINDLL" /D "_AFXDLL" /D "_MBCS" /FR /FD /c
# ADD BASE MTL /nologo /D "NDEBUG" /win32
# ADD MTL /nologo /D "NDEBUG" /mktyplib203 /win32
# ADD BASE RSC /l 0x408 /d "NDEBUG"
# ADD RSC /l 0x408 /d "NDEBUG" /d "_AFXDLL"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /machine:I386
# ADD LINK32 python15.lib /nologo /base:"0x1e240000" /subsystem:windows /dll /machine:I386 /out:"..\Build\Htmlex.pyd"
# SUBTRACT LINK32 /pdb:none /nodefaultlib

!ELSEIF  "$(CFG)" == "HtmlEx - Win32 Debug"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 1
# PROP BASE Output_Dir ".\Debug"
# PROP BASE Intermediate_Dir ".\Debug"
# PROP BASE Target_Dir ""
# PROP Use_MFC 2
# PROP Use_Debug_Libraries 1
# PROP Output_Dir "..\Build"
# PROP Intermediate_Dir "..\Build\Temp\htmlex\Debug"
# PROP Ignore_Export_Lib 0
# PROP Target_Dir ""
F90=df.exe
# ADD BASE CPP /nologo /MTd /W3 /Gm /GX /Zi /Od /D "WIN32" /D "_DEBUG" /D "_WINDOWS" /YX /c
# ADD CPP /nologo /MDd /W3 /Gm /GX /Zi /Od /I "..\GRiNSRes" /D "_DEBUG" /D "_WINDLL" /D "_AFXDLL" /D "_MBCS" /FR /FD /c
# SUBTRACT CPP /Gy /YX
# ADD BASE MTL /nologo /D "_DEBUG" /win32
# ADD MTL /nologo /D "_DEBUG" /mktyplib203 /win32
# ADD BASE RSC /l 0x408 /d "_DEBUG"
# ADD RSC /l 0x408 /d "_DEBUG" /d "_AFXDLL"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /debug /machine:I386
# ADD LINK32 python15_d.lib /nologo /base:"0x1e240000" /subsystem:windows /dll /debug /machine:I386 /out:"..\Build\Htmlex_d.pyd"
# SUBTRACT LINK32 /pdb:none /nodefaultlib

!ENDIF 

# Begin Target

# Name "HtmlEx - Win32 Release"
# Name "HtmlEx - Win32 Debug"
# Begin Group "Source Files"

# PROP Default_Filter "cpp;c;cxx;rc;def;r;odl;hpj;bat;for;f90"
# Begin Source File

SOURCE=.\ContainerWnd.cpp
# End Source File
# Begin Source File

SOURCE=.\Htmlexmodule.cpp
# End Source File
# Begin Source File

SOURCE=.\webbrowser.cpp
# End Source File
# End Group
# Begin Group "Header Files"

# PROP Default_Filter "h;hpp;hxx;hm;inl;fi;fd"
# Begin Source File

SOURCE=.\htmlex.h
# End Source File
# End Group
# Begin Group "Resource Files"

# PROP Default_Filter "ico;cur;bmp;dlg;rc2;rct;bin;cnt;rtf;gif;jpg;jpeg;jpe"
# Begin Source File

SOURCE=.\res\cmif.ico
# End Source File
# Begin Source File

SOURCE=.\res\cmif.rc2
# End Source File
# Begin Source File

SOURCE=.\Res\hand2.cur
# End Source File
# Begin Source File

SOURCE=.\res\pause.ico
# End Source File
# Begin Source File

SOURCE=.\res\play.ico
# End Source File
# Begin Source File

SOURCE=.\RES\python.ico
# End Source File
# Begin Source File

SOURCE=.\res\stop.ico
# End Source File
# End Group
# End Target
# End Project
# Section HtmlEx : {B7FC3597-8CE7-11CF-9754-00AA00C00908}
# 	2:5:Class:CDocOutput
# 	2:10:HeaderFile:docoutput.h
# 	2:8:ImplFile:docoutput.cpp
# End Section
# Section HtmlEx : {B7FC355E-8CE7-11CF-9754-00AA00C00908}
# 	0:8:Font.cpp:C:\RESEARCH\users\sol\projects\HtmlEx\Font.cpp
# 	0:6:HTML.h:C:\RESEARCH\users\sol\projects\HtmlEx\HTML.h
# 	0:12:DocHeaders.h:C:\RESEARCH\users\sol\projects\HtmlEx\DocHeaders.h
# 	0:6:Font.h:C:\RESEARCH\users\sol\projects\HtmlEx\Font.h
# 	0:8:HTML.cpp:C:\RESEARCH\users\sol\projects\HtmlEx\HTML.cpp
# 	0:10:DocInput.h:C:\RESEARCH\users\sol\projects\HtmlEx\DocInput.h
# 	0:13:DocHeader.cpp:C:\RESEARCH\users\sol\projects\HtmlEx\DocHeader.cpp
# 	0:10:HTMLForm.h:C:\RESEARCH\users\sol\projects\HtmlEx\HTMLForm.h
# 	0:12:DocInput.cpp:C:\RESEARCH\users\sol\projects\HtmlEx\DocInput.cpp
# 	0:11:DocOutput.h:C:\RESEARCH\users\sol\projects\HtmlEx\DocOutput.h
# 	0:13:DocOutput.cpp:C:\RESEARCH\users\sol\projects\HtmlEx\DocOutput.cpp
# 	0:11:HTMLForms.h:C:\RESEARCH\users\sol\projects\HtmlEx\HTMLForms.h
# 	0:11:DocHeader.h:C:\RESEARCH\users\sol\projects\HtmlEx\DocHeader.h
# 	0:12:HTMLForm.cpp:C:\RESEARCH\users\sol\projects\HtmlEx\HTMLForm.cpp
# 	0:13:HTMLForms.cpp:C:\RESEARCH\users\sol\projects\HtmlEx\HTMLForms.cpp
# 	0:14:DocHeaders.cpp:C:\RESEARCH\users\sol\projects\HtmlEx\DocHeaders.cpp
# 	2:21:DefaultSinkHeaderFile:html.h
# 	2:16:DefaultSinkClass:CHTML
# End Section
# Section HtmlEx : {B7FC3592-8CE7-11CF-9754-00AA00C00908}
# 	2:5:Class:CDocHeaders
# 	2:10:HeaderFile:docheaders.h
# 	2:8:ImplFile:docheaders.cpp
# End Section
# Section HtmlEx : {B7FC3551-8CE7-11CF-9754-00AA00C00908}
# 	2:5:Class:CHTMLForm
# 	2:10:HeaderFile:htmlform.h
# 	2:8:ImplFile:htmlform.cpp
# End Section
# Section HtmlEx : {B7FC3555-8CE7-11CF-9754-00AA00C00908}
# 	2:5:Class:CHTMLForms
# 	2:10:HeaderFile:htmlforms.h
# 	2:8:ImplFile:htmlforms.cpp
# End Section
# Section HtmlEx : {BEF6E003-A874-101A-8BBA-00AA00300CAB}
# 	2:5:Class:COleFont
# 	2:10:HeaderFile:font.h
# 	2:8:ImplFile:font.cpp
# End Section
# Section HtmlEx : {B7FC355C-8CE7-11CF-9754-00AA00C00908}
# 	2:5:Class:CHTML
# 	2:10:HeaderFile:html.h
# 	2:8:ImplFile:html.cpp
# End Section
# Section HtmlEx : {B7FC3595-8CE7-11CF-9754-00AA00C00908}
# 	2:5:Class:CDocInput
# 	2:10:HeaderFile:docinput.h
# 	2:8:ImplFile:docinput.cpp
# End Section
# Section OLE Controls
# 	{B7FC355E-8CE7-11CF-9754-00AA00C00908}
# End Section
# Section HtmlEx : {B7FC3590-8CE7-11CF-9754-00AA00C00908}
# 	2:5:Class:CDocHeader
# 	2:10:HeaderFile:docheader.h
# 	2:8:ImplFile:docheader.cpp
# End Section
