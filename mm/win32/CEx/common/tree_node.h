
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
	typedef std::pair<Node*, bool> value_type;
	
	tree_iterator()
	: m_root(0), m_cur(0), move(0) {}
		
	tree_iterator(Node *p)
		: m_root(p), m_cur(p), move(&tree_iterator::down) {}

	tree_iterator(const tree_iterator& other)
		:	m_root(other.m_root), m_cur(other.m_cur), move(other.move) {}

	const tree_iterator& operator=(const tree_iterator& other){
		if(&other!=this){
			m_root = other.m_root; 
			m_cur = other.m_cur; 
			move = other.move;
			}
		return *this;
		}

	friend bool operator==(const tree_iterator& lhs, const tree_iterator& rhs)
		{return lhs.m_root==rhs.m_root && lhs.m_cur==rhs.m_cur && move == other.move;}

	friend bool operator!=(const tree_iterator& lhs, const tree_iterator& rhs)
		{return lhs.m_root!=rhs.m_root || lhs.m_cur!=rhs.m_cur || move != other.move;}

	void operator++() {if(move)(this->*move)();}
	void operator++(int) {if(move)(this->*move)();}

	value_type operator*() { return value_type(m_cur, (move==&tree_iterator::down));}
	bool is_end() const { return move==0;}

	private:
	void down() {
		Node *p = m_cur->down();
		if(p) m_cur = p;
		else move = &tree_iterator::next;
		}

	void next() {
		if(m_cur == m_root) {move=0; return;}

		Node * it = m_cur->next();
		if(it){
			m_cur = it;
			move = &tree_iterator::down;
			}
		else {
			move = &tree_iterator::up;
			(this->*move)();
			}
		}

	void up() {
		if(m_cur == m_root) {move=0; return;}

		Node * it = m_cur->up();
		if(it) {
			m_cur = it;
			move = &tree_iterator::next;
			}
		else {
			m_cur = it;
			move = 0;
			}
		}

	Node *m_root;
	Node *m_cur;
	void (tree_iterator::*move)();
	};

template <class Node>
class tree_node
	{
	public:
	tree_node() 
	: m_parent(0), m_next(0), m_child(0) {}

	const Node *down() const { return m_child;}
	const Node *up() const { return m_parent;}
	const Node *next() const { return m_next;}

	Node *down()  { return m_child;}
	Node *up()  { return m_parent;}
	Node *next()  { return m_next;}

	void append_child(Node* child)
		{
		if(m_child == 0) 
			m_child = child;
		else
			{
			Node *e = m_child;
			while(e->m_next) e = e->m_next;
			e->m_next = child;
			}
		child->m_parent = (Node*)this;
		}

	void get_children(std::list<Node*>& l) const 
		{
		Node *e = down();
		if(!e) return;
		l.push_back(e);
		while((e=e->next())) l.push_back(e);
		}

	Node *m_parent;
	Node *m_next;
	Node *m_child;												   
	};

// tree_node with tag and data
template <class Node>
class basic_tree_node : public tree_node<Node>
	{
	public:
	basic_tree_node(const std::basic_string<char>& tag)
	:	m_tag(tag) {}
	
	void append_data(const char *data, int len)
		{ if(len>0) m_data.append(data, len);}

	const std::basic_string<char>& get_tag() const {return m_tag;}
	const std::basic_string<char>& get_data() const {return m_data;}

	Node *get_first_child(const char *name)
		{
		Node *e = down();
		if(!e) return 0;
		if(e->m_name == name) return e;
		while((e=e->next())) if(e->m_name == name) return e;
		return 0;
		}

	void get_children(std::list<Node*>& l, const char *name) const
		{
		Node *e = down();
		if(!e) return;
		if(e->m_name == name) l.push_back(e);
		while((e=e->next())) if(e->m_name == name) l.push_back(e);
		}

	private:
	std::basic_string<char> m_tag;
	std::basic_string<char> m_data;
	};


#endif // INC_TREE_NODE
