
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#include "stdenv.h"

#include "smil_node.h"

#include "any.h"

namespace smil {


node::node(const std::string& name, std::map<std::string, std::string>* attrs)
:	tree_node(name, attrs)
	{
	}

node::~node()
	{
	std::map<std::string, any*>::iterator it;
	for(it=m_attrs.begin();it!= m_attrs.end();it++)
		delete (*it).second;
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
