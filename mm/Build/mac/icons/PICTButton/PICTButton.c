/* ----------------------------------------------------------------------

	PICTButton CDEF
	version 1.3.2
	
	Written by: Paul Celestin
	
	Copyright © 1993-1997 Celestin Company, Inc.
	
	Modified by Jack Jansen, CWI.
	
	This CDEF displays a picture whose resource ID is derived from
	the min, max, and value fields of the CNTL. For a multiple-state
	button, set min to ID of the the first PICT and max to the ID of
	the last PICT. Also set value to the ID of the first PICT. PICT max+1 is
	the hilited picture, pict max+2 is the disabled picture.
	
	930822 - 1.0.0	initial release
	930829 - 1.0.1 	added variations 1 and 2
	930915 - 1.0.2	fixed the new variations
	930922 - 1.0.3	fixed a problem with black and white PICTs showing
					up, or so I thought
	931012 - 1.0.4	changed color of text in variation 2 to blue
	931012 - 1.0.5	really fixed problem with black and white PICTs
					showing up properly
	940319 - 1.0.6	removed unnecessary erasing code
	940703 - 1.0.7	now works over multiple monitors of different bit
					depths
	950804 - 1.1.0  finally converted this thing over to CodeWarrior!
	950809 - 1.2.0  fixed bug in hasColor that caused computer to crash
	                if button was partially or completely offscreen
	951215 - 1.3.0  updated to CW7
	970815 - 1.3.2 - updated for CW Pro 1

---------------------------------------------------------------------- */

#include <Types.h>
#include <Memory.h>
#include <Quickdraw.h>
#include <Fonts.h>
#include <ToolUtils.h>
#include <Icons.h>
#include <Controls.h>
#include <Gestalt.h>
#include <Resources.h>

#define kPlain			0
#define kInverted		1

#define HILITED_OFFSET	100
#define BW_OFFSET		0	// No black/white pictures, for now
#define kIsColorPort 	0xC000 // If these bits are set, its a CGrafPort.


/* ----------------------------------------------------------------------
prototypes
---------------------------------------------------------------------- */
pascal long main(short variation, ControlHandle theControl, short message, long param);
int hasColor(Rect);
void drawIt(ControlHandle control,short variation);
long testIt(ControlHandle control, Point myPoint);
static int NextControlValue(ControlHandle theControl);


/* ----------------------------------------------------------------------
main
---------------------------------------------------------------------- */
pascal long main(short variation, ControlHandle theControl, short message, long param)
{
	long	returnValue = 0L;
	char	state = HGetState((Handle)theControl);
	Str255	copyright = "\pCopyright © 1993-1996 Celestin Company, Inc.";

	/*
	** We want to use the upper bit of controlvalue for our magic.
	*/
	if ( GetControlMaximum(theControl) & 0x8000 )
		/*XXXX*/;
	switch(message)
	{
		case drawCntl:
			drawIt(theControl,variation);
		case testCntl:
			returnValue = testIt(theControl, *(Point *) &param);
		case calcCRgns:
			break;
	  	case initCntl:
	  		break;
		case dispCntl:
			break;
		case posCntl:
			break; // SetControlValue(theControl,NextControlValue(theControl));
		case thumbCntl:
			break;
		case dragCntl:
			break;
		case autoTrack:
			break;
		case calcCntlRgn:
			break;
		case calcThumbRgn:
			break;
		default:
			break;
	}

	HSetState((Handle)theControl,state);

	return(returnValue);				/* tell them what happened */
}

static int
NextControlValue(ControlHandle theControl)
{
			if (GetControlValue(theControl) >= GetControlMaximum(theControl))
				return GetControlMinimum(theControl);
			else
				return GetControlValue(theControl) + 1;
}

/* ----------------------------------------------------------------------
hasColor
---------------------------------------------------------------------- */
int hasColor(Rect r)

{
	SysEnvRec		myComputer;
	GDHandle		curDev;
	PixMapHandle	myPixMap;
	
	SysEnvirons(2,&myComputer);
	if (myComputer.hasColorQD)
	{
		LocalToGlobal((Point*) &r);
		LocalToGlobal(1 + (Point*) &r);
		curDev = GetMaxDevice(&r);
		if (curDev != nil)
		{
			myPixMap = (**curDev).gdPMap;
			if ((**myPixMap).pixelSize > 1)
				return(1);
			else
				return(0);
		}
	}
	return(0);
}


/* ----------------------------------------------------------------------
drawIt - here is where we actually draw the control
---------------------------------------------------------------------- */
void drawIt(ControlHandle control, short variation)

{
	short				hilited = 0, useBW = 0;
	int					savedFont, savedSize, savedMode, resid;
	Rect 				myRect;
	GrafPtr				thePort;
	PicHandle			myPicture;
	Str255				myTitle;
	
	GetPort(&thePort);							/* save off the current port */

	if (!(*control)->contrlVis)					/* if not visible, do nothing */
		return;

	myRect = (*control)->contrlRect;

	if (!hasColor(myRect))						/* use the B&W PICTs */
		useBW = BW_OFFSET;
	
	/*
	** Determine which picture to draw
	*/
	
	if ((*control)->contrlHilite == 255) {
		resid = GetControlMaximum(control)+1;
	} else {
#if 0
		if ((*control)->contrlHilite == kControlButtonPart)
		{
			hilited = HILITED_OFFSET;					/* invert while tracking */
			SetControlReference(control, kInverted);
		}
		else
		{
			if ( (GetControlReference(control) == kInverted) && (!Button()) )
			{
				SetControlReference(control, kPlain);
				if (GetControlValue(control) == GetControlMaximum(control))
					SetControlValue(control,GetControlMinimum(control));
				else
					SetControlValue(control,GetControlValue(control) + 1);
			}
		}
		resid = GetControlValue(control) + hilited;
#else
		if ((*control)->contrlHilite == kControlButtonPart)
			resid = NextControlValue(control);
		else
			resid = GetControlValue(control);
#endif
	}

	myPicture = (PicHandle)GetResource('PICT', (resid + useBW));
	
	if ( myPicture == 0L )						/* could not find the PICT */
		return;

	LoadResource((Handle)myPicture);
	HNoPurge((Handle)myPicture);

	DrawPicture(myPicture, &myRect);			/* draw the picture */
	
	switch (variation)
	{
	case 1:										/* display title of control in geneva 9 */
		{
			savedFont = thePort->txFont;		/* save off current values */
			savedSize = thePort->txSize;
			savedMode = thePort->txMode;
			
			ForeColor(blueColor);
			TextFont(kFontIDGeneva);
			TextSize(9);
			TextMode(srcOr);
			
			BlockMove(((*control)->contrlTitle),myTitle,((*control)->contrlTitle)[0] + 1);
			
			MoveTo((myRect.right+myRect.left) / 2 - StringWidth(myTitle) / 2, myRect.bottom - 6);
			DrawString(myTitle);
			
			TextFont(savedFont);				/* restore saved values */
			TextSize(savedSize);
			TextMode(savedMode);
			ForeColor(blackColor);
			
			break;
		}
	case 2:										/* simple 2-pixel wide black border */
		{
			PenSize(2,2);
			InsetRect(&myRect,-3,-3);
			FrameRect(&myRect);
			InsetRect(&myRect,3,3);
			PenSize(1,1);

			break;
		}
	}

#if 0
	if ((*control)->contrlHilite == 255)		/* gray out the picture */
	{
		GetPenState(&oldPenState);
		PenNormal();
		GetIndPattern(&myGray,0,4);
		PenPat(&myGray);
		PenMode(patBic);
		PaintRect(&myRect);
		SetPenState(&oldPenState);
	}
#endif
	
	HPurge((Handle)myPicture);
	
	return;										/* we are done drawing */
}


/* ----------------------------------------------------------------------
testIt - test for mouse hits within control
---------------------------------------------------------------------- */
long testIt(ControlHandle control, Point myPoint)

{
	Rect myRect;

	myRect = (*control)->contrlRect;
	
	if	(((*control)->contrlVis != 0) && ((*control)->contrlHilite != 255) &&
			(PtInRect(myPoint,&myRect)))
		return(kControlButtonPart);
	else
		return(0);
}
