#ifndef INC_GRINS_ITOPLEVEL
#define INC_GRINS_ITOPLEVEL

#ifndef INC_GRINS_IPLAYER
#include "grins_iplayer.h"
#endif

namespace grins {

struct itoplevel 
	{
	virtual ~itoplevel() {}
	virtual iplayer* get_player() = 0;
	};

} // namespace grins


#endif // INC_GRINS_ITOPLEVEL



