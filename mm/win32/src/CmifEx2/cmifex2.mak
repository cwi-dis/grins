# Microsoft Developer Studio Generated NMAKE File, Format Version 4.20
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Dynamic-Link Library" 0x0102

!IF "$(CFG)" == ""
CFG=cmifex2 - Win32 Debug
!MESSAGE No configuration specified.  Defaulting to cmifex2 - Win32 Debug.
!ENDIF 

!IF "$(CFG)" != "cmifex2 - Win32 Release" && "$(CFG)" !=\
 "cmifex2 - Win32 Debug"
!MESSAGE Invalid configuration "$(CFG)" specified.
!MESSAGE You can specify a configuration when running NMAKE on this makefile
!MESSAGE by defining the macro CFG on the command line.  For example:
!MESSAGE 
!MESSAGE NMAKE /f "cmifex2.mak" CFG="cmifex2 - Win32 Debug"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "cmifex2 - Win32 Release" (based on\
 "Win32 (x86) Dynamic-Link Library")
!MESSAGE "cmifex2 - Win32 Debug" (based on "Win32 (x86) Dynamic-Link Library")
!MESSAGE 
!ERROR An invalid configuration is specified.
!ENDIF 

!IF "$(OS)" == "Windows_NT"
NULL=
!ELSE 
NULL=nul
!ENDIF 
################################################################################
# Begin Project
# PROP Target_Last_Scanned "cmifex2 - Win32 Release"
RSC=rc.exe
MTL=mktyplib.exe
CPP=cl.exe

!IF  "$(CFG)" == "cmifex2 - Win32 Release"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir "Release"
# PROP BASE Intermediate_Dir "Release"
# PROP BASE Target_Dir ""
# PROP Use_MFC 2
# PROP Use_Debug_Libraries 0
# PROP Output_Dir "Release"
# PROP Intermediate_Dir "Release"
# PROP Target_Dir ""
OUTDIR=.\Release
INTDIR=.\Release

ALL : ".\debug\cmifex2.pyd" "$(OUTDIR)\cmifex2.bsc"

CLEAN : 
	-@erase "$(INTDIR)\cmifmodule2.obj"
	-@erase "$(INTDIR)\cmifmodule2.sbr"
	-@erase "$(OUTDIR)\cmifex2.bsc"
	-@erase "$(OUTDIR)\cmifex2.exp"
	-@erase "$(OUTDIR)\cmifex2.lib"
	-@erase ".\debug\cmifex2.pyd"

"$(OUTDIR)" :
    if not exist "$(OUTDIR)/$(NULL)" mkdir "$(OUTDIR)"

# ADD BASE CPP /nologo /MT /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_WINDOWS" /YX /c
# ADD CPP /nologo /MD /W3 /GX /Od /D "_AFXDLL" /D "USE_DL_IMPORT" /D "HAVE_CONFIG_H" /D LEAVE=__LEAVE /D FINALLY=__FINALLY /D EXCEPT=__EXCEPT /D CRTAPI1=_cdecl /D CRTAPI2=_cdecl /D _X86=1 /D WINVER=0x0400 /D "_WINDLL" /D "_MBCS" /FR /c
CPP_PROJ=/nologo /MD /W3 /GX /Od /D "_AFXDLL" /D "USE_DL_IMPORT" /D\
 "HAVE_CONFIG_H" /D LEAVE=__LEAVE /D FINALLY=__FINALLY /D EXCEPT=__EXCEPT /D\
 CRTAPI1=_cdecl /D CRTAPI2=_cdecl /D _X86=1 /D WINVER=0x0400 /D "_WINDLL" /D\
 "_MBCS" /FR"$(INTDIR)/" /Fo"$(INTDIR)/" /c 
CPP_OBJS=.\Release/
CPP_SBRS=.\Release/
# ADD BASE MTL /nologo /D "NDEBUG" /win32
# ADD MTL /nologo /D "NDEBUG" /win32
MTL_PROJ=/nologo /D "NDEBUG" /win32 
# ADD BASE RSC /l 0x408 /d "NDEBUG"
# ADD RSC /l 0x408 /d "NDEBUG" /d "_AFXDLL"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
BSC32_FLAGS=/nologo /o"$(OUTDIR)/cmifex2.bsc" 
BSC32_SBRS= \
	"$(INTDIR)\cmifmodule2.sbr"

"$(OUTDIR)\cmifex2.bsc" : "$(OUTDIR)" $(BSC32_SBRS)
    $(BSC32) @<<
  $(BSC32_FLAGS) $(BSC32_SBRS)
<<

LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /machine:I386
# ADD LINK32 Python.Lib win32ui.lib /nologo /base:0x1e240000 /subsystem:windows /dll /machine:I386 /out:".\debug\cmifex2.pyd"
# SUBTRACT LINK32 /pdb:none /nodefaultlib
LINK32_FLAGS=Python.Lib win32ui.lib /nologo /base:0x1e240000 /subsystem:windows\
 /dll /incremental:no /pdb:"$(OUTDIR)/cmifex2.pdb" /machine:I386\
 /out:".\debug\cmifex2.pyd" /implib:"$(OUTDIR)/cmifex2.lib" 
LINK32_OBJS= \
	"$(INTDIR)\cmifmodule2.obj"

".\debug\cmifex2.pyd" : "$(OUTDIR)" $(DEF_FILE) $(LINK32_OBJS)
    $(LINK32) @<<
  $(LINK32_FLAGS) $(LINK32_OBJS)
<<

!ELSEIF  "$(CFG)" == "cmifex2 - Win32 Debug"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 1
# PROP BASE Output_Dir "Debug"
# PROP BASE Intermediate_Dir "Debug"
# PROP BASE Target_Dir ""
# PROP Use_MFC 2
# PROP Use_Debug_Libraries 1
# PROP Output_Dir "Debug"
# PROP Intermediate_Dir "Debug"
# PROP Target_Dir ""
OUTDIR=.\Debug
INTDIR=.\Debug

ALL : "$(OUTDIR)\cmifex2.pyd" "$(OUTDIR)\cmifex2.bsc"

CLEAN : 
	-@erase "$(INTDIR)\cmifmodule2.obj"
	-@erase "$(INTDIR)\cmifmodule2.sbr"
	-@erase "$(INTDIR)\vc40.idb"
	-@erase "$(INTDIR)\vc40.pdb"
	-@erase "$(OUTDIR)\cmifex2.bsc"
	-@erase "$(OUTDIR)\cmifex2.exp"
	-@erase "$(OUTDIR)\cmifex2.ilk"
	-@erase "$(OUTDIR)\cmifex2.lib"
	-@erase "$(OUTDIR)\cmifex2.pdb"
	-@erase "$(OUTDIR)\cmifex2.pyd"

"$(OUTDIR)" :
    if not exist "$(OUTDIR)/$(NULL)" mkdir "$(OUTDIR)"

# ADD BASE CPP /nologo /MTd /W3 /Gm /GX /Zi /Od /D "WIN32" /D "_DEBUG" /D "_WINDOWS" /YX /c
# ADD CPP /nologo /MDd /W3 /Gm /GX /Zi /Od /D "_DEBUG" /D "USE_DL_IMPORT" /D "HAVE_CONFIG_H" /D "_WINDLL" /D "_AFXDLL" /D "_MBCS" /FR /c
# SUBTRACT CPP /Gy /YX
CPP_PROJ=/nologo /MDd /W3 /Gm /GX /Zi /Od /D "_DEBUG" /D "USE_DL_IMPORT" /D\
 "HAVE_CONFIG_H" /D "_WINDLL" /D "_AFXDLL" /D "_MBCS" /FR"$(INTDIR)/"\
 /Fo"$(INTDIR)/" /Fd"$(INTDIR)/" /c 
CPP_OBJS=.\Debug/
CPP_SBRS=.\Debug/
# ADD BASE MTL /nologo /D "_DEBUG" /win32
# ADD MTL /nologo /D "_DEBUG" /win32
MTL_PROJ=/nologo /D "_DEBUG" /win32 
# ADD BASE RSC /l 0x408 /d "_DEBUG"
# ADD RSC /l 0x408 /d "_DEBUG" /d "_AFXDLL"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
BSC32_FLAGS=/nologo /o"$(OUTDIR)/cmifex2.bsc" 
BSC32_SBRS= \
	"$(INTDIR)\cmifmodule2.sbr"

"$(OUTDIR)\cmifex2.bsc" : "$(OUTDIR)" $(BSC32_SBRS)
    $(BSC32) @<<
  $(BSC32_FLAGS) $(BSC32_SBRS)
<<

LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /debug /machine:I386
# ADD LINK32 Python.Lib win32ui.lib /nologo /base:0x1e240000 /subsystem:windows /dll /debug /machine:I386 /out:".\debug\cmifex2.pyd"
# SUBTRACT LINK32 /pdb:none /nodefaultlib
LINK32_FLAGS=Python.Lib win32ui.lib /nologo /base:0x1e240000 /subsystem:windows\
 /dll /incremental:yes /pdb:"$(OUTDIR)/cmifex2.pdb" /debug /machine:I386\
 /out:"$(OUTDIR)/cmifex2.pyd" /implib:"$(OUTDIR)/cmifex2.lib" 
LINK32_OBJS= \
	"$(INTDIR)\cmifmodule2.obj"

"$(OUTDIR)\cmifex2.pyd" : "$(OUTDIR)" $(DEF_FILE) $(LINK32_OBJS)
    $(LINK32) @<<
  $(LINK32_FLAGS) $(LINK32_OBJS)
<<

!ENDIF 

.c{$(CPP_OBJS)}.obj:
   $(CPP) $(CPP_PROJ) $<  

.cpp{$(CPP_OBJS)}.obj:
   $(CPP) $(CPP_PROJ) $<  

.cxx{$(CPP_OBJS)}.obj:
   $(CPP) $(CPP_PROJ) $<  

.c{$(CPP_SBRS)}.sbr:
   $(CPP) $(CPP_PROJ) $<  

.cpp{$(CPP_SBRS)}.sbr:
   $(CPP) $(CPP_PROJ) $<  

.cxx{$(CPP_SBRS)}.sbr:
   $(CPP) $(CPP_PROJ) $<  

################################################################################
# Begin Target

# Name "cmifex2 - Win32 Release"
# Name "cmifex2 - Win32 Debug"

!IF  "$(CFG)" == "cmifex2 - Win32 Release"

!ELSEIF  "$(CFG)" == "cmifex2 - Win32 Debug"

!ENDIF 

################################################################################
# Begin Source File

SOURCE=.\cmifmodule2.cpp

!IF  "$(CFG)" == "cmifex2 - Win32 Release"

DEP_CPP_CMIFM=\
	".\cmifex.h"\
	".\Ezfont.h"\
	"D:\Python1.4\Src\Include\abstract.h"\
	"D:\Python1.4\Src\Include\accessobject.h"\
	"D:\Python1.4\Src\Include\allobjects.h"\
	"D:\Python1.4\Src\Include\bltinmodule.h"\
	"D:\Python1.4\Src\Include\ceval.h"\
	"D:\Python1.4\Src\Include\classobject.h"\
	"D:\Python1.4\Src\Include\cobject.h"\
	"D:\Python1.4\Src\Include\complexobject.h"\
	"D:\Python1.4\Src\Include\config.h"\
	"D:\Python1.4\Src\Include\fileobject.h"\
	"D:\Python1.4\Src\Include\floatobject.h"\
	"D:\Python1.4\Src\Include\funcobject.h"\
	"D:\Python1.4\Src\Include\intobject.h"\
	"D:\Python1.4\Src\Include\intrcheck.h"\
	"D:\Python1.4\Src\Include\listobject.h"\
	"D:\Python1.4\Src\Include\longobject.h"\
	"D:\Python1.4\Src\Include\mappingobject.h"\
	"D:\Python1.4\Src\Include\methodobject.h"\
	"D:\Python1.4\Src\Include\moduleobject.h"\
	"D:\Python1.4\Src\Include\mymalloc.h"\
	"D:\Python1.4\Src\Include\myproto.h"\
	"D:\Python1.4\Src\Include\object.h"\
	"D:\Python1.4\Src\Include\objimpl.h"\
	"D:\Python1.4\Src\Include\pydebug.h"\
	"D:\Python1.4\Src\Include\pyerrors.h"\
	"D:\Python1.4\Src\Include\rangeobject.h"\
	"D:\Python1.4\Src\Include\rename2.h"\
	"D:\Python1.4\Src\Include\sliceobject.h"\
	"D:\Python1.4\Src\Include\stringobject.h"\
	"D:\Python1.4\Src\Include\sysmodule.h"\
	"D:\Python1.4\Src\Include\thread.h"\
	"D:\Python1.4\Src\Include\tupleobject.h"\
	"D:\Python1.4\Src\pythonwi\pythondlg.h"\
	"D:\Python1.4\Src\pythonwi\pythondoc.h"\
	"D:\Python1.4\Src\pythonwi\pythoneditview.h"\
	"D:\Python1.4\Src\pythonwi\pythonframe.h"\
	"D:\Python1.4\Src\pythonwi\pythonppage.h"\
	"D:\Python1.4\Src\pythonwi\pythonpsheet.h"\
	"D:\Python1.4\Src\pythonwi\pythonview.h"\
	"D:\Python1.4\Src\pythonwi\win32app.h"\
	"D:\Python1.4\Src\pythonwi\win32assoc.h"\
	"D:\Python1.4\Src\pythonwi\win32cmd.h"\
	"D:\Python1.4\Src\pythonwi\win32ui.h"\
	{$(INCLUDE)}"\graminit.h"\
	{$(INCLUDE)}"\import.h"\
	{$(INCLUDE)}"\modsupport.h"\
	{$(INCLUDE)}"\Python.h"\
	{$(INCLUDE)}"\pythonrun.h"\
	{$(INCLUDE)}"\stdafx.h"\
	{$(INCLUDE)}"\traceback.h"\
	{$(INCLUDE)}"\win32win.h"\
	

"$(INTDIR)\cmifmodule2.obj" : $(SOURCE) $(DEP_CPP_CMIFM) "$(INTDIR)"

"$(INTDIR)\cmifmodule2.sbr" : $(SOURCE) $(DEP_CPP_CMIFM) "$(INTDIR)"


!ELSEIF  "$(CFG)" == "cmifex2 - Win32 Debug"

DEP_CPP_CMIFM=\
	".\cmifex.h"\
	".\Ezfont.h"\
	"D:\Python1.4\Src\Include\abstract.h"\
	"D:\Python1.4\Src\Include\accessobject.h"\
	"D:\Python1.4\Src\Include\allobjects.h"\
	"D:\Python1.4\Src\Include\bltinmodule.h"\
	"D:\Python1.4\Src\Include\ceval.h"\
	"D:\Python1.4\Src\Include\classobject.h"\
	"D:\Python1.4\Src\Include\cobject.h"\
	"D:\Python1.4\Src\Include\complexobject.h"\
	"D:\Python1.4\Src\Include\config.h"\
	"D:\Python1.4\Src\Include\fileobject.h"\
	"D:\Python1.4\Src\Include\floatobject.h"\
	"D:\Python1.4\Src\Include\funcobject.h"\
	"D:\Python1.4\Src\Include\intobject.h"\
	"D:\Python1.4\Src\Include\intrcheck.h"\
	"D:\Python1.4\Src\Include\listobject.h"\
	"D:\Python1.4\Src\Include\longobject.h"\
	"D:\Python1.4\Src\Include\mappingobject.h"\
	"D:\Python1.4\Src\Include\methodobject.h"\
	"D:\Python1.4\Src\Include\moduleobject.h"\
	"D:\Python1.4\Src\Include\mymalloc.h"\
	"D:\Python1.4\Src\Include\myproto.h"\
	"D:\Python1.4\Src\Include\object.h"\
	"D:\Python1.4\Src\Include\objimpl.h"\
	"D:\Python1.4\Src\Include\pydebug.h"\
	"D:\Python1.4\Src\Include\pyerrors.h"\
	"D:\Python1.4\Src\Include\rangeobject.h"\
	"D:\Python1.4\Src\Include\rename2.h"\
	"D:\Python1.4\Src\Include\sliceobject.h"\
	"D:\Python1.4\Src\Include\stringobject.h"\
	"D:\Python1.4\Src\Include\sysmodule.h"\
	"D:\Python1.4\Src\Include\thread.h"\
	"D:\Python1.4\Src\Include\tupleobject.h"\
	"D:\Python1.4\Src\pythonwi\pythondlg.h"\
	"D:\Python1.4\Src\pythonwi\pythondoc.h"\
	"D:\Python1.4\Src\pythonwi\pythoneditview.h"\
	"D:\Python1.4\Src\pythonwi\pythonframe.h"\
	"D:\Python1.4\Src\pythonwi\pythonppage.h"\
	"D:\Python1.4\Src\pythonwi\pythonpsheet.h"\
	"D:\Python1.4\Src\pythonwi\pythonview.h"\
	"D:\Python1.4\Src\pythonwi\win32app.h"\
	"D:\Python1.4\Src\pythonwi\win32assoc.h"\
	"D:\Python1.4\Src\pythonwi\win32cmd.h"\
	"D:\Python1.4\Src\pythonwi\win32ui.h"\
	{$(INCLUDE)}"\graminit.h"\
	{$(INCLUDE)}"\import.h"\
	{$(INCLUDE)}"\modsupport.h"\
	{$(INCLUDE)}"\Python.h"\
	{$(INCLUDE)}"\pythonrun.h"\
	{$(INCLUDE)}"\stdafx.h"\
	{$(INCLUDE)}"\traceback.h"\
	{$(INCLUDE)}"\win32win.h"\
	

"$(INTDIR)\cmifmodule2.obj" : $(SOURCE) $(DEP_CPP_CMIFM) "$(INTDIR)"

"$(INTDIR)\cmifmodule2.sbr" : $(SOURCE) $(DEP_CPP_CMIFM) "$(INTDIR)"


!ENDIF 

# End Source File
# End Target
# End Project
################################################################################
