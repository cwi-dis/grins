#ifndef INC_MPEG2CSS
#define INC_MPEG2CSS

#ifndef INC_MPEG2DEF
#include "mpeg2def.h"
#endif

#ifndef _INC_STDLIB
#include <stdlib.h>
#endif

inline mpeg2_css_t* mpeg2_new_css()
	{
	mpeg2_css_t *css = (mpeg2_css_t *)calloc(1, sizeof(mpeg2_css_t));
	css->varient = -1;
	return css;
	}

inline int mpeg2_delete_css(mpeg2_css_t *css)
	{
	free(css);
	return 0;
	}

inline int mpeg2_init_css(mpeg2_t *file, mpeg2_css_t *css)
	{
	return 0;
	}

inline int mpeg2_get_keys(mpeg2_css_t *css)
	{
	return 1;
	}

inline int mpeg2_decrypt_packet(mpeg2_css_t *css, unsigned char *sector)
	{
	return 1;
	}

#endif // INC_MPEG2CSS


