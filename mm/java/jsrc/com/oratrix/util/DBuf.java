
package com.oratrix.util;

import java.util.Vector;

public class DBuf {
	private int readoff;  
	private int writeoff;
	
	public static final int PAGESIZE = 256;
	private Object[] page = new Object[PAGESIZE];
	
	public static final int NUM_PAGES = 4;
	private Vector pages = new Vector(NUM_PAGES);
	private Vector freelist = new Vector(NUM_PAGES);
	
	public DBuf(){
        readoff = 0;
        pages.addElement(allocpage());
	    writeoff = 0;
	}
	
    private void freepage(Object[] page) {
	    freelist.addElement(page);
	    }
	    
	private Object[] allocpage() {
	    Object[] page = null;
	    if(freelist.size()>0) {
		    page = (Object[])freelist.firstElement();
		    freelist.removeElementAt(0);
		}
	    else {
	        page = new Object[PAGESIZE];
	    }
	    return page;
	}
	
    public void put(Object obj) {
        if(pages.size()==NUM_PAGES) 
            removepage();
        
	    // start from back page
	    Object[] back = (Object[])pages.lastElement();

	    // how much space do we have on this page?
	    int available = PAGESIZE - writeoff;
	    if(available>0) {
	        back[writeoff++] = obj;
	    }
        else {
            pages.addElement(allocpage());
            writeoff = 0;
            put(obj);
        }
	}
	
	public int remove(int num){
	    // start reading from front page
	    Object[] front = (Object[])pages.firstElement();

	    // how much we can remove from this page?
	    int available;
	    if(pages.size()==1)
	        available = writeoff-readoff;
	    else
	        available = PAGESIZE-readoff;
	    // but we should not exit n
	    int chunklen = Math.min(available,num);
	    
	    // discard them by updating indicators
	    // and update indicators
	    readoff += chunklen;
	    int mumrem = num - chunklen;
	    
	    // can we free this page?
	    if(pages.size()==1){
		    // no we can not free it, but reuse it
		    if(writeoff==readoff)
			    writeoff=readoff=0;
	    }  
	    else {
		    // we have more pages, we can discard this
		    if(readoff==PAGESIZE) {
			    // free this page
			    pages.removeElementAt(0);
			    readoff = 0;
			 }
		}
	    // do we have more space and data?
	    // if yes remove it
	    if(pages.size()==1)
	        available = writeoff-readoff;
	    else
	        available = PAGESIZE-readoff;
	    if(mumrem>0 && available>0)
		    return chunklen + remove(mumrem);

	    return chunklen;
	}
	
    public void removepage() {
	    if(pages.size()==1)
		    writeoff=readoff=0;
	    else {
	        freepage((Object[])pages.firstElement());
	        pages.removeElementAt(0);
			readoff = 0;
		}
	}
	
	public int size(){
	    int n = 0;
	    
	    // first
	    if(pages.size()==1)
	        n = writeoff-readoff;
	    else
	        n = PAGESIZE-readoff;
	    
	    // rest except last
	    for(int i=1;i<pages.size()-1;i++){
	        n += PAGESIZE;
	    }
	    
	    // last
	    if(pages.size()>1){
	        n += writeoff;
	    }
	    return n;
	}
	
	private int readPage(Object[] page, int from, int to, Object[] data, int offset){
	    for(int i=from;i<to;i++) data[offset++]=page[i];
	    return offset;
	}
	
	public Object[] getElements(){
	    int n = size();
	    Object[] data = new Object[n];
	    int offset = 0;
	    // first
	    if(pages.size()==1)
	        offset = readPage((Object[])pages.firstElement(),readoff,writeoff,data,offset);
	    else
	        offset = readPage((Object[])pages.firstElement(),readoff,PAGESIZE,data,offset);
	    
	    // rest except last
	    for(int i=1;i<pages.size()-1;i++)
	        offset = readPage((Object[])pages.elementAt(i),0,PAGESIZE,data,offset);
	    
	    // last
	    if(pages.size()>1)
	        offset = readPage((Object[])pages.lastElement(),0,writeoff,data,offset);
	        
	    return data;
	}
}