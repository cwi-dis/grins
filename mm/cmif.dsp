# Microsoft Developer Studio Project File - Name="cmif" - Package Owner=<4>
# Microsoft Developer Studio Generated Build File, Format Version 6.00
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Generic Project" 0x010a

CFG=cmif - Win32 Debug
!MESSAGE This is not a valid makefile. To build this project using NMAKE,
!MESSAGE use the Export Makefile command and run
!MESSAGE 
!MESSAGE NMAKE /f "cmif.mak".
!MESSAGE 
!MESSAGE You can specify a configuration when running NMAKE
!MESSAGE by defining the macro CFG on the command line. For example:
!MESSAGE 
!MESSAGE NMAKE /f "cmif.mak" CFG="cmif - Win32 Debug"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "cmif - Win32 Release" (based on "Win32 (x86) Generic Project")
!MESSAGE "cmif - Win32 Debug" (based on "Win32 (x86) Generic Project")
!MESSAGE 

# Begin Project
# PROP AllowPerConfigDependencies 0
# PROP Scc_ProjName ""
# PROP Scc_LocalPath ""
MTL=midl.exe

!IF  "$(CFG)" == "cmif - Win32 Release"

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

!ELSEIF  "$(CFG)" == "cmif - Win32 Debug"

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

!ENDIF 

# Begin Target

# Name "cmif - Win32 Release"
# Name "cmif - Win32 Debug"
# Begin Group "common"

# PROP Default_Filter ""
# Begin Group "common/win32"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\common\win32\ChannelMime.py
# End Source File
# Begin Source File

SOURCE=.\common\win32\HtmlChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\win32\LicenseDialog.py
# End Source File
# Begin Source File

SOURCE=.\common\win32\MediaChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\win32\MidiChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\win32\NTVideoChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\win32\PreferencesDialog.py
# End Source File
# Begin Source File

SOURCE=.\common\win32\SoundChannel.py
# End Source File
# End Group
# Begin Group "common/mac"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\common\mac\HtmlChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\mac\LicenseDialog.py
# End Source File
# Begin Source File

SOURCE=.\common\mac\PreferencesDialog.py
# End Source File
# Begin Source File

SOURCE=.\common\mac\SocketChannel.py
# End Source File
# End Group
# Begin Group "common/motif"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\common\motif\HtmlChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\motif\LicenseDialog.py
# End Source File
# Begin Source File

SOURCE=.\common\motif\pausebutton.py
# End Source File
# Begin Source File

SOURCE=.\common\motif\pausebuttonunselect.py
# End Source File
# Begin Source File

SOURCE=.\common\motif\playbutton.py
# End Source File
# Begin Source File

SOURCE=.\common\motif\playbuttonunselect.py
# End Source File
# Begin Source File

SOURCE=.\common\motif\PlayerDialogBase.py
# End Source File
# Begin Source File

SOURCE=.\common\motif\PreferencesDialog.py
# End Source File
# Begin Source File

SOURCE=.\common\motif\stopbutton.py
# End Source File
# Begin Source File

SOURCE=.\common\motif\stopbuttonunselect.py
# End Source File
# End Group
# Begin Source File

SOURCE=.\common\AnchorDefs.py
# End Source File
# Begin Source File

SOURCE=.\common\AnimateChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\ArmStates.py
# End Source File
# Begin Source File

SOURCE=.\common\bitrates.py
# End Source File
# Begin Source File

SOURCE=.\common\Channel.py
# End Source File
# Begin Source File

SOURCE=.\common\ChannelMap.py
# End Source File
# Begin Source File

SOURCE=.\common\ChannelMime.py
# End Source File
# Begin Source File

SOURCE=.\common\ChannelThread.py
# End Source File
# Begin Source File

SOURCE=.\common\CmifChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\ExternalChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\flags.py
# End Source File
# Begin Source File

SOURCE=.\common\GLLock.py
# End Source File
# Begin Source File

SOURCE=.\common\GraphChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\HDTL.py
# End Source File
# Begin Source File

SOURCE=.\common\Help.py
# End Source File
# Begin Source File

SOURCE=.\common\ImageChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\LabelChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\languages.py
# End Source File
# Begin Source File

SOURCE=.\common\LayoutChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\MACVideoChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\MidiChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\MovieChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\MPEGVideoChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\NullChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\PrefetchChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\PseudoHtmlChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\PythonChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\RealAudioChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\RealChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\RealPixChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\RealTextChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\RealVideoChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\RealWindowChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\rtpool.py
# End Source File
# Begin Source File

SOURCE=.\common\Scheduler.py
# End Source File
# Begin Source File

SOURCE=.\common\Selecter.py
# End Source File
# Begin Source File

SOURCE=.\common\SGIVideoChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\ShellChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\SocketChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\SoundChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\systemtestnames.py
# End Source File
# Begin Source File

SOURCE=.\common\TextChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\Timing.py
# End Source File
# Begin Source File

SOURCE=.\common\VcrChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\VideoChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\WordChannel.py
# End Source File
# End Group
# Begin Group "editor"

# PROP Default_Filter ""
# Begin Group "editor/win32"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\editor\win32\_AssetsView.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\_ErrorsView.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\_LayoutView.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\_LayoutView2.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\_LinkView.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\_PreferencesDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\_StructView.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\_TransitionView.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\_UsergroupView.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\AssetsViewDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\AttrEditDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\AttrEditForm.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\ErrorsViewDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\HierarchyViewDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\LayoutViewDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\LayoutViewDialog2.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\LinkEditDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\MainDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\MainFrameSpecific.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\MenuTemplate.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\NodeEdit.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\patchlevel.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\PlayerDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\SourceViewDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\TemporalViewDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\ToolbarState.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\ToolbarTemplate.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\TopLevelDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\TransitionViewDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\usercmdui.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\UsergroupViewDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\win32\wndusercmd.py
# End Source File
# End Group
# Begin Group "editor/mac"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\editor\mac\AnchorEditDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\mac\ArcInfoDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\mac\AttrEditDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\mac\HierarchyViewDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\mac\LayoutViewDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\mac\LinkEditDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\mac\MainDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\mac\MenuTemplate.py
# End Source File
# Begin Source File

SOURCE=.\editor\mac\NodeEdit.py
# End Source File
# Begin Source File

SOURCE=.\editor\mac\NodeInfoDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\mac\patchlevel.py
# End Source File
# Begin Source File

SOURCE=.\editor\mac\PlayerDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\mac\TopLevel.py
# End Source File
# Begin Source File

SOURCE=.\editor\mac\TopLevelDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\mac\UsergroupViewDialog.py
# End Source File
# End Group
# Begin Group "editor/motif"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\editor\motif\AnchorEditDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\ArcInfoDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\AttrEditDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\bandwidthbad.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\bandwidthgood.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\emptyicon.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\folderclosed.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\folderopen.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\HierarchyViewDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\LayoutViewDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\LinkEditDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\MainDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\NodeInfoDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\patchlevel.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\PlayerDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\stopicon.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\TopLevelDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\UsergroupViewDialog.py
# End Source File
# End Group
# Begin Group "editor/g2pro"

# PROP Default_Filter "*.py"
# Begin Source File

SOURCE=.\editor\g2pro\features.py
# End Source File
# End Group
# Begin Group "editor/g2lite"

# PROP Default_Filter "*.py"
# Begin Source File

SOURCE=.\editor\g2lite\features.py
# End Source File
# End Group
# Begin Group "editor/qtlite"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\editor\qtlite\features.py
# End Source File
# End Group
# Begin Group "editor/qtpro"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\editor\qtpro\features.py
# End Source File
# End Group
# Begin Group "editor/smil10"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\editor\smil10\features.py
# End Source File
# End Group
# Begin Group "editor/snap"

# PROP Default_Filter ""
# Begin Group "editor/snap/win32"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\editor\snap\win32\splashbmp.py
# End Source File
# End Group
# Begin Group "editor/snap/mac"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\editor\snap\mac\MenuTemplate.py
# End Source File
# End Group
# Begin Source File

SOURCE=.\editor\snap\AppDefaults.py
# End Source File
# Begin Source File

SOURCE=.\editor\snap\features.py
# End Source File
# End Group
# Begin Group "editor/smilboston"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\editor\smilboston\features.py
# End Source File
# End Group
# Begin Group "smil2real"

# PROP Default_Filter ""
# Begin Group "smil2real-win32"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\editor\smil2real\win32\splashbmp.py
# End Source File
# End Group
# Begin Source File

SOURCE=.\editor\smil2real\features.py
# End Source File
# Begin Source File

SOURCE=.\editor\smil2real\version.py
# End Source File
# End Group
# Begin Source File

SOURCE=.\editor\AnchorEdit.py
# End Source File
# Begin Source File

SOURCE=.\editor\AnchorList.py
# End Source File
# Begin Source File

SOURCE=.\editor\AppDefaults.py
# End Source File
# Begin Source File

SOURCE=.\editor\ArcInfo.py
# End Source File
# Begin Source File

SOURCE=.\editor\AssetsView.py
# End Source File
# Begin Source File

SOURCE=.\editor\AttrEdit.py
# End Source File
# Begin Source File

SOURCE=.\editor\BandwidthCompute.py
# End Source File
# Begin Source File

SOURCE=.\editor\cmifed.py
# End Source File
# Begin Source File

SOURCE=.\editor\compatibility.py
# End Source File
# Begin Source File

SOURCE=.\editor\EditableObjects.py
# End Source File
# Begin Source File

SOURCE=.\editor\ErrorsView.py
# End Source File
# Begin Source File

SOURCE=.\editor\EventEditor.py
# End Source File
# Begin Source File

SOURCE=.\editor\FeatureSet.py
# End Source File
# Begin Source File

SOURCE=.\editor\HierarchyView.py
# End Source File
# Begin Source File

SOURCE=.\editor\LayoutView.py
# End Source File
# Begin Source File

SOURCE=.\editor\LayoutView2.py
# End Source File
# Begin Source File

SOURCE=.\editor\LinkEdit.py
# End Source File
# Begin Source File

SOURCE=.\editor\LinkEditLight.py
# End Source File
# Begin Source File

SOURCE=.\editor\NodeEdit.py
# End Source File
# Begin Source File

SOURCE=.\editor\NodeInfo.py
# End Source File
# Begin Source File

SOURCE=.\editor\patchlevel.py
# End Source File
# Begin Source File

SOURCE=.\editor\Player.py
# End Source File
# Begin Source File

SOURCE=.\editor\PlayerCore.py
# End Source File
# Begin Source File

SOURCE=.\editor\SourceView.py
# End Source File
# Begin Source File

SOURCE=.\editor\splashimg.py
# End Source File
# Begin Source File

SOURCE=.\editor\StructureWidgets.py
# End Source File
# Begin Source File

SOURCE=.\editor\TemporalView.py
# End Source File
# Begin Source File

SOURCE=.\editor\TemporalWidgets.py
# End Source File
# Begin Source File

SOURCE=.\editor\TimeMapper.py
# End Source File
# Begin Source File

SOURCE=.\editor\TopLevel.py
# End Source File
# Begin Source File

SOURCE=.\editor\TransitionView.py
# End Source File
# Begin Source File

SOURCE=.\editor\usercmd.py
# End Source File
# Begin Source File

SOURCE=.\editor\UsergroupView.py
# End Source File
# Begin Source File

SOURCE=.\editor\version.py
# End Source File
# Begin Source File

SOURCE=.\editor\ViewDialog.py
# End Source File
# End Group
# Begin Group "lib"

# PROP Default_Filter ""
# Begin Group "lib/win32"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\lib\win32\_FSPlayerView.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\_PlayerView.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\_SourceView.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\appcon.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\AppToplevel.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\AutoLicense.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\components.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\DrawTk.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\DropTarget.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\Font.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\GenFormView.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\GenView.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\GenWnd.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\IconMixin.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\ListCtrl.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\MainFrame.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\NodeInfoForm.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\NTVideoDuration.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\SoundDuration.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\splash.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\sysmetrics.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\ToolbarIcons.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\Toolbars.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\TransitionBitBlit.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\TreeCtrl.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\win32dialog.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\win32displaylist.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\win32dlview.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\win32dxm.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\win32ig.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\win32menu.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\win32mu.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\win32transitions.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\win32window.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\windowinterface.py
# End Source File
# Begin Source File

SOURCE=.\lib\win32\winplayerdlg.py
# End Source File
# End Group
# Begin Group "lib/motif"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\lib\motif\splash.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\windowinterface.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\XAdornment.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\XButton.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\XButtonSupport.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\XCommand.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\XConstants.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\XDialog.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\XDisplist.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\XFont.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\XFormWindow.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\XHelpers.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\XHtml.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\XRubber.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\XTemplate.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\XTopLevel.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\XWindow.py
# End Source File
# End Group
# Begin Group "lib/mac"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\lib\mac\greekconv.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac\htmlwidget.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac\mac_image.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac\machtmlentitydefs.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac\mw_dialogs.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac\mw_displaylist.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac\mw_fonts.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac\mw_globals.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac\mw_menucmd.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac\mw_resources.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac\mw_textwindow.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac\mw_toplevel.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac\mw_widgets.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac\mw_windows.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac\quietconsole.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac\splash.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac\videoreader.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac\windowinterface.py
# End Source File
# End Group
# Begin Source File

SOURCE=.\lib\Animators.py
# End Source File
# Begin Source File

SOURCE=.\lib\ASXParser.py
# End Source File
# Begin Source File

SOURCE=.\lib\Attrdefs
# End Source File
# Begin Source File

SOURCE=.\lib\Attrdefs.py
# End Source File
# Begin Source File

SOURCE=.\lib\Attrgrs.py
# End Source File
# Begin Source File

SOURCE=.\lib\Bandwidth.py
# End Source File
# Begin Source File

SOURCE=.\lib\calcwmcorr.py
# End Source File
# Begin Source File

SOURCE=.\lib\chkcmif.py
# End Source File
# Begin Source File

SOURCE=.\lib\Clipboard.py
# End Source File
# Begin Source File

SOURCE=.\lib\cmif.py
# End Source File
# Begin Source File

SOURCE=.\lib\colors.py
# End Source File
# Begin Source File

SOURCE=.\lib\dialogs.doc
# End Source File
# Begin Source File

SOURCE=.\lib\dummy_windowbase.py
# End Source File
# Begin Source File

SOURCE=.\lib\Duration.py
# End Source File
# Begin Source File

SOURCE=.\lib\EditMgr.py
# End Source File
# Begin Source File

SOURCE=.\lib\events.doc
# End Source File
# Begin Source File

SOURCE=.\lib\fastimp.py
# End Source File
# Begin Source File

SOURCE=.\lib\FileCache.py
# End Source File
# Begin Source File

SOURCE=.\lib\FtpWriter.py
# End Source File
# Begin Source File

SOURCE=.\lib\GeometricPrimitives.py
# End Source File
# Begin Source File

SOURCE=.\lib\GL_window.py
# End Source File
# Begin Source File

SOURCE=.\lib\GL_windowbase.py
# End Source File
# Begin Source File

SOURCE=.\lib\glwindow.py
# End Source File
# Begin Source File

SOURCE=.\lib\grins_mimetypes.py
# End Source File
# Begin Source File

SOURCE=.\lib\Hlinks.py
# End Source File
# Begin Source File

SOURCE=.\lib\HTMLWrite.py
# End Source File
# Begin Source File

SOURCE=.\lib\imgimagesize.py
# End Source File
# Begin Source File

SOURCE=.\lib\license.py
# End Source File
# Begin Source File

SOURCE=.\lib\licparser.py
# End Source File
# Begin Source File

SOURCE=.\lib\links.doc
# End Source File
# Begin Source File

SOURCE=.\lib\MACVideoDuration.py
# End Source File
# Begin Source File

SOURCE=.\lib\MenuMaker.py
# End Source File
# Begin Source File

SOURCE=.\lib\mkimg.py
# End Source File
# Begin Source File

SOURCE=.\lib\mklicense.py
# End Source File
# Begin Source File

SOURCE=.\lib\mksplash.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMAttrdefs.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMCache.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMExc.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMNode.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMParser.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMRead.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMStat.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMTree.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMTypes.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMurl.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMWrite.py
# End Source File
# Begin Source File

SOURCE=.\lib\MovieDuration.py
# End Source File
# Begin Source File

SOURCE=.\lib\MPEGVideoDuration.py
# End Source File
# Begin Source File

SOURCE=.\lib\README
# End Source File
# Begin Source File

SOURCE=.\lib\realconvert.py
# End Source File
# Begin Source File

SOURCE=.\lib\realnode.py
# End Source File
# Begin Source File

SOURCE=.\lib\realsupport.py
# End Source File
# Begin Source File

SOURCE=.\lib\rpconvert.py
# End Source File
# Begin Source File

SOURCE=.\lib\settings.py
# End Source File
# Begin Source File

SOURCE=.\lib\SGIVideoDuration.py
# End Source File
# Begin Source File

SOURCE=.\lib\Sizes.py
# End Source File
# Begin Source File

SOURCE=.\lib\SMIL.py
# End Source File
# Begin Source File

SOURCE=.\lib\SMILCssResolver.py
# End Source File
# Begin Source File

SOURCE=.\lib\SMILTreeRead.py
# End Source File
# Begin Source File

SOURCE=.\lib\SMILTreeWrite.py
# End Source File
# Begin Source File

SOURCE=.\lib\SMILTreeWriteHtmlTime.py
# End Source File
# Begin Source File

SOURCE=.\lib\smpte.py
# End Source File
# Begin Source File

SOURCE=.\lib\SoundDuration.py
# End Source File
# Begin Source File

SOURCE=.\lib\SR.py
# End Source File
# Begin Source File

SOURCE=.\lib\staticlicense.py
# End Source File
# Begin Source File

SOURCE=.\lib\StringStuff.py
# End Source File
# Begin Source File

SOURCE=.\lib\svgpath.py
# End Source File
# Begin Source File

SOURCE=.\lib\trace.py
# End Source File
# Begin Source File

SOURCE=.\lib\Transitions.py
# End Source File
# Begin Source File

SOURCE=.\lib\urlcache.py
# End Source File
# Begin Source File

SOURCE=.\lib\VideoDuration.py
# End Source File
# Begin Source File

SOURCE=.\lib\watchcursor.py
# End Source File
# Begin Source File

SOURCE=.\lib\Widgets.py
# End Source File
# Begin Source File

SOURCE=.\lib\windowinterface.doc
# End Source File
# Begin Source File

SOURCE=.\lib\WMEVENTS.py
# End Source File
# Begin Source File

SOURCE=.\lib\wmpsupport.py
# End Source File
# End Group
# Begin Group "grins"

# PROP Default_Filter ""
# Begin Group "grins/win32"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\grins\win32\MainDialog.py
# End Source File
# Begin Source File

SOURCE=.\grins\win32\MenuTemplate.py
# End Source File
# Begin Source File

SOURCE=.\grins\win32\patchlevel.py
# End Source File
# Begin Source File

SOURCE=.\grins\win32\PlayerDialog.py
# End Source File
# Begin Source File

SOURCE=.\grins\win32\PreferencesDialog.py
# End Source File
# Begin Source File

SOURCE=.\grins\win32\ToolbarTemplate.py
# End Source File
# Begin Source File

SOURCE=.\grins\win32\TopLevelDialog.py
# End Source File
# Begin Source File

SOURCE=.\grins\win32\usercmdui.py
# End Source File
# Begin Source File

SOURCE=.\grins\win32\wndusercmd.py
# End Source File
# End Group
# Begin Group "grins/mac"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\grins\mac\MainDialog.py
# End Source File
# Begin Source File

SOURCE=.\grins\mac\MenuTemplate.py
# End Source File
# Begin Source File

SOURCE=.\grins\mac\patchlevel.py
# End Source File
# Begin Source File

SOURCE=.\grins\mac\PlayerDialog.py
# End Source File
# Begin Source File

SOURCE=.\grins\mac\PreferencesDialog.py
# End Source File
# Begin Source File

SOURCE=.\grins\mac\TopLevelDialog.py
# End Source File
# End Group
# Begin Group "grins/motif"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\grins\motif\MainDialog.py
# End Source File
# Begin Source File

SOURCE=.\grins\motif\patchlevel.py
# End Source File
# Begin Source File

SOURCE=.\grins\motif\PlayerDialog.py
# End Source File
# Begin Source File

SOURCE=.\grins\motif\PreferencesDialog.py
# End Source File
# Begin Source File

SOURCE=.\grins\motif\TopLevelDialog.py
# End Source File
# End Group
# Begin Source File

SOURCE=.\grins\features.py
# End Source File
# Begin Source File

SOURCE=.\grins\grins.py
# End Source File
# Begin Source File

SOURCE=.\grins\mac_window.py
# End Source File
# Begin Source File

SOURCE=.\grins\patchlevel.py
# End Source File
# Begin Source File

SOURCE=.\grins\Player.py
# End Source File
# Begin Source File

SOURCE=.\grins\PlayerCore.py
# End Source File
# Begin Source File

SOURCE=.\grins\Preferences.py
# End Source File
# Begin Source File

SOURCE=.\grins\splashimg.py
# End Source File
# Begin Source File

SOURCE=.\grins\TopLevel.py
# End Source File
# Begin Source File

SOURCE=.\grins\usercmd.py
# End Source File
# Begin Source File

SOURCE=.\grins\version.py
# End Source File
# End Group
# Begin Group "pylib"

# PROP Default_Filter ""
# Begin Group "audio"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\pylib\audio\__init__.py
# End Source File
# Begin Source File

SOURCE=.\pylib\audio\aifc.py
# End Source File
# Begin Source File

SOURCE=.\pylib\audio\au.py
# End Source File
# Begin Source File

SOURCE=.\pylib\audio\convert.py
# End Source File
# Begin Source File

SOURCE=.\pylib\audio\dev.py
# End Source File
# Begin Source File

SOURCE=.\pylib\audio\devmac.py
# End Source File
# Begin Source File

SOURCE=.\pylib\audio\devsgi.py
# End Source File
# Begin Source File

SOURCE=.\pylib\audio\devsun.py
# End Source File
# Begin Source File

SOURCE=.\pylib\audio\devwin.py
# End Source File
# Begin Source File

SOURCE=.\pylib\audio\file.py
# End Source File
# Begin Source File

SOURCE=.\pylib\audio\format.py
# End Source File
# Begin Source File

SOURCE=.\pylib\audio\merge.py
# End Source File
# Begin Source File

SOURCE=.\pylib\audio\README
# End Source File
# Begin Source File

SOURCE=.\pylib\audio\select.py
# End Source File
# Begin Source File

SOURCE=.\pylib\audio\wav.py
# End Source File
# Begin Source File

SOURCE=.\pylib\audio\what.py
# End Source File
# End Group
# Begin Group "pywinlib"

# PROP Default_Filter ""
# Begin Group "mfc"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\pylib\pywinlib\mfc\afxres.py
# End Source File
# Begin Source File

SOURCE=.\pylib\pywinlib\mfc\dialog.py
# End Source File
# Begin Source File

SOURCE=.\pylib\pywinlib\mfc\docview.py
# End Source File
# Begin Source File

SOURCE=.\pylib\pywinlib\mfc\object.py
# End Source File
# Begin Source File

SOURCE=.\pylib\pywinlib\mfc\thread.py
# End Source File
# Begin Source File

SOURCE=.\pylib\pywinlib\mfc\window.py
# End Source File
# End Group
# Begin Group "framework"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\pylib\pywinlib\framework\app.py
# End Source File
# Begin Source File

SOURCE=.\pylib\pywinlib\framework\cmdline.py
# End Source File
# Begin Source File

SOURCE=.\pylib\pywinlib\framework\interact.py
# End Source File
# Begin Source File

SOURCE=.\pylib\pywinlib\framework\scriptutils.py
# End Source File
# Begin Source File

SOURCE=.\pylib\pywinlib\framework\winout.py
# End Source File
# End Group
# End Group
# Begin Source File

SOURCE=.\pylib\longpath.py
# End Source File
# Begin Source File

SOURCE=.\pylib\mimetypes.py
# End Source File
# Begin Source File

SOURCE=.\pylib\xmllib.py
# End Source File
# End Group
# Begin Group "bin"

# PROP Default_Filter ""
# Begin Group "win32"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\bin\win32\iGRiNS.py
# End Source File
# Begin Source File

SOURCE=.\bin\win32\iGRiNS_Boston.py
# End Source File
# Begin Source File

SOURCE=.\bin\win32\iGRiNS_Snap.py
# End Source File
# Begin Source File

SOURCE=.\bin\win32\iGRiNSlight.py
# End Source File
# Begin Source File

SOURCE=.\bin\win32\iGRiNSplayer.py
# End Source File
# Begin Source File

SOURCE=.\bin\win32\iGRiNSPlayer_SMIL2.py
# End Source File
# End Group
# End Group
# End Target
# End Project
