#ifndef INC_GRINS
#define INC_GRINS

#ifndef INC_GRINS_TOPLEVEL
#include "grins_itoplevel.h"
#endif

namespace grins {

class TopLevel;

class Main 
	{
	public:
	Main(const TCHAR *cmdline);
	~Main();

	itoplevel* get_toplevel();

	bool open_file(const TCHAR *pfilename);
	bool open_url(const TCHAR *purl);
	void close();

	private:
	TopLevel *m_toplevel;
	};

} // namespace grins


extern grins::Main *g_pGRiNSMain;


#ifndef INC_GRINS_IPLAYER
#include "grins_iplayer.h"
#endif

inline grins::iplayer* get_player()
	{
	if(g_pGRiNSMain != NULL)
		{
		grins::itoplevel* toplevel = g_pGRiNSMain->get_toplevel();
		if(toplevel != 0)
			return toplevel->get_player();
		}
	return 0;
	}

#endif // INC_GRINS

	