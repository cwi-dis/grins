# Microsoft Developer Studio Project File - Name="GRiNSRes" - Package Owner=<4>
# Microsoft Developer Studio Generated Build File, Format Version 6.00
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Dynamic-Link Library" 0x0102

CFG=GRiNSRes - Win32 Release
!MESSAGE This is not a valid makefile. To build this project using NMAKE,
!MESSAGE use the Export Makefile command and run
!MESSAGE 
!MESSAGE NMAKE /f "GRiNSRes.mak".
!MESSAGE 
!MESSAGE You can specify a configuration when running NMAKE
!MESSAGE by defining the macro CFG on the command line. For example:
!MESSAGE 
!MESSAGE NMAKE /f "GRiNSRes.mak" CFG="GRiNSRes - Win32 Release"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "GRiNSRes - Win32 Release" (based on "Win32 (x86) Dynamic-Link Library")
!MESSAGE 

# Begin Project
# PROP AllowPerConfigDependencies 0
# PROP Scc_ProjName ""
# PROP Scc_LocalPath ""
CPP=cl.exe
MTL=midl.exe
RSC=rc.exe
# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir "Release"
# PROP BASE Intermediate_Dir "Release"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 0
# PROP Output_Dir "..\Build"
# PROP Intermediate_Dir "..\Build\Temp\GRiNSRes\Release"
# PROP Ignore_Export_Lib 0
# PROP Target_Dir ""
F90=df.exe
# ADD BASE CPP /nologo /MT /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_WINDOWS" /YX /FD /c
# ADD CPP /nologo /MT /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_WINDOWS" /FR /YX /FD /c
# ADD BASE MTL /nologo /D "NDEBUG" /mktyplib203 /o "NUL" /win32
# ADD MTL /nologo /D "NDEBUG" /mktyplib203 /o "NUL" /win32
# ADD BASE RSC /l 0xc09 /d "NDEBUG"
# ADD RSC /l 0x409 /d "NDEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /machine:I386
# ADD LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /pdb:none /machine:I386 /noentry
# Begin Custom Build - Generating grinsRC.py
OutDir=.\..\Build
InputPath=\ufs\mm\cmif\win32\src\Build\GRiNSRes.dll
SOURCE="$(InputPath)"

BuildCmds= \
	..\..\..\..\python\PCbuild\python ..\..\..\..\python\tools\scripts\h2py.py  GRiNSRes.h \
	copy GRiNSRes.py $(OutDir)\grinsRC.py \
	del GRiNSRes.py \
	del ..\..\..\bin\win32\GRiNSRes.dll \
	copy $(OutDir)\GRiNSRes.dll ..\..\..\bin\win32 \
	

"$(OutDir)\grinsRC.py" : $(SOURCE) "$(INTDIR)" "$(OUTDIR)"
   $(BuildCmds)

"..\..\..\bin\win32\GRiNSRes.dll" : $(SOURCE) "$(INTDIR)" "$(OUTDIR)"
   $(BuildCmds)
# End Custom Build
# Begin Target

# Name "GRiNSRes - Win32 Release"
# Begin Group "Resources"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\RES\animatio.ico
# End Source File
# Begin Source File

SOURCE=.\RES\causeeve.ico
# End Source File
# Begin Source File

SOURCE=.\RES\Drag.cur
# End Source File
# Begin Source File

SOURCE=.\RES\draghand.cur
# End Source File
# Begin Source File

SOURCE=.\RES\Draglink.cur
# End Source File
# Begin Source File

SOURCE=.\RES\DragMove.cur
# End Source File
# Begin Source File

SOURCE=.\RES\duration.ico
# End Source File
# Begin Source File

SOURCE=.\RES\eventin.ico
# End Source File
# Begin Source File

SOURCE=.\RES\eventout.ico
# End Source File
# Begin Source File

SOURCE=.\RES\Excl_close.ico
# End Source File
# Begin Source File

SOURCE=.\RES\Excl_open.ico
# End Source File
# Begin Source File

SOURCE=.\RES\focusin.ico
# End Source File
# Begin Source File

SOURCE=.\RES\grins_ed.ico
# End Source File
# Begin Source File

SOURCE=.\RES\grinsbar.bmp
# End Source File
# Begin Source File

SOURCE=.\RES\GRiNSed.ico
# End Source File
# Begin Source File

SOURCE=..\Build\grinsRC.py
# End Source File
# Begin Source File

SOURCE=.\GRiNSRes.h
# End Source File
# Begin Source File

SOURCE=.\GRiNSRes.rc
# End Source File
# Begin Source File

SOURCE=.\RES\hand.cur
# End Source File
# Begin Source File

SOURCE=.\RES\happyfac.ico
# End Source File
# Begin Source File

SOURCE=.\Res\html.bmp
# End Source File
# Begin Source File

SOURCE=.\RES\ico00001.ico
# End Source File
# Begin Source File

SOURCE=.\RES\ico00002.ico
# End Source File
# Begin Source File

SOURCE=.\RES\ico00003.ico
# End Source File
# Begin Source File

SOURCE=.\RES\ico00004.ico
# End Source File
# Begin Source File

SOURCE=.\RES\ico00005.ico
# End Source File
# Begin Source File

SOURCE=.\RES\ico00006.ico
# End Source File
# Begin Source File

SOURCE=.\RES\ico00007.ico
# End Source File
# Begin Source File

SOURCE=.\RES\ico00008.ico
# End Source File
# Begin Source File

SOURCE=.\RES\ico00009.ico
# End Source File
# Begin Source File

SOURCE=.\RES\ico00010.ico
# End Source File
# Begin Source File

SOURCE=.\RES\ico00011.ico
# End Source File
# Begin Source File

SOURCE=.\RES\icon1.ico
# End Source File
# Begin Source File

SOURCE=.\RES\icon_lin.ico
# End Source File
# Begin Source File

SOURCE=.\RES\icon_ope.ico
# End Source File
# Begin Source File

SOURCE=.\RES\idle.ico
# End Source File
# Begin Source File

SOURCE=.\Res\image.bmp
# End Source File
# Begin Source File

SOURCE="..\..\..\Build\products\g2-15\pro\intransition.ICO"
# End Source File
# Begin Source File

SOURCE=.\RES\intransition.ICO
# End Source File
# Begin Source File

SOURCE=.\RES\Nodrop.cur
# End Source File
# Begin Source File

SOURCE="..\..\..\Build\products\g2-15\pro\outtransition.ICO"
# End Source File
# Begin Source File

SOURCE=.\RES\outtransition.ICO
# End Source File
# Begin Source File

SOURCE=.\RES\Par_close.ico
# End Source File
# Begin Source File

SOURCE=.\RES\Par_open.ico
# End Source File
# Begin Source File

SOURCE=.\RES\pause.ico
# End Source File
# Begin Source File

SOURCE=.\RES\play.ico
# End Source File
# Begin Source File

SOURCE=.\RES\player8bit.bmp
# End Source File
# Begin Source File

SOURCE=.\RES\playing.ico
# End Source File
# Begin Source File

SOURCE=.\RES\Prio_close.ico
# End Source File
# Begin Source File

SOURCE=.\RES\Prio_open.ico
# End Source File
# Begin Source File

SOURCE=.\Res\region.bmp
# End Source File
# Begin Source File

SOURCE=.\RES\repeat.ico
# End Source File
# Begin Source File

SOURCE=.\RES\Seq_close.ico
# End Source File
# Begin Source File

SOURCE=.\RES\Seq_open.ico
# End Source File
# Begin Source File

SOURCE=.\Res\sound.bmp
# End Source File
# Begin Source File

SOURCE=.\RES\spaceman.ico
# End Source File
# Begin Source File

SOURCE="..\..\..\Build\products\g2-15\lite\splash8bit.bmp"
# End Source File
# Begin Source File

SOURCE="..\..\..\Build\products\g2-15\pro\splash8bit.bmp"
# End Source File
# Begin Source File

SOURCE=..\..\..\Build\products\qt\pro\splash8bit.bmp
# End Source File
# Begin Source File

SOURCE="..\..\..\Build\products\smil-10\splash8bit.bmp"
# End Source File
# Begin Source File

SOURCE="..\..\..\Build\products\smil-20\editor\splash8bit.bmp"
# End Source File
# Begin Source File

SOURCE="..\..\..\Build\products\smil-20\player\splash8bit.bmp"
# End Source File
# Begin Source File

SOURCE=..\..\..\Build\products\snap\splash8bit.bmp
# End Source File
# Begin Source File

SOURCE=..\..\..\Build\products\snap\win32\splash8bit.bmp
# End Source File
# Begin Source File

SOURCE=.\RES\splashimg.bmp
# End Source File
# Begin Source File

SOURCE="..\..\..\Build\products\g2-15\lite\splashpr.bmp"
# End Source File
# Begin Source File

SOURCE="..\..\..\Build\products\g2-15\pro\splashqt.bmp"
# End Source File
# Begin Source File

SOURCE="..\..\..\Build\products\g2-15\pro\splashsm.bmp"
# End Source File
# Begin Source File

SOURCE=..\..\..\Build\products\snap\splashsn.bmp
# End Source File
# Begin Source File

SOURCE=.\RES\Stop.cur
# End Source File
# Begin Source File

SOURCE=.\RES\stop.ico
# End Source File
# Begin Source File

SOURCE=.\RES\Switch_close.ico
# End Source File
# Begin Source File

SOURCE=.\RES\Switch_open.ico
# End Source File
# Begin Source File

SOURCE=.\RES\tb_alignment.bmp
# End Source File
# Begin Source File

SOURCE=.\RES\tb_player.bmp
# End Source File
# Begin Source File

SOURCE=.\Res\text.bmp
# End Source File
# Begin Source File

SOURCE=.\RES\toolbar1.bmp
# End Source File
# Begin Source File

SOURCE=.\Res\video.bmp
# End Source File
# Begin Source File

SOURCE=.\Res\viewport.bmp
# End Source File
# Begin Source File

SOURCE=.\RES\waitstop.ico
# End Source File
# Begin Source File

SOURCE=.\RES\wallcloc.ico
# End Source File
# Begin Source File

SOURCE=.\RES\zoomin.ico
# End Source File
# Begin Source File

SOURCE=.\RES\zoomout.ico
# End Source File
# End Group
# Begin Source File

SOURCE=.\RES\animate.ico
# End Source File
# Begin Source File

SOURCE=.\RES\Audio.ico
# End Source File
# Begin Source File

SOURCE=.\RES\Blank.ico
# End Source File
# Begin Source File

SOURCE=.\RES\brush.ico
# End Source File
# Begin Source File

SOURCE=.\RES\cdarrow.cur
# End Source File
# Begin Source File

SOURCE=.\RES\cdarrowh.cur
# End Source File
# Begin Source File

SOURCE=.\RES\closedeye.ico
# End Source File
# Begin Source File

SOURCE=.\RES\danglinganchor.ico
# End Source File
# Begin Source File

SOURCE=.\RES\danglingev.ico
# End Source File
# Begin Source File

SOURCE=.\RES\darrow.cur
# End Source File
# Begin Source File

SOURCE=.\RES\darrowhi.cur
# End Source File
# Begin Source File

SOURCE=.\RES\icon_bro.ico
# End Source File
# Begin Source File

SOURCE=.\RES\icon_con.ico
# End Source File
# Begin Source File

SOURCE=.\RES\icon_med.ico
# End Source File
# Begin Source File

SOURCE=.\RES\Image.ico
# End Source File
# Begin Source File

SOURCE=.\RES\linkin.ico
# End Source File
# Begin Source File

SOURCE=.\RES\linkout.ico
# End Source File
# Begin Source File

SOURCE=.\RES\Node.ico
# End Source File
# Begin Source File

SOURCE=.\RES\openedeye.ico
# End Source File
# Begin Source File

SOURCE=.\RES\openedeyekey.ico
# End Source File
# Begin Source File

SOURCE=.\RES\pausing.ico
# End Source File
# Begin Source File

SOURCE=.\RES\properties.ico
# End Source File
# Begin Source File

SOURCE=.\RES\region.ico
# End Source File
# Begin Source File

SOURCE=.\RES\region1.ico
# End Source File
# Begin Source File

SOURCE=.\RES\showed1.ico
# End Source File
# Begin Source File

SOURCE=..\..\..\Build\products\smil2real\splash8bit.bmp
# End Source File
# Begin Source File

SOURCE=.\RES\svg.bmp
# End Source File
# Begin Source File

SOURCE=.\RES\Text.ico
# End Source File
# Begin Source File

SOURCE=.\RES\unknown.ico
# End Source File
# Begin Source File

SOURCE=.\RES\Video.ico
# End Source File
# Begin Source File

SOURCE=.\RES\viewport.ico
# End Source File
# End Target
# End Project
