package com.oratrix.client;

import java.io.*;
import java.net.*;

class GRiNSPlayerProxy implements CMLMediator {
 
    // GRiNS Player address
	private String server;
	private int serverport;
    
    // do we have a socket connection?
	private boolean connected=false;

    // socket stream variables
	private Socket socket;
	private OutputStream outputStream;
	
	// stream reader
	private XMLStreamReader reader;

    GRiNSPlayerProxy(String server, int serverport){
        this.server = server;
        this.serverport = serverport;
        
    }
    
	private void message(String str) {
	    System.out.println(str);
	}
	
	private void errormessage(String str) {
	    message(str);
	}
    
	public void connect() {
		message("Connecting to host "+ server + ":" + serverport);	
		if(!connected)
		    connected = doConnect();
		URL docBase = null;
		try {
		    docBase = new URL("http://www.oratrix.com");
		}
		catch(Exception e){errormessage("Exception" + e);}
		if(connected) { 
		    reader = new XMLStreamReader(this, socket, docBase);
			reader.start();
		}
	}
    
	public void disconnect() {
	    if(reader!=null)
	        reader.stop();
	    try {
	        if(socket!=null) {
	            Socket temp = socket;
	            socket = null;
	            outputStream = null;
	            temp.close();
	        }
	    }
	    catch(IOException e) {
	        errormessage("IOException" + e);
	    }
	    reader = null;
	    connected = false;
	}
   
   public void open(String src){
        sendcmd("<open src=\"" + src + "\"/>\n");   
   }
   
   public void play(){
        sendcmd("<play/>\n");  
   }
   
   public void stop(){
        sendcmd("<stop/>\n");   
   }
   
   public void pause(){
        sendcmd("<pause/>\n");   
   }
   
   
	private boolean doConnect() {
		try {
			socket = new Socket(server, serverport);
		}
		catch(Throwable e){
			errormessage("Failed to connect.");
			socket = null;
			return false;
		}
		try {
		    outputStream = socket.getOutputStream();
		}
		catch(Throwable e){
		    outputStream = null;
			errormessage("Failed to connect.");
		}
		if(outputStream == null){
		    stop();
		    return false;
		}
		message("Connected.");
		return true;
	}
	
	
    // Implement CMLMediator interface
    
    // sender part
	public void sendcmd(String str) {
	    if(!connected || outputStream==null || str==null || str.length()==0) return;
	    byte buf[] = EuLocal.getBytes(str);
		try {
			outputStream.write(buf, 0, buf.length);
		}
		catch(Exception e){errormessage("Error " + e);}
	}
      
    // receiver part
    public void response(String cmdid, String msg){
    }
    
    public void sessionEnd(){
        if(socket!=null){
            disconnect();
            message("Disconnected.");
        }        
    }
    
    public void errorMsg(String msg){
        errormessage(msg);
    }
	

   // helpers
   private String xmlquote(String str) {
        StringBuffer sb = new StringBuffer();
        for(int i=0;i<str.length();i++) {
            char ch = str.charAt(i);
            if(ch=='<') sb.append("&lt;");
            else if(ch=='>') sb.append("&gt;");
            else if(ch=='&') sb.append("&amp;");
            else sb.append(ch);
        }
        return sb.toString();
    }
	
}

    