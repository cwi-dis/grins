
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#ifndef INC_SMIL_NODE
#define INC_SMIL_NODE

#ifndef INC_TREE_NODE
#include "tree_node.h"
#endif

struct any;

namespace smil {

class node : public tree_node
	{
	public:
	node(const std::string& name, std::map<std::string, std::string>* attrs = 0);
	~node();

	any* get_attribute(const char *name);

	void set_parsed_attr(const char *name, any *p)
		{ m_attrs[name] = p;}
	
	private:
	std::map<std::string, any*> m_attrs;
	};

} // namespace smil

#endif // INC_SMIL_NODE
