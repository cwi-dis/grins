#ifndef INC_GRINS_TOPLEVEL
#define INC_GRINS_TOPLEVEL

#ifndef INC_GRINS_ITOPLEVEL
#include "grins_itoplevel.h"
#endif

namespace smil {
	class node;
	}

namespace grins {

class Main;
struct iplayer;
class Player;

class TopLevel : public itoplevel
	{
	public:
	TopLevel(Main *pMain, const TCHAR *url);
	~TopLevel();

	bool read_it();
	
	virtual iplayer* get_player();
	
	smil::node* get_root() {return m_root;}
	const std::basic_string<TCHAR>& get_document_url() {return m_url;}

	private:
	void makeplayer();

	Main *m_pMain;
	std::basic_string<TCHAR> m_url;
	smil::node *m_root;
	Player *m_player;
	};

} // namespace grins


#endif // INC_GRINS_TOPLEVEL



