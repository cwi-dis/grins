GRiNS for Unix

This is the readme file for the GRiNS editor and player Release 0.5,
patchlevel 2 for Silicon Graphics IRIX 6.5 and for Sun Solaris 2.5.
More information on GRiNS can be obtained at
http://www.oratrix.com/GRiNS, or by email to
grins-request@oratrix.com.  Release notes for this version can be
found in the file relnotes.html in the top-level directory.  More
documentation can be found on the homepage.

Prerequisites

The SGI version of the GRiNS editor and player have only been tested
on an SGI O2 running IRIX 6.5.2.  Other systems may or may not work.

The GRiNS editor and player use a number of system shared libraries.
Not all of these libraries are installed by default.  Ask your system
administrator to install these images if they haven't been installed
already.  Which images are installed can be seen with the standard
program versions.  Shared libraries from the following images are
used: compiler_eoe.sw.lib, dmedia_eoe.sw.audio, dmedia_eoe.sw.lib,
eoe.sw.base, eoe.sw.gfx, motif_eoe.sw.eoe, x_eoe.sw.eoe.

Feedback

Bug reports and other technical feedback should be sent to
grins-support@oratrix.com, please check the feedback section on the
homepage for details.

Non-technical feedback should be sent to info@oratrix.com.

Example documents

A number of example documents can be found in the Examples
directory. More examples will be added to the GRiNS home page over
time.

License keys

To start the editor you need a license key. You may have been provided
with a temporary license key in the same message in which you received
the password for the download area. If not you can send an empty mail
message to evalutation-license@oratrix.com and we will send you a
time-limited key, or we will mail you details on how to proceed.

SGI-IRIX user interface open issues

The editor crashes occasionally when deep inside the X/Motif
libraries.  This seems to happen only when Motif dialogs are active.
Save your work regularly.

Sun-Solaris user interface open issues

There seems to be a wide range of audio capabilities on Sun
workstations.  It is not guaranteed that audio works in all
circumstances.
MPEG video rendering on the Sun is slow.
