# Microsoft Developer Studio Generated NMAKE File, Format Version 4.20
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Dynamic-Link Library" 0x0102

!IF "$(CFG)" == ""
CFG=soundex - Win32 Debug
!MESSAGE No configuration specified.  Defaulting to soundex - Win32 Debug.
!ENDIF 

!IF "$(CFG)" != "soundex - Win32 Release" && "$(CFG)" !=\
 "soundex - Win32 Debug"
!MESSAGE Invalid configuration "$(CFG)" specified.
!MESSAGE You can specify a configuration when running NMAKE on this makefile
!MESSAGE by defining the macro CFG on the command line.  For example:
!MESSAGE 
!MESSAGE NMAKE /f "soundex.mak" CFG="soundex - Win32 Debug"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "soundex - Win32 Release" (based on\
 "Win32 (x86) Dynamic-Link Library")
!MESSAGE "soundex - Win32 Debug" (based on "Win32 (x86) Dynamic-Link Library")
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
# PROP Target_Last_Scanned "soundex - Win32 Debug"
CPP=cl.exe
RSC=rc.exe
MTL=mktyplib.exe

!IF  "$(CFG)" == "soundex - Win32 Release"

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

ALL : ".\dsoundex.pyd" "$(OUTDIR)\soundex.bsc"

CLEAN : 
	-@erase "$(INTDIR)\assert.obj"
	-@erase "$(INTDIR)\assert.sbr"
	-@erase "$(INTDIR)\AudioStream.obj"
	-@erase "$(INTDIR)\AudioStream.sbr"
	-@erase "$(INTDIR)\soundmodule.obj"
	-@erase "$(INTDIR)\soundmodule.sbr"
	-@erase "$(INTDIR)\Timer.obj"
	-@erase "$(INTDIR)\Timer.sbr"
	-@erase "$(INTDIR)\WaveFile.obj"
	-@erase "$(INTDIR)\WaveFile.sbr"
	-@erase "$(OUTDIR)\dsoundex.exp"
	-@erase "$(OUTDIR)\dsoundex.lib"
	-@erase "$(OUTDIR)\soundex.bsc"
	-@erase ".\dsoundex.pyd"

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
BSC32_FLAGS=/nologo /o"$(OUTDIR)/soundex.bsc" 
BSC32_SBRS= \
	"$(INTDIR)\assert.sbr" \
	"$(INTDIR)\AudioStream.sbr" \
	"$(INTDIR)\soundmodule.sbr" \
	"$(INTDIR)\Timer.sbr" \
	"$(INTDIR)\WaveFile.sbr"

"$(OUTDIR)\soundex.bsc" : "$(OUTDIR)" $(BSC32_SBRS)
    $(BSC32) @<<
  $(BSC32_FLAGS) $(BSC32_SBRS)
<<

LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /machine:I386
# ADD LINK32 Python.Lib win32ui.lib winmm.lib dsound.lib /nologo /base:0x1e240000 /subsystem:windows /dll /machine:I386 /out:"dsoundex.pyd"
# SUBTRACT LINK32 /pdb:none /nodefaultlib
LINK32_FLAGS=Python.Lib win32ui.lib winmm.lib dsound.lib /nologo\
 /base:0x1e240000 /subsystem:windows /dll /incremental:no\
 /pdb:"$(OUTDIR)/dsoundex.pdb" /machine:I386 /out:"dsoundex.pyd"\
 /implib:"$(OUTDIR)/dsoundex.lib" 
LINK32_OBJS= \
	"$(INTDIR)\assert.obj" \
	"$(INTDIR)\AudioStream.obj" \
	"$(INTDIR)\soundmodule.obj" \
	"$(INTDIR)\Timer.obj" \
	"$(INTDIR)\WaveFile.obj"

".\dsoundex.pyd" : "$(OUTDIR)" $(DEF_FILE) $(LINK32_OBJS)
    $(LINK32) @<<
  $(LINK32_FLAGS) $(LINK32_OBJS)
<<

!ELSEIF  "$(CFG)" == "soundex - Win32 Debug"

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

ALL : ".\dsoundex.pyd" "$(OUTDIR)\soundex.bsc"

CLEAN : 
	-@erase "$(INTDIR)\assert.obj"
	-@erase "$(INTDIR)\assert.sbr"
	-@erase "$(INTDIR)\AudioStream.obj"
	-@erase "$(INTDIR)\AudioStream.sbr"
	-@erase "$(INTDIR)\soundmodule.obj"
	-@erase "$(INTDIR)\soundmodule.sbr"
	-@erase "$(INTDIR)\Timer.obj"
	-@erase "$(INTDIR)\Timer.sbr"
	-@erase "$(INTDIR)\vc40.idb"
	-@erase "$(INTDIR)\vc40.pdb"
	-@erase "$(INTDIR)\WaveFile.obj"
	-@erase "$(INTDIR)\WaveFile.sbr"
	-@erase "$(OUTDIR)\dsoundex.exp"
	-@erase "$(OUTDIR)\dsoundex.lib"
	-@erase "$(OUTDIR)\dsoundex.pdb"
	-@erase "$(OUTDIR)\soundex.bsc"
	-@erase ".\dsoundex.ilk"
	-@erase ".\dsoundex.pyd"

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
BSC32_FLAGS=/nologo /o"$(OUTDIR)/soundex.bsc" 
BSC32_SBRS= \
	"$(INTDIR)\assert.sbr" \
	"$(INTDIR)\AudioStream.sbr" \
	"$(INTDIR)\soundmodule.sbr" \
	"$(INTDIR)\Timer.sbr" \
	"$(INTDIR)\WaveFile.sbr"

"$(OUTDIR)\soundex.bsc" : "$(OUTDIR)" $(BSC32_SBRS)
    $(BSC32) @<<
  $(BSC32_FLAGS) $(BSC32_SBRS)
<<

LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /debug /machine:I386
# ADD LINK32 Python.Lib win32ui.lib winmm.lib dsound.lib /nologo /base:0x1e240000 /subsystem:windows /dll /debug /machine:I386 /out:"dsoundex.pyd"
# SUBTRACT LINK32 /pdb:none /nodefaultlib
LINK32_FLAGS=Python.Lib win32ui.lib winmm.lib dsound.lib /nologo\
 /base:0x1e240000 /subsystem:windows /dll /incremental:yes\
 /pdb:"$(OUTDIR)/dsoundex.pdb" /debug /machine:I386 /out:"dsoundex.pyd"\
 /implib:"$(OUTDIR)/dsoundex.lib" 
LINK32_OBJS= \
	"$(INTDIR)\assert.obj" \
	"$(INTDIR)\AudioStream.obj" \
	"$(INTDIR)\soundmodule.obj" \
	"$(INTDIR)\Timer.obj" \
	"$(INTDIR)\WaveFile.obj"

".\dsoundex.pyd" : "$(OUTDIR)" $(DEF_FILE) $(LINK32_OBJS)
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

# Name "soundex - Win32 Release"
# Name "soundex - Win32 Debug"

!IF  "$(CFG)" == "soundex - Win32 Release"

!ELSEIF  "$(CFG)" == "soundex - Win32 Debug"

!ENDIF 

################################################################################
# Begin Source File

SOURCE=.\assert.c
DEP_CPP_ASSER=\
	".\assert.h"\
	

"$(INTDIR)\assert.obj" : $(SOURCE) $(DEP_CPP_ASSER) "$(INTDIR)"

"$(INTDIR)\assert.sbr" : $(SOURCE) $(DEP_CPP_ASSER) "$(INTDIR)"


# End Source File
################################################################################
# Begin Source File

SOURCE=.\AudioStream.cpp
DEP_CPP_AUDIO=\
	".\assert.h"\
	".\audiostream.h"\
	".\timer.h"\
	".\wavefile.h"\
	

"$(INTDIR)\AudioStream.obj" : $(SOURCE) $(DEP_CPP_AUDIO) "$(INTDIR)"

"$(INTDIR)\AudioStream.sbr" : $(SOURCE) $(DEP_CPP_AUDIO) "$(INTDIR)"


# End Source File
################################################################################
# Begin Source File

SOURCE=.\soundmodule.cpp
DEP_CPP_SOUND=\
	".\audiostream.h"\
	".\cmifex.h"\
	".\sampledll.h"\
	".\StdAfx.h"\
	".\timer.h"\
	".\wavefile.h"\
	"D:\Python1.4\Src\Include\accessobject.h"\
	"D:\Python1.4\Src\Include\bltinmodule.h"\
	"D:\Python1.4\Src\Include\ceval.h"\
	"D:\Python1.4\Src\Include\classobject.h"\
	"D:\Python1.4\Src\Include\cobject.h"\
	"D:\Python1.4\Src\Include\complexobject.h"\
	"D:\Python1.4\Src\Include\config.h"\
	"D:\Python1.4\Src\Include\fileobject.h"\
	"D:\Python1.4\Src\Include\floatobject.h"\
	"D:\Python1.4\Src\Include\funcobject.h"\
	"D:\Python1.4\Src\Include\import.h"\
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
	"D:\Python1.4\Src\Include\pythonrun.h"\
	"D:\Python1.4\Src\Include\rangeobject.h"\
	"D:\Python1.4\Src\Include\rename2.h"\
	"D:\Python1.4\Src\Include\sliceobject.h"\
	"D:\Python1.4\Src\Include\stringobject.h"\
	"D:\Python1.4\Src\Include\sysmodule.h"\
	"D:\Python1.4\Src\Include\thread.h"\
	"D:\Python1.4\Src\Include\traceback.h"\
	"D:\Python1.4\Src\Include\tupleobject.h"\
	{$(INCLUDE)}"\abstract.h"\
	{$(INCLUDE)}"\allobjects.h"\
	{$(INCLUDE)}"\modsupport.h"\
	

"$(INTDIR)\soundmodule.obj" : $(SOURCE) $(DEP_CPP_SOUND) "$(INTDIR)"

"$(INTDIR)\soundmodule.sbr" : $(SOURCE) $(DEP_CPP_SOUND) "$(INTDIR)"


# End Source File
################################################################################
# Begin Source File

SOURCE=.\Timer.cpp
DEP_CPP_TIMER=\
	".\assert.h"\
	".\timer.h"\
	

"$(INTDIR)\Timer.obj" : $(SOURCE) $(DEP_CPP_TIMER) "$(INTDIR)"

"$(INTDIR)\Timer.sbr" : $(SOURCE) $(DEP_CPP_TIMER) "$(INTDIR)"


# End Source File
################################################################################
# Begin Source File

SOURCE=.\WaveFile.cpp
DEP_CPP_WAVEF=\
	".\assert.h"\
	".\wavefile.h"\
	

"$(INTDIR)\WaveFile.obj" : $(SOURCE) $(DEP_CPP_WAVEF) "$(INTDIR)"

"$(INTDIR)\WaveFile.sbr" : $(SOURCE) $(DEP_CPP_WAVEF) "$(INTDIR)"


# End Source File
# End Target
# End Project
################################################################################
