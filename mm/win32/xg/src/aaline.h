#ifndef INC_AALINE
#define INC_AALINE

// What follows is based on:
// Sample code to draw antialiased lines as described in the Journal of Graphic Tools article 
// "High Quality Hardware Line Antialiasing" by Scott R. Nelson of Sun Microsystems.

//  C++ porting by Kleanthis Kleanthous. 

namespace aa {

typedef double user_t;
typedef long int fix_xy;	// S11.20
typedef long int fix_rgb;	// S1.30
typedef long int fix_dec;	// Sx.y


// Convert from floating-point to internal fixed-point formats
const fix_dec ONE_XY = 0x00100000;
const fix_dec FIX_XY_SHIFT = 20;
const fix_dec ONEHALF_XY = 0x00080000;
const fix_dec ONE_RGB = 0x40000000;
const fix_dec MASK_FRACT_XY = 0x000fffff;
const fix_dec MASK_FLOOR_XY = 0xfff00000;

template <class T>
inline fix_dec FLOAT_TO_FIX_XY(T x) {return  fix_dec(x * user_t(ONE_XY));}

template <class T>
inline fix_dec FLOAT_TO_FIX_RGB(T x) {return  fix_dec(x * user_t(ONE_RGB));}

template <class T>
inline fix_dec FIX_TO_INT_XY(T x) {return x >> FIX_XY_SHIFT;}

template <class T>
inline user_t FIX_TO_FLOAT_XY(T x) {return user_t(x) / user_t(ONE_XY);}

template <class T>
inline user_t FIX_TO_FLOAT_RGB(T x) {return user_t(x) / user_t(ONE_RGB);}

template <class T>
inline fix_dec FRACT_XY(T x) {return x & MASK_FRACT_XY;}

template <class T>
inline fix_dec FLOOR_XY(T x) {return x & MASK_FLOOR_XY;}

// Get fractional part, next lowest integer part
template <class T>
inline fix_dec FIX_XY_TO_INT(T x) {return  x >> FIX_XY_SHIFT;}


const fix_dec EP_MASK	= 0x000f0000u;	// AA line end-point filter mask
const fix_dec EP_SHIFT	= 13u;	// Number of bits to shift end-point

// One vertex at any of the various stages of the pipeline
struct vertex
	{
    user_t x, y;
    user_t r, g, b, a;
	};

// All values needed to draw one line
struct setup_line 
	{
    bool x_major;
    bool negative;

    fix_xy vs;			// Starting point
    fix_xy us;
    fix_xy ue;			// End (along major axis)
    fix_xy dvdu;		// Delta for minor axis step

    fix_rgb rs; // Starting color
    fix_rgb gs;
    fix_rgb bs;
    fix_rgb as;

    fix_rgb drdu;   // Delta for color
    fix_rgb dgdu;
    fix_rgb dbdu;
    fix_rgb dadu;
	};


// graphics table sizes
#define FILTER_WIDTH	0.75	// Line filter width adjustment
#define F_TABLE_SIZE	64		// Filter table size
#define SC_TABLE_SIZE	32		// Slope correction table size
#define SRT_INT		5	// Sqrt table index integer bits
#define SRT_FRACT	4	// ...fraction bits
#define SR_INT		3	// Square root result integer bits
#define SR_FRACT	5	// ...fraction bits
#define SR_TABLE_SIZE	(1 << (SRT_INT + SRT_FRACT))

#define BLEND_ARBITRARY	1	// Blend to arbitrary background color
#define BLEND_CONSTANT	2	// Blend to constant background color
#define ADD_TO_BACKGROUND 3	// Add to background color

template<class T>
class toolkit
	{
	public:
	typedef T value_type;

	toolkit()
		{
		build_slope_corr_table();
		build_filter_table();
		build_sqrt_table();

		antialiased = true;
		capline = false;
		blendmode = BLEND_CONSTANT;
		background = 0x000000;
		}

	void build_slope_corr_table();
	void build_filter_table();
	void build_sqrt_table();

	bool antialiased;		// Antialiased lines, not jaggy 
	bool capline;			// Draw last pixel of jaggy lines 
    int blendmode;			// Which blend mode to use 
	int background;			// Black 

	value_type slope_corr_table[SC_TABLE_SIZE];
	value_type filter_table[F_TABLE_SIZE];
	value_type sqrt_table[SR_TABLE_SIZE];
	};

typedef toolkit<long> xtoolkit;

/*
	Build slope correction table.  The index into this table
	is the truncated 5-bit fraction of the slope used to draw
	the line.  Round the computed values here to get the closest
	fit for all slopes matching an entry.
*/

template<class T>
inline void toolkit<T>::build_slope_corr_table()
	{
    for(int i = 0; i < SC_TABLE_SIZE; i++) 
		{
		// Round and make a fraction 
		double m = ((double) i + 0.5) / double(SC_TABLE_SIZE);
		double v = sqrt(m * m + 1) * 0.707106781; // (m + 1)^2 / sqrt(2)
		slope_corr_table[i] = (value_type) (v * 256.0);
		}
	}

// Build the Gaussian filter table, round to the middle of the sample region.
template<class T>
inline void toolkit<T>::build_filter_table()
	{
    for (int i = 0; i < F_TABLE_SIZE; i++) 
		{
		double d = (double(i) + 0.5) / double(F_TABLE_SIZE/2.0);
		d /= FILTER_WIDTH;
		double v = 1.0 / exp(d * d);		// Gaussian function 
		filter_table[i] = value_type(v * 256.0);
		}
	}

// Build the square root table for big dots.
template<class T>
inline void toolkit<T>::build_sqrt_table()
	{
    for(int i = 0; i < SR_TABLE_SIZE; i++) 
		{
		double v = (double) ((i << 1) + 1) / double(1 << (SRT_FRACT + 1));
		double sr = sqrt(v);
		sqrt_table[i] = (value_type) (sr * double(1 << SR_FRACT));
		}
    }

template<class T>
class line
	{
	public:
	vertex first, second;
	
	line(toolkit<T>& tk, xg::surface<T>& fb)
		:	xtk(tk), frame_buffer(fb) {}
	void draw();
	
	
	private:
	toolkit<T>& xtk;
	xg::surface<T>& frame_buffer;

	void setup(setup_line& l);
	
	void draw_hspan(fix_xy x, fix_xy y, fix_rgb r, fix_rgb g, fix_rgb b, 
		long int  ep_corr, long int slope);
	void draw_vspan(fix_xy x, fix_xy y, fix_rgb r, fix_rgb g, fix_rgb b, 
		long int  ep_corr, long int slope);
	
	T fix_xy_mult(T a, fix_xy b);
	T clamp_rgb(T x);
	T float_to_fix(user_t x, T one);

	void process_pixel(unsigned x, unsigned y, unsigned long color);
	};

typedef line<long> xline;

// Clamp a fixed-point color value and return it as an 8-bit value.
template<class T>
inline T line<T>::clamp_rgb(T x)
	{
    if (x < 0) x = 0;
    else if (x >= ONE_RGB) x = ONE_RGB - 1;
    return (x >> (30 - 8));
	} 

/*
 *---------------------------------------------------------------
 *
 * fix_xy_mult
 *
 *	Multiply a fixed-point number by a s11.20 fixed-point
 *	number.  The actual multiply uses less bits for the
 *	multiplier, since it always represents a fraction
 *	less than 1.0 and less total bits are sufficient.
 *	Some of the steps here are not needed.  This was originally
 *	written to simulate exact hardware behavior.
 *
 *	This could easily be optimized when using a flexible compiler.
 *
 *---------------------------------------------------------------
 */
template<class T>
inline T line<T>::fix_xy_mult(T a, fix_xy b)
	{
    int negative;			/* 1 = result is negative */
    int a1;				/* Multiplier */
    int bh, bl;				/* Multiplicant (high and low) */
    int ch, cl, c;			/* Product */

    /* Determine the sign, then force multiply to be unsigned */
    negative = 0;
    if (a < 0) {
		negative ^= 1;
		a = -a;
		}
    if (b < 0) {
		negative ^= 1;
		b = -b;
    }

    /* Grab the bits we want to use */
    a1 = a >> 10;			/* Just use 10-bit fraction */

    /* Split the 32-bit number into two 16-bit halves */
    bh = (b >> 16) & 0xffff;
    bl = b & 0xffff;

    /* Perform the multiply */
    ch = bh * a1;			/* 30 bit product (with no carry) */
    cl = bl * a1;
    /* Put the halves back together again */
    c = (ch << 6) + (cl >> 10);
    if (negative)
		c = -c;

    return c;
	} 


template<class T>
inline void line<T>::setup(setup_line& l)
	{
	vertex *v1 = &first;
	vertex *v2 = &second;

    user_t dx, dy;			/* Deltas in X and Y */
    user_t udx, udy;			/* Positive version of deltas */
    user_t one_du;			/* 1.0 / udx or udy */

    dx = v1->x - v2->x;
    if (dx < 0.0)
		udx = -dx;
    else
		udx = dx;

   dy = v1->y - v2->y;
   if (dy < 0.0)
		udy = -dy;
    else
		udy = dy;

    if (udx > udy) 
		{
		/* X major line */
		l.x_major = true;
		l.negative = (dx < 0.0);
		l.us = FLOAT_TO_FIX_XY(v2->x);
		l.vs = FLOAT_TO_FIX_XY(v2->y);
		l.ue = FLOAT_TO_FIX_XY(v1->x);
		one_du = 1.0f / udx;
		l.dvdu = FLOAT_TO_FIX_XY(dy * one_du);
		}
    else 
		{
		/* Y major line */
		l.x_major = false;
		l.negative = (dy < 0.0);
		l.us = FLOAT_TO_FIX_XY(v2->y);
		l.vs = FLOAT_TO_FIX_XY(v2->x);
		l.ue = FLOAT_TO_FIX_XY(v1->y);
		one_du = 1.0f / udy;
		l.dvdu = FLOAT_TO_FIX_XY(dx * one_du);
		}

    /* Convert start Z and colors to fixed-point */
    //l.zs = FLOAT_TO_FIX_Z(v2->z);
    l.rs = FLOAT_TO_FIX_RGB(v2->r);
    l.gs = FLOAT_TO_FIX_RGB(v2->g);
    l.bs = FLOAT_TO_FIX_RGB(v2->b);
    l.as = FLOAT_TO_FIX_RGB(v2->a);

    /* Compute delta values for Z and colors */
    //l.dzdu = FLOAT_TO_FIX_Z((v1->z - v2->z) * one_du);
    l.drdu = FLOAT_TO_FIX_RGB((v1->r - v2->r) * one_du);
    l.dgdu = FLOAT_TO_FIX_RGB((v1->g - v2->g) * one_du);
    l.dbdu = FLOAT_TO_FIX_RGB((v1->b - v2->b) * one_du);
    l.dadu = FLOAT_TO_FIX_RGB((v1->a - v2->a) * one_du);
	}

template<class T>
inline void line<T>::draw()
	{
    setup_line l;
	setup(l);
	setup_line *pl = &l;

    fix_xy x, y;				// Start value 
    fix_xy dudu;				// Constant 1 or -1 for step 
    fix_xy dx, dy;				// Steps in X and Y 
    fix_rgb r, g, b, a;
    fix_xy u_off;				// Offset to starting sample grid 
    fix_xy us, vs, ue;			// Start and end for drawing 
    fix_xy count;				// How many pixels to draw 

    long int color;				// Color of generated pixel 
    long int slope_index;		// Index into slope correction table 
    long int slope;				// Slope correction value 
    long int ep_corr;			// End-point correction value 
    long int scount, ecount;	// Start/end count for endpoints 
    long int sf, ef;			// Sand and end fractions 
    long int ep_code;			// One of 9 endpoint codes 

    // Get directions 
    if (pl->negative)
		dudu = -ONE_XY;
    else
		dudu = ONE_XY;

    if (pl->x_major) 
		{
		dx = dudu;
		dy = pl->dvdu;
		}
    else 
		{
		dx = pl->dvdu;
		dy = dudu;
		}

    // Get initial values and count 
    if (xtk.antialiased) 
		{
		// Antialiased 
		if (pl->negative) 
			{
			u_off = FRACT_XY(pl->us) - ONE_XY;
			us = pl->us + ONE_XY;
			ue = pl->ue;
			count = FLOOR_XY(us) - FLOOR_XY(ue);
			}
		else 
			{
			u_off = 0 - FRACT_XY(pl->us);
			us = pl->us;
			ue = pl->ue + ONE_XY;
			count = FLOOR_XY(ue) - FLOOR_XY(us);
			}
		}
    else 
		{
		// Jaggy 
		if (pl->negative) 
			{
			u_off = FRACT_XY(pl->us + ONEHALF_XY) - ONEHALF_XY;
			us = FLOOR_XY(pl->us + ONEHALF_XY);
			ue = FLOOR_XY(pl->ue - ONEHALF_XY);
			count = us - ue;
			}
		else 
			{
			u_off = ONEHALF_XY - FRACT_XY(pl->us - ONEHALF_XY);
			us = FLOOR_XY(pl->us + ONEHALF_XY);
			ue = FLOOR_XY(pl->ue + ONEHALF_XY + ONE_XY);
			count = ue - us;
			}
		}

    vs = pl->vs + fix_xy_mult(pl->dvdu, u_off) + ONEHALF_XY;

    if (pl->x_major) 
		{
		x = us;
		y = vs;
		}
    else 
		{
		x = vs;
		y = us;
		}

    //z = pl->zs + fix_xy_mult(pl->dzdu, u_off);
    r = pl->rs + fix_xy_mult(pl->drdu, u_off);
    g = pl->gs + fix_xy_mult(pl->dgdu, u_off);
    b = pl->bs + fix_xy_mult(pl->dbdu, u_off);
    a = pl->as + fix_xy_mult(pl->dadu, u_off);

    if (!xtk.antialiased) 
		{
		// Jaggy line 

		// If not capped, shorten by one 
		if (!xtk.capline)
			count -= ONE_XY;

		// Interpolate the edges
		while ((count -= ONE_XY) >= 0) 
			{
			// Now interpolate the pixels of the span 
			color = clamp_rgb(r) |
			(clamp_rgb(g) << 8) |
			(clamp_rgb(b) << 16) |
			(clamp_rgb(a) << 24);
			process_pixel(FIX_XY_TO_INT(x), FIX_XY_TO_INT(y), color);

			x += dx;
			y += dy;
			//z += pl->dzdu;
			r += pl->drdu;
			g += pl->dgdu;
			b += pl->dbdu;
			a += pl->dadu;
			} 
		} 

    else 
		{
		// Antialiased line 

		// Compute slope correction once per line 
		slope_index = (pl->dvdu >> (FIX_XY_SHIFT - 5)) & 0x3fu;
		if (pl->dvdu < 0)
			slope_index ^= 0x3fu;
		if ((slope_index & 0x20u) == 0)
			slope = xtk.slope_corr_table[slope_index];
		else
			slope = 0x100;		// True 1.0 

		// Set up counters for determining endpoint regions 
		scount = 0;
		ecount = FIX_TO_INT_XY(count);

		// Get 4-bit fractions for end-point adjustments 
		sf = (us & EP_MASK) >> EP_SHIFT;
		ef = (ue & EP_MASK) >> EP_SHIFT;

		/* Interpolate the edges */
		while (count >= 0) 
			{
			/*-
			* Compute end-point code (defined as follows):
			*  0 =  0, 0: short, no boundary crossing
			*  1 =  0, 1: short line overlap (< 1.0)
			*  2 =  0, 2: 1st pixel of 1st endpoint
			*  3 =  1, 0: short line overlap (< 1.0)
			*  4 =  1, 1: short line overlap (> 1.0)
			*  5 =  1, 2: 2nd pixel of 1st endpoint
			*  6 =  2, 0: last of 2nd endpoint
			*  7 =  2, 1: first of 2nd endpoint
			*  8 =  2, 2: regular part of line
			*/
			ep_code = ((scount < 2) ? scount : 2) * 3 + ((ecount < 2) ? ecount : 2);
			if (pl->negative) 
				{
				// Drawing in the negative direction 

				// Compute endpoint information 
				switch (ep_code) 
					{
					case 0: ep_corr = 0;				break;
					case 1: ep_corr = ((sf - ef) & 0x78) | 4;	break;
					case 2: ep_corr = sf | 4;			break;
					case 3: ep_corr = ((sf - ef) & 0x78) | 4;	break;
					case 4: ep_corr = ((sf - ef) + 0x80) | 4;	break;
					case 5: ep_corr = (sf + 0x80) | 4;		break;
					case 6: ep_corr = (0x78 - ef) | 4;		break;
					case 7: ep_corr = ((0x78 - ef) + 0x80) | 4;	break;
					case 8: ep_corr = 0x100;			break;
					} 
				}
			else 
				{
				// Drawing in the positive direction 

				// Compute endpoint information 
				switch (ep_code) 
					{
					case 0: ep_corr = 0;				break;
					case 1: ep_corr = ((ef - sf) & 0x78) | 4;	break;
					case 2: ep_corr = (0x78 - sf) | 4;		break;
					case 3: ep_corr = ((ef - sf) & 0x78) | 4;	break;
					case 4: ep_corr = ((ef - sf) + 0x80) | 4;	break;
					case 5: ep_corr = ((0x78 - sf) + 0x80) | 4;   break;
					case 6: ep_corr = ef | 4;			break;
					case 7: ep_corr = (ef + 0x80) | 4;		break;
					case 8: ep_corr = 0x100;			break;
					} 
				}

			if (pl->x_major)
				draw_hspan(x, y, r, g, b, ep_corr, slope);
			else
				draw_vspan(x, y, r, g, b, ep_corr, slope);

			x += dx;
			y += dy;
			//z += pl->dzdu;
			r += pl->drdu;
			g += pl->dgdu;
			b += pl->dbdu;
			a += pl->dadu;

			scount++;
			ecount--;
			count -= ONE_XY;
			} 
		} 
	}

// Draw one span of an antialiased line (for horizontal lines).
template<class T>
inline void line<T>::draw_hspan(fix_xy x, fix_xy y, fix_rgb r, fix_rgb g, fix_rgb b, 
	long int ep_corr, long int slope)
	{
    long int sample_dist;		// Distance from line to sample point
    long int filter_index;		// Index into filter table
    long int i;				// Count pixels across span
    long int index;			// Final filter table index
    fix_rgb a;				// Alpha
    long int color;			// Final pixel color

    sample_dist = (FRACT_XY(y) >> (FIX_XY_SHIFT - 5)) - 16;
    y = y - ONE_XY;
    filter_index = sample_dist + 32;

    for (i = 0; i < 4; i++) 
		{
		if (filter_index < 0)
			index = ~filter_index;	// Invert when negative
		else
			index = filter_index;
		if (index > 47)
			continue;			// Not a valid pixel

		a = ((((slope * ep_corr) & 0x1ff00) * xtk.filter_table[index]) &
			0xff0000) >> 16;
		// Should include the alpha value as well...

		// Draw the pixel
		color = clamp_rgb(r) | (clamp_rgb(g) << 8) | (clamp_rgb(b) << 16) | (a << 24);
		process_pixel(FIX_XY_TO_INT(x), FIX_XY_TO_INT(y),color);

		filter_index -= 32;
		y += ONE_XY;
		}
	} 


// Draw one span of an antialiased line (for vertical lines).
template<class T>
inline void line<T>::draw_vspan(fix_xy x, fix_xy y, fix_rgb r, fix_rgb g, fix_rgb b, 
	long int ep_corr, long int slope)
	{
    long int sample_dist;		// Distance from line to sample point
    long int filter_index;		// Index into filter table
    long int i;				// Count pixels across span
    long int index;			// Final filter table index
    fix_rgb a;				// Alpha
    long int color;			// Final pixel color

    sample_dist = (FRACT_XY(x) >> (FIX_XY_SHIFT - 5)) - 16;
    x = x - ONE_XY;
    filter_index = sample_dist + 32;

    for (i = 0; i < 4; i++) 
		{
		if (filter_index < 0) index = ~filter_index;	// Invert when negative
		else index = filter_index;
		if (index > 47) continue;			// Not a valid pixel

		a = ((((slope * ep_corr) & 0x1ff00) * xtk.filter_table[index]) & 0xff0000) >> 16;
		// Should include the alpha value as well...

		// Draw the pixel
		color = clamp_rgb(r) | (clamp_rgb(g) << 8) | (clamp_rgb(b) << 16) | (a << 24);
		process_pixel(FIX_XY_TO_INT(x), FIX_XY_TO_INT(y), color);

		filter_index -= 32;
		x += ONE_XY;
		}
	}


// Perform blending and draw the pixel
template<class T>
inline void line<T>::process_pixel(unsigned x, unsigned y, unsigned long color)
	{
    int cr, cg, cb;			// The color components
    int ca;				    // The alpha values
    int a1;				    // 1 - alpha
    int or, og, ob;			// Old RGB values
    int old_color;			// The old color value
    int nr, ng, nb;			// New RGB values
    int new_color;			// The new color value
    int br, bg, bb;			// Background color

    if(x>=frame_buffer.get_width() || y>=frame_buffer.get_height())
		return;

    cr = color & 0xff;
    cg = (color >> 8) & 0xff;
    cb = (color >> 16) & 0xff;
    ca = (color >> 24) & 0xff;

    old_color = frame_buffer.pixel(x,y);

    if (!xtk.antialiased) 
		{
		// No blending
		new_color = cr | (cg << 8) | (cb << 16);
		frame_buffer.pixel(x, y) = new_color;
		return;				
		}

    or = old_color & 0xff;
    og = (old_color >> 8) & 0xff;
    ob = (old_color >> 16) & 0xff;

    // Blend to arbitrary background
    if (xtk.blendmode == BLEND_ARBITRARY) 
		{
		a1 = ca ^ 0xff;			// 1's complement is close enough

		nr = ((cr * ca) >> 8) + ((or * a1) >> 8);
		if (nr > 0xff)nr = 0xff;			// Clamp

		ng = ((cg * ca) >> 8) + ((og * a1) >> 8);
		if (ng > 0xff) ng = 0xff;			// Clamp

		nb = ((cb * ca) >> 8) + ((ob * a1) >> 8);
		if (nb > 0xff) nb = 0xff;			// Clamp
		}

    // Blend to constant background
    if (xtk.blendmode == BLEND_CONSTANT) 
		{
		br =  xtk.background & 0xff;		// Sorry this isn't optimized
		bg = (xtk.background >> 8) & 0xff;
		bb = (xtk.background >> 16) & 0xff;

		nr = (((cr - br) * ca) >> 8) + or;
		if (nr > 0xff) nr = 0xff;			// Clamp
		if (nr < 0) nr = 0;

		ng = (((cg - bg) * ca) >> 8) + og;
		if (ng > 0xff) ng = 0xff;			// Clamp
		if (ng < 0) ng = 0;

		nb = (((cb - bb) * ca) >> 8) + ob;
		if (nb > 0xff) nb = 0xff;			// Clamp
		if (nb < 0) nb = 0;
		}

    // Add to background
    if (xtk.blendmode == ADD_TO_BACKGROUND) 
		{
		nr = ((cr * ca) >> 8) + or;
		if (nr > 0xff) nr = 0xff;			// Clamp

		ng = ((cg * ca) >> 8) + og;
		if (ng > 0xff)ng = 0xff;			// Clamp

		nb = ((cb * ca) >> 8) + ob;
		if (nb > 0xff) nb = 0xff;			// Clamp
		}

    new_color = nr | (ng << 8) | (nb << 16);
	frame_buffer.pixel(x, y) = new_color;
	}

} // namespace aa

#endif // INC_AALINE