package com.oratrix.client;

import com.oratrix.xml.parse.*;

import java.net.*;

import java.io.IOException;
import java.util.Locale;
import java.util.Stack;
import java.util.Hashtable;

class XMLParser extends ApplicationAdapter {
	private EntityParser parser=null;
	private CMLMediator mediator=null;
 	private Stack stack=new Stack();
	private Hashtable cmdHandlers = new Hashtable();
	private String[] handlers = {
	    //"com.oratrix.client.ResponseCmdHandler",
	};
	
    XMLParser(CMLMediator mediator, Socket socket,URL url){
        this.mediator = mediator;
        
        OpenEntity entity=null;
        EntityManager entityManager=null;
        Application app=null;
        Locale locale=null;
		
		try {
            entity = EntityManagerImpl.openSocketInput(socket, url);
        }
        catch(IOException e){
            System.out.println("XMLParser.Error " + e + "\n");
        }
        entityManager = new EntityManagerImpl();
        locale = Locale.getDefault();
        
        try {
            parser = new EntityParser(entity, entityManager,
                this, locale, null);
        }
        catch(IOException e){
            System.out.println("XMLParser.Error " + e + "\n");
        }
		
		createCmdHandlers();
    }
    
    public void run(){
        try {
            parser.parseDocumentEntity();
        }
        catch(IOException e){
            System.out.println("Error " + e + "\n");
        }
        catch(ApplicationException e){
            System.out.println("Error " + e + "\n");
        }
    }
    
   public void startElement(StartElementEvent event){
		if(Element.isRoot(event.getName())) return;
		stack.push(new Element(event));
    }

    public void endElement(EndElementEvent event) { 
		if(Element.isRoot(event.getName())) return;
		
		Element top = (Element)stack.pop();
		if(stack.empty()){
			CmdHandler handler = (CmdHandler)cmdHandlers.get(top.getName());
			if(handler!=null)
				handler.execute(top);
		}
		else
			((Element)stack.peek()).appendChild(top);
    }

    public void characterData(CharacterDataEvent event) {
        // we may have an empty stack since root element
        // is not pushed
		if(stack.empty()) 
		    return;
		    
		Element top = (Element)stack.peek();
		top.onCharDara(event);
    }

	void createCmdHandlers(){
	    int nHandlers = handlers.length;
	    for(int i=0;i<nHandlers;i++){
	        try {
		        CmdHandler ch = (CmdHandler)Class.forName(handlers[i]).newInstance();
		        ch.setMediator(mediator);
		        cmdHandlers.put(ch.getName(), ch);
	        }
	        
	        // ClassNotFoundException, 
	        // InstantiationException
	        // IllegalAccessException
	        catch(Exception e) {mediator.errorMsg(""+e);}
	    }
   }
}
