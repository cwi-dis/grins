
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#include "stdenv.h"

#include "smil_node.h"

#include "any.h"

namespace smil {


node::node(const std::string& name, std::map<std::string, std::string>* raw_attrs)
:	basic_tree_node<node>(name), m_raw_attrs(raw_attrs)
	{
	}

node::~node()
	{
	if(m_raw_attrs != 0) delete m_raw_attrs;

	std::map<std::string, any*>::iterator it;
	for(it=m_attrs.begin();it!= m_attrs.end();it++)
		delete (*it).second;

	node *e = down();
	if(e)
		{
		node *tmp = e;
		e = e->next();
		delete tmp;
		while(e)
			{
			node *tmp = e;
			e = e->next();
			delete tmp;
			}
		}
	}

any* node::get_attribute(const char *name)
	{
	std::map<std::string, any*>::iterator it;
	it = m_attrs.find(name);
	if(it != m_attrs.end())
		return (*it).second;
	return NULL;
	}

} // namespace smil
