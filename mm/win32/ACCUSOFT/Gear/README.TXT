======================================================
                  ImageGear DLL README.TXT File
======================================================

Welcome to ImageGear DLL 6.0's Readme.txt file!

This file is intended to provide you with important information
that becomes available after the manual had already gone to
print.  The manual is now available in printed form, and also
on-line.  The on-line help will be updated in-between printings
of the manual, so you should check it when something in the
manual sounds incorrect.  If it was an error, or a change has
been made, it may have been corrected in the on-line help
already.   See also the file called RelNotes.txt, which is
installed to your product directory.  This file includes a log
of build numbers, and the changes made to each new build,
including changes to functions and functions that are new.

======================================================
Upgrading to ImageGear
======================================================
If you are upgrading to ImageGear from the IFL 5.0 or earlier,
you will want to use the ImageGear 6.0 Transition Guide.  This
document, which is separate from your User Manual, is an
essential guide for replacing your old function calls with
ImageGear function calls.


======================================================
CHANGES to the Manual: Release Version 6.0-00l
======================================================
Note:  The changes logged below refer to changes made after the
manual (rv# 6.0-001) went to print.  This section is divided
into three categories: "Global Changes", "API Changes or
Corrections", and "New Functions or Features".  Versions of the
manual later than 6.0-001 will already include these updates.
All of the changes logged below will also be made to the help
file, which is updated more often than the manual.  You should
download new help files whenever they are available.


===================
GLOBAL CHANGES
===================
To help customers that were having problems with the names of
some of the ImageGear type definitions, the following types have
undergone name changes:

Old Name		New Name
--------		--------
PIXEL			AT_PIXEL
DIMENSION		AT_DIMENSION
PIXPOS			AT_PIXPOS

LPPIXEL			LPAT_PIXEL
LPDIMENSION		LPAT_DIMENSION
LPPIXPOS		LPAT_PIXPOS

*As elsewhere, the prefix "AT" stands for AccuSoft type.


==============================================
Specific Changes:
==============================================

Consult the help file for the details concerning any of the
changes listed below:

IG_device_rect_set(), p. 138: the type of the second parameter,
lprcDevRect, should be: const LPAT_RECT.  "const" was
erroneously omitted.

IG_DIB_area_get/set(): pp. 140-141: the AT_MODE nPixelFormat now
has an additional setting: IG_DIB_AREA_RAW.  This will store the
pixels in the same order in which they are found:
packed or unpacked.

IG_DIB_raster_get()/set(), pp. 150-151: each have a new
parameter, AT_MODE nFormat, added to the end of their argument
lists.  This determines whether the data will be packed,
unpacked, or RLE_compressed. This allows you to read in data
that is either packed, unpacked, or RLE-compressed, and to set
its saving format to either packed, unpacked, or RLE-compressed.
Set this parameter to IG_PIXEL_PACKED, IG_PIXEL_UNPACKED, or
IG_PIXEL_RLE. 

IG_DIB_row_get()/set(), pp. 151-153: same note as for
		IG_DIB_raster_get()/set().

IG_display_angle_get/set(): pp. 158-159.  The type of the Angle
parameter has been changed from an AT_MODE to an integer.  You
may set the value of this variable to 0, 90, 180, or 270.  Also,
for the time being, this function can only be used for 1-bit
images.

IG_display_centered_get(): pp. 164.  A new "hwnd" parameter has
been inserted into the argument list.  New prototype:
IG_display_centered_get(HIGEAR hIGear, HWND hwnd, BOOL                                 bCenter);

IG_display_desktop_pattern_get/set(): pp.  167-169  these
functions now have a new parameter at the end of their argument
lists.  "Enabled", which is Boolean, will enable desktop
painting when set to TRUE and disable desktop painting when set
to FALSE. 

IG_ext_info_get(): pg. 204.  Two new parameters have been added:
a pointer to the compile date, and the size of the buffer to
hold the compile date.  New argument list:

(const LPSTR lpszExtension, LPSTR lpszCompanyName, UINT
nCompanyNameLen, LPSTR lpszCompileDate, UINT         nCompileDateLen,LPINT lpVersionMajor, LPINT 
lpVersionMinor, LPINT lpVersionUpdate);

IG_FX_motion(): pg. 211.  The last parameter dblDirection, has
been changed to type AT_MODE and will now take a value such as
IG_COMPASS_SE or IG_COMPASS_N.

IG_FX_stitch(): pg. 218.  The parameters list contains a
duplication error.  Two parameters are both declared: AT_MODE
nCompassDir.  The second of these should be DOUBLE dblStrength.

IG_GUI_thumbnail_file_append(): pg. 235. This function will now
put all pages from the specified file into the GUI thumbnail,
rather than just the first page.

IG_image_control_get(): pg. 243. The first argument is
erroneously shown as a far pointer.  It should just say: 
AT_MODE nOption 

IG_image_import_DIB(): pg. 259. A note to DLL 16 Pro Gold users
has been added:

A copy of the DIB is imported into the library.  The copied
DIB is put into 32-bit flat memory.  The original DIB 		                memory must be freed by the programmer.  We suggest 				                allocating the original	DIB memory, if possible, with 
the function IG_image_create_DIB().  Otherwise, you will 			                have two DIBs in memory at one time.

IG_IP_chromakey(): pg. 271.  Has been renamed to
IG_FX_chroma_key().  A new AT_RECT parameter has also been
inserted as the second argument.  This allows you to specify a
rectangular area of the image to apply blending to.

IG_load_size_get and IG_load_size_set(): pp. 332-333  TIP: To
reset ImageGear to load the whole image, set both parameters of
IG_load_size_set() (width and the height) to 0.

IG_load_tag_CB_register(): p. 334.  Error in example code: first
line should say LPFNIG_TAG_SET.

IG_IP_blend_percent(): p. 269.  A new AT_RECT parameter has be
inserted to let you select a rectangular portion of the image to
be blended.

IG_IP_blend_with_LUT(): p. 270.  The type of the last argument,
lpLUT, which is a pointer to the lookup table, is now of type
LPAT_LUT. (was LPPIXEL).

IG_IP_color_reduce_median_cut()
IG_IP_color_reduce_octree() : pp. 277-278.  These functions do not
support 4-bit images as stated.  They support 8i, 8g, and 24-bit.

LPFNIG_GUITHUMBSELECT(): p. 381.  New parameter added to end of
argument list: UINT nPageNumber.  This indicates the page number
that was selected.

==============================
NEW FUNCTIONS AND FEATURES
==============================
NOTE: See the Help file for complete descriptions of these new
functions. 

IG_convert_PPM_to_DPI() IG_convert_DPI_to_PPM():
Use these to convert from pel-per-meter to dots-per-inch or vice
versa.  Use these in conjunction with
IG_image_pels_per_meter_get() and IG_image_pels_per_meter_set(),
which are listed below.

IG_DIB_area_get_info():
Returns a single pixel value from the given rectangle.  The
"info" and "channel" parameters decide which pixel value is
returned.

IG_DIB_area_size_get():
Calculates and returns the numberof bytes required to hold a
specified rectangular region of an image.


IG_DIB_raster_size_get():
Returns the size in bytes of the raster of the image.

IG_display_PPM_correct_get()
IG_display_PPM_correct_set():
Let you correct the device rectangle of an image according to
the values of biXPelsPerMeter and biYPelsPerMeter.

IG_GUI_window_attribute_get()
IG_GUI_window_attribute_set():
These allow you to get/set the attributes of the current GUI window.

IG_IP_draw_frame():
Use this function to draw a frame around your image.

IG_image_resolution_get()
IG_image_resolution_set():
These functions allow you to set both the values and the units of resolution of the HIGEAR image.  In addition, the values will be converted to pels per meter and stored directly to the DIB.  The units of resolution argument allows 4 different AT_MODE settings.

IG_print_document():
Use this function to print more than one image at a time.

IG_print_page():
Use this function to specify how much of the printed page to
fill with the image, and how to align the image on the page.

LPFNIG_IMAGESPOOLED:
Called by IG_print_document(). Useful for keeping track of which
image from the array of images used by _print_document() have
already been spooled to the printer.

========================================================
If you are using an EVALUATION VERSION of ImageGear:
========================================================
As with all evaluation copies, it is scheduled to "time out" 60
days from the build date.  You can check the build date by
looking at the Help About box.  The Help About box will also
identify the product as an Evaluation version, if it is.  The
time-out feature will help you to remember to use the most
up-to-date version and to delete older ones.  When the DLL times
out you will be given a Time Out Message and the DLL will no
longer work.  All functions will return a Time Out Error on the
error stack.



=================================
ON-LINE HELP
=================================
The manual, which has now been printed, is also represented by
an on-line Help file called IGDLL16.HLP or IGDLL32.HLP
(depending on your version), and is located in the
ACCUSOFT\GEAR\DLL16ST or DLL32ST subdirectory.  Simply
double-click this file from File Manager or Windows 95 Explorer.
The on-line help will actually be updated more often than the
printed manual, so it is a good place to look if something in
the manual seems incorrect.
  

=================================
On-line Function Reference
=================================
To access the function descriptions in the function reference
when using the 16-bit version of ImageGear 6.0:  Either press
the Search button, and enter the name of the function you would
like to see, or Click over the area on the Main Window that
takes you to the Table of Contents; Click over "The Complete
ImageGear Function Reference", and use the page down (>>) and
page up (<<) buttons to move through the function descriptions.

The 32-bit version ImageGear Help File is set up as a Windows
95-style Help File.  It therefore has a "Contents tab" with
"books" and "topics".  If you are not familiar yet with Windows
95 Help, yet, it does not take long to learn how it works.  A
Window with three tabs appears, with the "Contents tab" first
appearing on the top.  On it are several book icons that
represent the different chapters of the manual.  Double-click on
a book to see the main topics included in each chapter.
Double-click on a topic to go to it.  The Index tab will list
all topics in the Help in alphabetical order.  The Find tab lets
you type in a key word to search for.  This Help file will be
usually be updated for each new release that we ship.


=====================================
ImageGear Sample Application Programs
=====================================
ImageGear is equipped with 35+ sample application programs.
Nearly every ImageGear function is demonstrated by one or more
of these sample programs.  The samples are installed with your
copy as long as you do not deselect the samples option from the
Install screen.  Each sample is placed in its own aptly-named
subdirectory under a AccuSoft\GEAR\DLL... directory, where the
"..." will vary according to the ImageGear version that you are
using.  For example, IMGDISP.C is stored in the
AccuSoft\GEAR\DLL...\SAMPLES\IMGDISP subdirectory.  An icon for
each appears in the ImageGear program group.  In addition to
demonstrating ImageGear's features, these are useful for cutting
and pasting code into your own applications, or even for using
as a template on which to build your application.


=================================
GIF and LZW Extension
=================================

The GIF format and any use of the LZW compression scheme (e.g.
TIFF LZW) require a license from Unisys.  This LZW compression
extension is included with each copy of ImageGear, where it can
be used for evaluation purposes, or as a release version if
given a valid password.  This setup means that you will not have
to download any additional files to use LZW.  And, of course,
this extension is free of charge.

To use the LZW DLL as an evaluation, simply give it an
"evaluation password" of "EVAL" and a code of "".  Please see
the LOADEXT sample application program for a demonstration of
this procedure.   If used as an evaluation, this will
automatically time out 90 (or more) days after the build date.

To make the LZW extension a permanent part of your library, you
need to provide ImageGear with a valid password, which will be
different from the evaluation password.  After faxing us a copy
of your license from Unisys, (or proof that you do not need a
license), simply call AccuSoft to get your password.

=================================
REPORTING PROBLEMS TO ACCUSOFT
=================================

Please report all problems with ImageGear 6.0 to AccuSoft's
Technical Support staff.  We value your feedback.  You can
report your problems by E-mail, fax, or telephone:

By E-mail: GearTech@accusoft.com   Please take the time to
prepare a thoughtful, intelligent and complete problem report,
as described below.  A copy of this can be found at the end of
this file, and also accompanies your copy of ImageGear.

By Fax: If you don't have access to E-mail, you may fax in your
problem report.  Please fax to: (508) 870-0085. Please take the
time to prepare a thoughtful, intelligent and complete problem
report, as described below.  A copy of this can be found at the
end of this file, and also accompanies your copy of ImageGear.

By phone: (508) 836 - 4896.  Be sure that you have first checked
the manual, and the RELNOTES.TXT file which comes with your copy
of  ImageGear.  It is also recommended that you fill out the
Problem Report shown below, to have on hand when you make your
call to us.  This can greatly facilitate your session with our
support engineers.  

========================== 
AccuSoft Image Guarantee 
========================== 
We guarantee to read any valid raster image stored to any of ImageGear's supported file formats.  If you cannot make your image work, please: 1) Read Chapter 9 - "Analyzing Images" of the ImageGear User Manual 2) If you still can't read your image, please archive it together with your AccuSoft Problem Report (below), and send it to use; we cannot help you with your problem image unless you send it to us.

==========================
ImageGear Problem Report
==========================

PROBLEM REPORT: Please use the problem report included below
when reporting your problem.  Remember to archive the report
together with any pertinent images and/or source code.  For
further reading see the Support Services section of
"Introduction" (Chapter 1) or "Analyzing Images" 
(Chapter 9) of the ImageGear 6.0 User's Manual.

Please take the time to look at our release notes before
bringing a problem to our attention.

AccuSoft will post updates to ImageGear on our BBS and on our
FTP site as soon as they become available.  Please call the
AccuSoft sales department for information about the most 
current release.  Please call our Technical Support line for information on obtaining updates.



                ACCUSOFT IMAGEGEAR TECHNICAL SUPPORT FORM

Please complete this form in its entirety.

CUSTOMER CONTACT INFORMATION
     Name:____________________________________________________
  Company:____________________________________________________
Telephone:____________________________________________________
      Fax:____________________________________________________
   E-Mail:____________________________________________________
           (please include country and city codes if intern'l)

LIBRARY DESCRIPTION (refer to your AccuSoft .LIB,.DLL,.VBX,.OCX)
      Version:_________________________________________________
     Filename:_________________________________________________
     Filedate:_________________________________________________
     Filesize:_________________________________________________

SYSTEM DESCRIPTION
                  Operating System:____________________________
CPU Type (486, Pentium, 68K, etc.):____________________________
                CPU Speed (in MHz):____________________________
          Physical RAM (in MBytes):____________________________
             Swap File (in MBytes):____________________________
                             Video: [ ] 16 colors [ ] 256 colors
                                    [ ] 64K colors
                                    [ ] 16.7 million colors

PROBLEM DESCRIPTION (feel free to use as much space as you need)
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________

Please send this file (archived together with any code and/or
images if necessary) to: GearTech@accusoft.com or fax to (508)
870-0085.
