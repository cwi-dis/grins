
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#ifndef INC_TREE_NODE
#define INC_TREE_NODE

#ifndef INC_EXTRA_TYPES
#include "extra_types.h"
#endif

template <class Node>
class tree_iterator 
	{
	public:

	typedef Node* treeiter;

	typedef std::pair<treeiter, bool> value_type;
	
	tree_iterator()
		: currit(0), move(&tree_iterator::down) {}
	
	tree_iterator(treeiter it)
		: currit(it), move(&tree_iterator::down) {}

	tree_iterator(const tree_iterator& other)
		:	currit(other.currit), move(other.move) {}

	const tree_iterator& operator=(const tree_iterator& other){
		if(&other!=this){
			currit = other.currit; 
			move = other.move;
			}
		return *this;
		}

	friend bool operator==(const tree_iterator& lhs, const tree_iterator& rhs)
		{return lhs.currit==rhs.currit;}
	friend bool operator!=(const tree_iterator& lhs, const tree_iterator& rhs)
		{return lhs.currit!=rhs.currit;}

	void operator++() {if(move)(this->*move)();}
	void operator++(int) {if(move)(this->*move)();}

	value_type operator*() {return value_type(currit, (move==&tree_iterator::down));}
	
	operator int() {return move?1:0;}

	private:
	void down() {
		treeiter it = currit->down();
		if(it) currit = it;
		else move = &tree_iterator::next;
		}

	void next() {
		treeiter it = currit->next();
		if(it){
			currit = it;
			move = &tree_iterator::down;
			}
		else {
			move = &tree_iterator::up;
			(this->*move)();
			}
		}

	void up() {
		treeiter it = currit->up();
		if(it) {
			currit = it;
			move = &tree_iterator::next;
			}
		else {
			currit = it;
			move = 0;
			}
		}

	treeiter currit;
	void (tree_iterator::*move)();
	};

class tree_node
	{
	public:
	typedef const tree_node iterator_arg;
	typedef tree_iterator<iterator_arg> iterator;
	typedef const tree_iterator<iterator_arg> const_iterator;

	tree_node(const std::string& name, 
		std::map<std::string, std::string>* attrs = 0)
	:	m_name(name),
		m_parent(NULL),
		m_child(NULL),												   
		m_next(NULL),
		m_attrs(attrs)
		{
		m_beginit = iterator(this);
		}
	
	virtual ~tree_node()
		{
		tree_node *e = m_child;
		if(e)
			{
			tree_node *tmp = e;
			e = e->m_next;
			delete tmp;
			while(e)
				{
				tree_node *tmp = e;
				e = e->m_next;
				delete tmp;
				}
			}
		if(m_attrs != 0) delete m_attrs;
		}
	int appendCharData(const char *data, int len)
		{
		if(len) m_data.append(data, len);
		return m_data.size();
		}
	
	// tree builder method
	void appendChild(tree_node* child);
		
	const char *getName() const {return m_name.c_str();}
	const char *getData() const {return m_data.c_str();}

	int getDataSize() const {return m_data.size();}
	std::string get_raw_attribute(const char *name) const;
	const std::map<std::string, std::string>* getAttributes() const {return m_attrs;}
	void getChildren(std::list<const tree_node*>& l) const;
	void getChildren(std::list<const tree_node*>& l, const char *name) const;
	const tree_node *getFirstChild(const char *name) const;
	tree_node *getFirstChild(const char *name);
	std::string xmlrepr() const;

	iterator begin() {return m_beginit;}
	const_iterator begin() const {return (const_iterator)m_beginit;}

	iterator end() {return m_endit;}
	const_iterator end() const {return (const_iterator)m_endit;}

	const tree_node *down() const {return m_child;}
	const tree_node *up() const {return m_parent;}
	const tree_node *next() const {return m_next;}

	tree_node *down()  {return m_child;}
	tree_node *up()  {return m_parent;}
	tree_node *next()  {return m_next;}

	private:
	const tree_node *getChild() const {return m_child;}
	const tree_node *getNext() const {return m_next;}			
	void setChild(tree_node *e){m_child=e;}
	void setNext(tree_node *e){m_next=e;}
	
	std::string m_name;
	tree_node *m_child;												   
	tree_node *m_next;
	tree_node *m_parent;

	iterator m_beginit;
	iterator m_endit;

	std::string m_data;
	std::map<std::string, std::string>* m_attrs;
	};

inline void tree_node::appendChild(tree_node* child)
	{
	if(!m_child) 
		m_child = child;
	else
		{
		tree_node *e = m_child;
		while(e->m_next) e = e->m_next;
		e->m_next = child;
		}
	child->m_parent = this;
	child->m_endit = iterator(this);
	}

inline std::string tree_node::get_raw_attribute(const char *name) const 
	{
	if(m_attrs == 0) return "";
	std::map<std::string, std::string>::const_iterator it = m_attrs->find(name);
	if(it == m_attrs->end())
		return "";
	return (*it).second;
	}

inline void tree_node::getChildren(std::list<const tree_node*>& l) const
	{
	const tree_node *e = getChild();
	if(!e) return;
	l.push_back(e);
	while((e=e->getNext())) l.push_back(e);
	}

inline void tree_node::getChildren(std::list<const tree_node*>& l, const char *name) const
	{
	const tree_node *e = getChild();
	if(!e) return;
	if(e->m_name==name)l.push_back(e);
	while((e=e->getNext())) if(e->m_name==name) l.push_back(e);
	}

inline const tree_node *tree_node::getFirstChild(const char *name) const
	{
	const tree_node *e = getChild();
	if(!e) return NULL;
	if(e->m_name==name)return e;
	while((e=e->getNext())) if(e->m_name==name) return e;
	return NULL;
	}

inline tree_node *tree_node::getFirstChild(const char *name)
	{
	tree_node *e = m_child;
	if(!e) return NULL;
	if(e->m_name==name) return e;
	while((e=e->m_next)) if(e->m_name==name) return e;
	return NULL;
	}


inline std::string tree_node::xmlrepr() const {
	std::string s(m_name);
	if(m_attrs == 0) return s;
	std::map<std::string, std::string>::const_iterator it = m_attrs->begin();
	while(!(it == m_attrs->end())) {
		s += " ";
		s += (*it).first;
		s += "=\"";
		s += (*it).second;
		s += "\"";
		it++;
		}
	return s;
	}

#endif // INC_TREE_NODE
