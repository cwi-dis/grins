#include "stdenv.h"

#include "grins_player.h"

#include "grins_toplevel.h"

#include "smil/smil_node.h"

#include "windowinterface.h"
#include "charconv.h"

namespace grins {

Player::Player(TopLevel *toplevel)
:	m_toplevel(toplevel) 
	{
	}
		
Player::~Player()
	{
	}

void Player::play()
	{
	// test code
	const char *src = test_get_first_img();
	if(src != 0)
		{
		std::basic_string<TCHAR> str = m_toplevel->get_document_url();
		int pos = str.find_last_of(TCHAR('\\'));
		str = str.substr(0, pos);
		str += TCHAR('\\');
		str += (TCHAR*)TextPtr(src);
		windowinterface::showmessage(str.c_str());
		}
	}

void Player::pause()
	{
	}

void Player::stop()
	{
	}

// test
const char* Player::test_get_first_img()
	{
	smil::node *root = m_toplevel->get_root();
	tree_iterator<smil::node> it(root);
	while(!it.is_end())
		{
		tree_iterator<smil::node>::value_type v = *it;
		smil::node *n = (smil::node*)v.first;
		const std::string&  tag = n->get_tag();
		if(tag == "img")
			{
			const char *pstr = n->get_source();
			if(pstr != 0)
				{
				return pstr;
				}
			}
		it++;
		}
	return 0;
	}

} // namespace grins
