// CMIF_ADD
//
// kk@epsilon.com.gr
//
#include <objbase.h>
#include <strmif.h>
#include <control.h>
#include <evcode.h>
#include <uuids.h>
#pragma comment (lib,"strmiids.lib")

class GraphBuilder
	{
	public:
	GraphBuilder(IGraphBuilder* p):m_pI(p),m_pIMP(NULL){}
	virtual ~GraphBuilder(){Release();}
	void Release()
		{
		if(m_pIMP)m_pIMP->Release();m_pIMP=NULL;
		if(m_pI)m_pI->Release();m_pI=NULL;
		}
	IGraphBuilder* m_pI;
	IMediaPosition* m_pIMP;
	};

class GraphBuilderCreator
	{
	public:
	static PyObject *Create(PyObject *self, PyObject *args);
	};

