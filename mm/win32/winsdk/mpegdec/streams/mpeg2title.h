#ifndef INC_MPEG2TITLE
#define INC_MPEG2TITLE

#ifndef INC_MPEG2DEF
#include "mpeg2def.h"
#endif

mpeg2_title_t* mpeg2_new_title(mpeg2_t *file, TCHAR *path);
int mpeg2_delete_title(mpeg2_title_t *title);
int mpeg2_copy_title(mpeg2_title_t *dst, mpeg2_title_t *src);
int mpeg2_dump_title(mpeg2_title_t *title);

#endif  // INC_MPEG2TITLE
