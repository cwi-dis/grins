
package com.oratrix.client;


import com.oratrix.util.Hashtable;
import java.util.Vector;
import com.oratrix.xml.parse.*;

class Element {
    private final Hashtable attTable = new Hashtable();
	private String name = null;
	private Element child = null;												   
	private Element next = null;
	
	private char[] data = new char[8];
	private int offset = 0;

	private final class Attribute {
		String name = null;
		String value = null;	
	}

	Element(StartElementEvent ev){
		name = ev.getName();
		int n = ev.getAttributeCount();
		for(int i=0;i<n;i++)
			appendAttr(ev.getAttributeName(i),ev.getAttributeValue(i));
	}

	String getName() {return name;}

	void appendAttr(String name, String value){
		Attribute att = new Attribute();
		attTable.put(name, att);
		att.name = name;
		att.value = value;
	}

	String getAttribute(String name) {
		Attribute attr = (Attribute)attTable.get(name);
		if(attr!=null)
			return attr.value;
		return "";
	}

	void onCharDara(CharacterDataEvent ev) {
        int n = ev.getLength();
		int free = data.length - offset;
		if(free < n) grow(n-free);
        ev.copyChars(data, offset);
		offset += n;
	}

	void appendChild(Element child){
		if(getChild()==null) {
			setChild(child);
		}
		else {
			Element e = getChild();
			while(e.getNext()!=null)
				e = e.getNext();
			e.setNext(child);
		}
	}

    Vector getChildren() {
		Element e = child;
        if(e==null)return null;
        Vector v = new Vector(10,10);
        v.addElement(e);
		while(e.getNext()!=null){
			e = e.getNext();
			v.addElement(e);
		}
        return v;
    }
    
	String getDisplayText(){
		String str = new String(data, 0, offset);
		return str.trim();
    }
	
	// ignore attrs for now
	public String toString(){
        StringBuffer sb = new StringBuffer("<");
        sb.append("<");sb.append(name);sb.append(">");
        sb.append(getDisplayText());
        sb.append("</");sb.append(name);sb.append(">");
        return sb.toString();
	}
	
	Element getChild(){return child;}
	Element getNext(){return next;}
	void setChild(Element e){child=e;}
	void setNext(Element e){next=e;}
	static boolean isRoot(String name) {return name.equals("cml");}

	private final void grow(int n) {
		int length = data.length << 1;
		while(length < (data.length + n))
			length = length << 1;

		char[] tem = data;
		data = new char[length];
		if(offset>0)
		    System.arraycopy(tem, 0, data, 0, offset);
	}
}

