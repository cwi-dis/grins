// xglab.cpp : Defines the entry point for the console application.
//

#include "stdafx.h"

#include "xg.h"
#include "aaline.h"

void drawOn(xg::xsurface&  xsurf);

aa::xtoolkit xtk;

int main(int argc, char* argv[])
	{
	int w = 800, h = 600;

	xtk.blendmode = BLEND_CONSTANT;
	xtk.background = 0xFFFFFF;

	xg::xsurface xsurf(w, h, xtk.background);
	drawOn(xsurf);
	xsurf.save_as_bmp("test.bmp");

	return 0;
	}


// Adjusted test from:
// Sample code to draw antialiased lines as described in the Journal of Graphic Tools article 
// "High Quality Hardware Line Antialiasing" by Scott R. Nelson of Sun Microsystems.

void drawOn(xg::xsurface& xsurf)
	{
	aa::xline line(xtk, xsurf);

    aa::user_t cx, cy;			// Center X and Y 
    aa::user_t sx, sy;			// Scale X and Y 
    aa::user_t nx, ny;			// New X and Y, from trig functions 
    aa::user_t x1, y1, x2, y2;		// Computed values 
    aa::user_t angle;

    // Initialize the colors 
    line.first.r = 0.75;			// Almost white 
    line.first.g = 0.75;
    line.first.b = 0.75;
    line.first.a = 1.0;

    line.second.r = 0.75;
    line.second.g = 0.75;
    line.second.b = 0.75;
    line.second.a = 1.0;

    // Radial lines, in to out 
    cx = 150.2;
    cy = 150.2;
    sx = 125.0;
    sy = 125.0;
    for (angle = 0.0; angle < 360.0; angle += 2.0f) 
		{
		nx = (aa::user_t)sin(angle * 3.1415926535 / 180.0);
		ny = (aa::user_t)cos(angle * 3.1415926535 / 180.0);
		x1 = cx;
		y1 = cy;
		x2 = nx * sx + cx;
		y2 = ny * sy + cy;
		line.first.x = x1;
		line.first.y = y1;
		line.second.x = x2;
		line.second.y = y2;
		line.draw();
		}

    // Radial lines, out to in, change color along lines 
    line.first.r = 0.0;				// Blue center 
    line.first.g = 0.0;
    line.first.b = 0.5;
    line.second.r = 1.0;				// Yellow edge 
    line.second.g = 1.0;
    line.second.b = 0.0;
    cx = 400.2;
    cy = 150.2;
    sx = 125.0;
    sy = 125.0;
    for (angle = 0.0; angle < 360.0; angle += 5.0) 
		{
		nx = (aa::user_t)sin(angle * 3.1415926535 / 180.0);
		ny = (aa::user_t)cos(angle * 3.1415926535 / 180.0);
		x1 = cx;
		x2 = nx * sx + cx;
		y2 = ny * sy + cy;
		line.first.x = x1;
		line.first.y = y1;
		line.second.x = x2;
		line.second.y = y2;
		line.draw();
		}

    // Radial lines, with saturation 
    line.first.r = 1.0;				// Orange 
	y1 = cy;
    line.first.g = 0.4;
    line.first.b = 0.1;
    line.second.r = 1.0;
    line.second.g = 0.4;
    line.second.b = 0.1;
    cx = 570.0;
    cy = 70.0;
    sx = 65.0;
    sy = 65.0;
    for (angle = 0.0; angle < 360.0; angle += 5.0) 
		{
		nx = (aa::user_t)sin(angle * 3.1415926535 / 180.0);
		ny = (aa::user_t)cos(angle * 3.1415926535 / 180.0);
		x1 = cx;
		y1 = cy;
		x2 = nx * sx + cx;
		y2 = ny * sy + cy;
		line.first.x = x1;
		line.first.y = y1;
		line.second.x = x2;
		line.second.y = y2;
		line.draw();
		}

    // Concentric circles 
    line.first.r = 0.5;				// Medium grey 
    line.first.g = 0.5;
    line.first.b = 0.5;
    line.second.r = 0.5;
    line.second.g = 0.5;
    line.second.b = 0.5;
    cx = 105.0;
    cy = 375.0;
    for (sx = 90.0; sx > 40.0; sx *= 0.97f) 
		{
		sy = sx;
		x1 = (aa::user_t)sin(0.0) * sx + cx;
		y1 = (aa::user_t)cos(0.0) * sy + cy;
		for (angle = 0.0; angle < 361.0; angle += 2.0f) 
			{
			nx = (aa::user_t)sin(angle * 3.1415926535 / 180.0);
			ny = (aa::user_t)cos(angle * 3.1415926535 / 180.0);
			x2 = nx * sx + cx;
			y2 = ny * sy + cy;
			line.first.x = x1;
			line.first.y = y1;
			line.second.x = x2;
			line.second.y = y2;
			x1 = x2;
			y1 = y2;
			line.draw();
			}
		}

    // Small circles 
    line.first.r = 0.25;			// Light blue 
    line.first.g = 0.5;
    line.first.b = 1.0;
    line.second.r = 0.25;
    line.second.g = 0.5;
    line.second.b = 1.0;
    cx = 250.0;
    cy = 310.0;
    for (sx = 12.0; sx > 0.5; sx *= 0.93f) 
		{
		sy = sx;
		x1 = (aa::user_t)sin(0.0) * sx + cx;
		y1 = (aa::user_t)cos(0.0) * sy + cy;
		for (angle = 0.0; angle < 361.0; angle += 2.0) 
			{
			nx = (aa::user_t)sin(angle * 3.1415926535 / 180.0);
			ny = (aa::user_t)cos(angle * 3.1415926535 / 180.0);
			x2 = nx * sx + cx;
			y2 = ny * sy + cy;
			line.first.x = x1;
			line.first.y = y1;
			line.second.x = x2;
			line.second.y = y2;
			x1 = x2;
			y1 = y2;
			line.draw();
			}
		cx += sx * 2.0f + 4.0;
		if (cx > 500.0f) 
			{
			cx = 250.0;
			cy += sy * 2.0f + 12.0;
			}
		}
	} 
