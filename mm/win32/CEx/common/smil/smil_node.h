
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

class node : public basic_tree_node<node>
	{
	public:
	node(const std::string& name, std::map<std::string, std::string>* raw_attrs = 0);
	~node();

	bool has_raw_attribute(const char *name);
	const char* get_raw_attribute(const char *name);
	any* get_attribute(const char *name);

	const char* get_source() { return get_raw_attribute("src");}

	void set_parsed_attr(const char *name, any *p)
		{ m_attrs[name] = p;}
	
	typedef std::map<std::string, std::string> raw_attrs_t;
	typedef std::map<std::string, any*> attrs_t;

	bool has_row_attrs() { return m_raw_attrs != 0;}
	raw_attrs_t& get_raw_attrs() {return *m_raw_attrs;}
	attrs_t& get_attrs() {return m_attrs;}

	private:
	std::map<std::string, std::string> *m_raw_attrs;
	std::map<std::string, any*> m_attrs;
	};

inline bool node::has_raw_attribute(const char *name)
	{
	if(m_raw_attrs == 0) return false;
	std::map<std::string, std::string>::iterator it = m_raw_attrs->find(name);
	if(it != m_raw_attrs->end())
		return true;
	return false;
	}

inline const char* node::get_raw_attribute(const char *name)
	{
	if(m_raw_attrs == 0) return 0;
	std::map<std::string, std::string>::iterator it = m_raw_attrs->find(name);
	if(it != m_raw_attrs->end())
		return (*it).second.c_str();
	return 0;
	}

} // namespace smil

#endif // INC_SMIL_NODE
