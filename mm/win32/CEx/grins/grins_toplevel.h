#ifndef INC_GRINS_TOPLEVEL
#define INC_GRINS_TOPLEVEL


class tree_node;

namespace grins {

class Main;

class TopLevel 
	{
	public:
	TopLevel(Main *pMain, const TCHAR *url);
	~TopLevel();

	bool read_it();

	private:
	Main *m_pMain;
	std::basic_string<TCHAR> m_url;
	tree_node *m_root;
	};

} // namespace grins


#endif // INC_GRINS_TOPLEVEL



