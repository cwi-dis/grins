
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#include "stdenv.h"

#include "smil_parser.h"

#include "tree_node.h"

namespace smil {

parser::parser()
	{
	set_handler("smil", &parser::start_smil, &parser::end_smil);
	set_handler("head", &parser::start_head, &parser::end_head);
	set_handler("meta", &parser::start_meta, &parser::end_meta);
	// ...

	m_rootnode = new tree_node();
	m_curnode = m_rootnode;
	}

parser::~parser()
	{
	delete m_rootnode;
	}

void parser::start_smil(raw_attr_list_t *pattrs)
	{
	new_node("smil", pattrs);
	}

void parser::end_smil()
	{
	end_node();
	}

void parser::start_head(raw_attr_list_t *pattrs)
	{
	new_node("head", pattrs);
	}

void parser::end_head()
	{
	end_node();
	}

void parser::start_meta(raw_attr_list_t *pattrs)
	{
	new_node("meta", pattrs);
	}

void parser::end_meta()
	{
	end_node();
	}

// ...


//
void parser::unknown_starttag(const char *tag, raw_attr_list_t *pattrs)
	{
	new_node(tag, pattrs);
	}

void parser::unknown_endtag()
	{
	end_node();
	}

//
void parser::new_node(const char *name, raw_attr_list_t *pattrs)
	{
	tree_node *p = new tree_node("smil", pattrs);
	m_curnode->appendChild(p);
	m_curnode = p;
	}

void parser::end_node()
	{
	m_curnode = m_curnode->up();
	}

} // namespace smil
