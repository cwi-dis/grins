
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include "mpegdisplay.h"

// mpeg2 constants
#include "mpglib/mpeg2dec.h"

// tables used
extern "C" int Inverse_Table_6_9[8][4];
extern "C"  unsigned char *Clip;

MpegDisplay::MpegDisplay(const display_info& di)
:	u422(0), v422(0), u444(0), v444(0),
	m_di(di), 
	m_surf(0)
	{
	if(m_di.chroma_format != CHROMA444)
		{
		if (!u444)
			{
			if (m_di.chroma_format==CHROMA420)
				{
				u422 = new uchar_t[(m_di.coded_picture_width>>1)*m_di.coded_picture_height]; 
				v422 = new uchar_t[(m_di.coded_picture_width>>1)*m_di.coded_picture_height];
				}
			u444 = new uchar_t[m_di.coded_picture_width*m_di.coded_picture_height];
			v444 = new uchar_t[m_di.coded_picture_width*m_di.coded_picture_height];
			}
		}
	}

MpegDisplay::~MpegDisplay()
	{
	if(u422 != 0) delete[] u422;
	if(v422 != 0) delete[] v422;
	if(u444 != 0) delete[] u444;
	if(v444 != 0) delete[] v444;
	}


void MpegDisplay::update_surface(unsigned char *src[], int frame, int offset,int incr, int vsteps)
	{
	if(m_surf == 0) return;

	if (m_di.chroma_format==CHROMA444)
		{
		u444 = src[1];
		v444 = src[2];
		}
	else
		{
		if (m_di.chroma_format==CHROMA420)
			{
			conv420to422(src[1],u422);
			conv420to422(src[2],v422);
			conv422to444(u422,u444);
			conv422to444(v422,v444);
			}
		else
			{
			conv422to444(src[1],u444);
			conv422to444(src[2],v444);
			}
		}

	// matrix coefficients
	int crv = Inverse_Table_6_9[m_di.matrix_coefficients][0];
	int cbu = Inverse_Table_6_9[m_di.matrix_coefficients][1];
	int cgu = Inverse_Table_6_9[m_di.matrix_coefficients][2];
	int cgv = Inverse_Table_6_9[m_di.matrix_coefficients][3];
  
	m_cs.enter();
	color_repr_t *pcr = 0;
	for (int yi=0; yi<vsteps; yi++)
		{
		unsigned char *py = src[0] + offset + incr*yi;
		unsigned char *pu = u444 + offset + incr*yi;
		unsigned char *pv = v444 + offset + incr*yi;
		color_repr_t *pcr = m_surf->get_row(yi);
		for (int xi=0; xi<m_di.horizontal_size; xi++)
			{
			int u = *pu++ - 128;
			int v = *pv++ - 128;
			int y = 76309 * (*py++ - 16); // (255/219)*65536 
			int r = Clip[(y + crv*v + 32768)>>16];
			int g = Clip[(y - cgu*u - cgv*v + 32768)>>16];
			int b = Clip[(y + cbu*u + 32786)>>16];
			// store to bitmap surface for display
			*pcr++ = color_repr_t(r, g, b);
			}
		}
	m_cs.leave();
	}

/* horizontal 1:2 interpolation filter */
void MpegDisplay::conv422to444(unsigned char *src, unsigned char *dst)
{
  int i, i2, w, j, im3, im2, im1, ip1, ip2, ip3;

  w = m_di.coded_picture_width>>1;

  if (m_di.mpeg2_flag)
  {
    for (j=0; j<m_di.coded_picture_height; j++)
    {
      for (i=0; i<w; i++)
      {
        i2 = i<<1;
        im2 = (i<2) ? 0 : i-2;
        im1 = (i<1) ? 0 : i-1;
        ip1 = (i<w-1) ? i+1 : w-1;
        ip2 = (i<w-2) ? i+2 : w-1;
        ip3 = (i<w-3) ? i+3 : w-1;

        /* FIR filter coefficients (*256): 21 0 -52 0 159 256 159 0 -52 0 21 */
        /* even samples (0 0 256 0 0) */
        dst[i2] = src[i];

        /* odd samples (21 -52 159 159 -52 21) */
        dst[i2+1] = Clip[(int)(21*(src[im2]+src[ip3])
                        -52*(src[im1]+src[ip2]) 
                       +159*(src[i]+src[ip1])+128)>>8];
      }
      src+= w;
      dst+= m_di.coded_picture_width;
    }
  }
  else
  {
    for (j=0; j<m_di.coded_picture_height; j++)
    {
      for (i=0; i<w; i++)
      {

        i2 = i<<1;
        im3 = (i<3) ? 0 : i-3;
        im2 = (i<2) ? 0 : i-2;
        im1 = (i<1) ? 0 : i-1;
        ip1 = (i<w-1) ? i+1 : w-1;
        ip2 = (i<w-2) ? i+2 : w-1;
        ip3 = (i<w-3) ? i+3 : w-1;

        /* FIR filter coefficients (*256): 5 -21 70 228 -37 11 */
        dst[i2] =   Clip[(int)(  5*src[im3]
                         -21*src[im2]
                         +70*src[im1]
                        +228*src[i]
                         -37*src[ip1]
                         +11*src[ip2]+128)>>8];

       dst[i2+1] = Clip[(int)(  5*src[ip3]
                         -21*src[ip2]
                         +70*src[ip1]
                        +228*src[i]
                         -37*src[im1]
                         +11*src[im2]+128)>>8];
      }
      src+= w;
      dst+= m_di.coded_picture_width;
    }
  }
}

/* vertical 1:2 interpolation filter */
void MpegDisplay::conv420to422(unsigned char *src, unsigned char *dst)
{
  int w, h, i, j, j2;
  int jm6, jm5, jm4, jm3, jm2, jm1, jp1, jp2, jp3, jp4, jp5, jp6, jp7;

  w = m_di.coded_picture_width>>1;
  h = m_di.coded_picture_height>>1;

  if (m_di.progressive_frame)
  {
    /* intra frame */
    for (i=0; i<w; i++)
    {
      for (j=0; j<h; j++)
      {
        j2 = j<<1;
        jm3 = (j<3) ? 0 : j-3;
        jm2 = (j<2) ? 0 : j-2;
        jm1 = (j<1) ? 0 : j-1;
        jp1 = (j<h-1) ? j+1 : h-1;
        jp2 = (j<h-2) ? j+2 : h-1;
        jp3 = (j<h-3) ? j+3 : h-1;

        /* FIR filter coefficients (*256): 5 -21 70 228 -37 11 */
        /* New FIR filter coefficients (*256): 3 -16 67 227 -32 7 */
        dst[w*j2] =     Clip[(int)(  3*src[w*jm3]
                             -16*src[w*jm2]
                             +67*src[w*jm1]
                            +227*src[w*j]
                             -32*src[w*jp1]
                             +7*src[w*jp2]+128)>>8];

        dst[w*(j2+1)] = Clip[(int)(  3*src[w*jp3]
                             -16*src[w*jp2]
                             +67*src[w*jp1]
                            +227*src[w*j]
                             -32*src[w*jm1]
                             +7*src[w*jm2]+128)>>8];
      }
      src++;
      dst++;
    }
  }
  else
  {
    /* intra field */
    for (i=0; i<w; i++)
    {
      for (j=0; j<h; j+=2)
      {
        j2 = j<<1;

        /* top field */
        jm6 = (j<6) ? 0 : j-6;
        jm4 = (j<4) ? 0 : j-4;
        jm2 = (j<2) ? 0 : j-2;
        jp2 = (j<h-2) ? j+2 : h-2;
        jp4 = (j<h-4) ? j+4 : h-2;
        jp6 = (j<h-6) ? j+6 : h-2;

        /* Polyphase FIR filter coefficients (*256): 2 -10 35 242 -18 5 */
        /* New polyphase FIR filter coefficients (*256): 1 -7 30 248 -21 5 */
        dst[w*j2] = Clip[(int)(  1*src[w*jm6]
                         -7*src[w*jm4]
                         +30*src[w*jm2]
                        +248*src[w*j]
                         -21*src[w*jp2]
                          +5*src[w*jp4]+128)>>8];

        /* Polyphase FIR filter coefficients (*256): 11 -38 192 113 -30 8 */
        /* New polyphase FIR filter coefficients (*256):7 -35 194 110 -24 4 */
        dst[w*(j2+2)] = Clip[(int)( 7*src[w*jm4]
                             -35*src[w*jm2]
                            +194*src[w*j]
                            +110*src[w*jp2]
                             -24*src[w*jp4]
                              +4*src[w*jp6]+128)>>8];

        /* bottom field */
        jm5 = (j<5) ? 1 : j-5;
        jm3 = (j<3) ? 1 : j-3;
        jm1 = (j<1) ? 1 : j-1;
        jp1 = (j<h-1) ? j+1 : h-1;
        jp3 = (j<h-3) ? j+3 : h-1;
        jp5 = (j<h-5) ? j+5 : h-1;
        jp7 = (j<h-7) ? j+7 : h-1;

        /* Polyphase FIR filter coefficients (*256): 11 -38 192 113 -30 8 */
        /* New polyphase FIR filter coefficients (*256):7 -35 194 110 -24 4 */
        dst[w*(j2+1)] = Clip[(int)( 7*src[w*jp5]
                             -35*src[w*jp3]
                            +194*src[w*jp1]
                            +110*src[w*jm1]
                             -24*src[w*jm3]
                              +4*src[w*jm5]+128)>>8];

        dst[w*(j2+3)] = Clip[(int)(  1*src[w*jp7]
                             -7*src[w*jp5]
                             +30*src[w*jp3]
                            +248*src[w*jp1]
                             -21*src[w*jm1]
                              +5*src[w*jm3]+128)>>8];
      }
      src++;
      dst++;
    }
  }
}
