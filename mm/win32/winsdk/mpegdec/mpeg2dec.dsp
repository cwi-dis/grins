# Microsoft Developer Studio Project File - Name="mpeg2dec" - Package Owner=<4>
# Microsoft Developer Studio Generated Build File, Format Version 6.00
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Console Application" 0x0103

CFG=mpeg2dec - Win32 Debug
!MESSAGE This is not a valid makefile. To build this project using NMAKE,
!MESSAGE use the Export Makefile command and run
!MESSAGE 
!MESSAGE NMAKE /f "mpeg2dec.mak".
!MESSAGE 
!MESSAGE You can specify a configuration when running NMAKE
!MESSAGE by defining the macro CFG on the command line. For example:
!MESSAGE 
!MESSAGE NMAKE /f "mpeg2dec.mak" CFG="mpeg2dec - Win32 Debug"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "mpeg2dec - Win32 Release" (based on "Win32 (x86) Console Application")
!MESSAGE "mpeg2dec - Win32 Debug" (based on "Win32 (x86) Console Application")
!MESSAGE 

# Begin Project
# PROP AllowPerConfigDependencies 0
# PROP Scc_ProjName ""
# PROP Scc_LocalPath ""
CPP=cl.exe
RSC=rc.exe

!IF  "$(CFG)" == "mpeg2dec - Win32 Release"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir "Release"
# PROP BASE Intermediate_Dir "Release"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 0
# PROP Output_Dir "Release"
# PROP Intermediate_Dir "Release"
# PROP Target_Dir ""
# ADD BASE CPP /nologo /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_CONSOLE" /D "_MBCS" /YX /FD /c
# ADD CPP /nologo /W3 /GX /O2 /I "." /D "WIN32" /D "NDEBUG" /D "_CONSOLE" /D "_MBCS" /D "UNICODE" /D "_UNICODE" /FR /YX /FD /c
# ADD BASE RSC /l 0x409 /d "NDEBUG"
# ADD RSC /l 0x409 /d "NDEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:console /machine:I386
# ADD LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:console /machine:I386

!ELSEIF  "$(CFG)" == "mpeg2dec - Win32 Debug"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 1
# PROP BASE Output_Dir "Debug"
# PROP BASE Intermediate_Dir "Debug"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 1
# PROP Output_Dir "Debug"
# PROP Intermediate_Dir "Debug"
# PROP Target_Dir ""
# ADD BASE CPP /nologo /W3 /Gm /GX /ZI /Od /D "WIN32" /D "_DEBUG" /D "_CONSOLE" /D "_MBCS" /YX /FD /GZ /c
# ADD CPP /nologo /W3 /Gm /GX /ZI /Od /I "." /D "WIN32" /D "_DEBUG" /D "_CONSOLE" /D "_MBCS" /D "UNICODE" /D "_UNICODE" /FR /YX /FD /GZ /c
# ADD BASE RSC /l 0x409 /d "_DEBUG"
# ADD RSC /l 0x409 /d "_DEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:console /debug /machine:I386 /pdbtype:sept
# ADD LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:console /debug /machine:I386 /pdbtype:sept

!ENDIF 

# Begin Target

# Name "mpeg2dec - Win32 Release"
# Name "mpeg2dec - Win32 Debug"
# Begin Group "Source Files"

# PROP Default_Filter "cpp;c;cxx;rc;def;r;odl;idl;hpj;bat"
# Begin Source File

SOURCE=.\mpeg_container.cpp
# End Source File
# Begin Source File

SOURCE=.\mpeg_player.cpp
# End Source File
# Begin Source File

SOURCE=.\mpegdisplay.cpp
# End Source File
# Begin Source File

SOURCE=.\test_main.cpp
# End Source File
# End Group
# Begin Group "Header Files"

# PROP Default_Filter "h;hpp;hxx;hm;inl"
# Begin Source File

SOURCE=.\mpeg2con.h
# End Source File
# Begin Source File

SOURCE=.\mpeg2def.h
# End Source File
# Begin Source File

SOURCE=.\mpeg_container.h
# End Source File
# Begin Source File

SOURCE=.\mpeg_input_stream.h
# End Source File
# Begin Source File

SOURCE=.\mpeg_player.h
# End Source File
# Begin Source File

SOURCE=.\mpeg_video_display.h
# End Source File
# Begin Source File

SOURCE=.\mpegdisplay.h
# End Source File
# Begin Source File

SOURCE=.\stdio_mpeg_input_stream.h
# End Source File
# Begin Source File

SOURCE=.\wave_out_device.h
# End Source File
# Begin Source File

SOURCE=.\wnds_mpeg_input_stream.h
# End Source File
# End Group
# Begin Group "Resource Files"

# PROP Default_Filter "ico;cur;bmp;dlg;rc2;rct;bin;rgs;gif;jpg;jpeg;jpe"
# End Group
# Begin Group "Audio files"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\audio\ac3.cpp
# End Source File
# Begin Source File

SOURCE=.\audio\ac3.h
# End Source File
# Begin Source File

SOURCE=.\audio\bit_allocation.cpp
# End Source File
# Begin Source File

SOURCE=.\audio\dct.cpp
# End Source File
# Begin Source File

SOURCE=.\audio\dct.h
# End Source File
# Begin Source File

SOURCE=.\audio\exponents.cpp
# End Source File
# Begin Source File

SOURCE=.\audio\header.cpp
# End Source File
# Begin Source File

SOURCE=.\audio\header.h
# End Source File
# Begin Source File

SOURCE=.\audio\huffman.h
# End Source File
# Begin Source File

SOURCE=.\audio\layer.h
# End Source File
# Begin Source File

SOURCE=.\audio\layer1.cpp
# End Source File
# Begin Source File

SOURCE=.\audio\layer2.cpp
# End Source File
# Begin Source File

SOURCE=.\audio\layer3.cpp
# End Source File
# Begin Source File

SOURCE=.\audio\mantissa.cpp
# End Source File
# Begin Source File

SOURCE=.\audio\mpeg2audio.cpp
# End Source File
# Begin Source File

SOURCE=.\audio\mpeg2audio.h
# End Source File
# Begin Source File

SOURCE=.\audio\pcm.cpp
# End Source File
# Begin Source File

SOURCE=.\audio\pcm.h
# End Source File
# Begin Source File

SOURCE=.\audio\synthesizers.cpp
# End Source File
# Begin Source File

SOURCE=.\audio\synthesizers.h
# End Source File
# Begin Source File

SOURCE=.\audio\tables.cpp
# End Source File
# Begin Source File

SOURCE=.\audio\tables.h
# End Source File
# End Group
# Begin Group "Video Files"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\video\getpicture.cpp
# End Source File
# Begin Source File

SOURCE=.\video\getpicture.h
# End Source File
# Begin Source File

SOURCE=.\video\headers.cpp
# End Source File
# Begin Source File

SOURCE=.\video\headers.h
# End Source File
# Begin Source File

SOURCE=.\video\idct.cpp
# End Source File
# Begin Source File

SOURCE=.\video\idct.h
# End Source File
# Begin Source File

SOURCE=.\video\macroblocks.cpp
# End Source File
# Begin Source File

SOURCE=.\video\macroblocks.h
# End Source File
# Begin Source File

SOURCE=.\video\motion.cpp
# End Source File
# Begin Source File

SOURCE=.\video\motion.h
# End Source File
# Begin Source File

SOURCE=.\video\mpeg2video.cpp
# End Source File
# Begin Source File

SOURCE=.\video\mpeg2video.h
# End Source File
# Begin Source File

SOURCE=.\video\reconstruct.cpp
# End Source File
# Begin Source File

SOURCE=.\video\reconstruct.h
# End Source File
# Begin Source File

SOURCE=.\video\seek.cpp
# End Source File
# Begin Source File

SOURCE=.\video\seek.h
# End Source File
# Begin Source File

SOURCE=.\video\slice.cpp
# End Source File
# Begin Source File

SOURCE=.\video\slice.h
# End Source File
# Begin Source File

SOURCE=.\video\vlc.cpp
# End Source File
# Begin Source File

SOURCE=.\video\vlc.h
# End Source File
# End Group
# Begin Group "Streams"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\streams\bitstream.cpp
# End Source File
# Begin Source File

SOURCE=.\streams\bitstream.h
# End Source File
# Begin Source File

SOURCE=.\streams\mpeg2css.h
# End Source File
# Begin Source File

SOURCE=.\streams\mpeg2demux.cpp
# End Source File
# Begin Source File

SOURCE=.\streams\mpeg2demux.h
# End Source File
# Begin Source File

SOURCE=.\streams\mpeg2io.cpp
# End Source File
# Begin Source File

SOURCE=.\streams\mpeg2io.h
# End Source File
# Begin Source File

SOURCE=.\streams\mpeg2title.cpp
# End Source File
# Begin Source File

SOURCE=.\streams\mpeg2title.h
# End Source File
# End Group
# Begin Group "Mpglib files"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\mpglib\mpeg_video.cpp
# End Source File
# Begin Source File

SOURCE=.\mpglib\mpeg_video.h
# End Source File
# Begin Source File

SOURCE=.\mpglib\mpeg_video_bitstream.h
# End Source File
# Begin Source File

SOURCE=.\mpglib\mpeg_video_getblk.cpp
# End Source File
# Begin Source File

SOURCE=.\mpglib\mpeg_video_getpic.cpp
# End Source File
# Begin Source File

SOURCE=.\mpglib\mpeg_video_getvlc.cpp
# End Source File
# Begin Source File

SOURCE=.\mpglib\mpeg_video_getvlc.h
# End Source File
# Begin Source File

SOURCE=.\mpglib\mpeg_video_globals.h
# End Source File
# Begin Source File

SOURCE=.\mpglib\mpeg_video_headers.cpp
# End Source File
# Begin Source File

SOURCE=.\mpglib\mpeg_video_idct.cpp
# End Source File
# Begin Source File

SOURCE=.\mpglib\mpeg_video_motion.cpp
# End Source File
# Begin Source File

SOURCE=.\mpglib\mpeg_video_recon.cpp
# End Source File
# Begin Source File

SOURCE=.\mpglib\mpeg_video_spatscal.cpp
# End Source File
# Begin Source File

SOURCE=.\mpglib\stdio_mpeg_input_stream.h
# End Source File
# End Group
# Begin Group "common"

# PROP Default_Filter ""
# Begin Source File

SOURCE=..\common\charconv.h
# End Source File
# Begin Source File

SOURCE=..\common\memfile.h
# End Source File
# Begin Source File

SOURCE=..\common\memman.h
# End Source File
# Begin Source File

SOURCE=..\common\mtsync.h
# End Source File
# Begin Source File

SOURCE=..\common\platform.h
# End Source File
# Begin Source File

SOURCE=..\common\strutil.h
# End Source File
# Begin Source File

SOURCE=..\common\surface.h
# End Source File
# Begin Source File

SOURCE=..\common\thread.h
# End Source File
# Begin Source File

SOURCE=..\common\video.h
# End Source File
# Begin Source File

SOURCE=..\common\xg.h
# End Source File
# End Group
# End Target
# End Project
