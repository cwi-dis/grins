
package com.oratrix.client;

import java.net.*;

class XMLStreamReader extends Thread {
    private CMLMediator mediator;
    private Socket socket;
    private URL url;
    
    XMLStreamReader(CMLMediator mediator, Socket socket,URL url) {
        this.mediator = mediator;
        this.socket = socket;
        this.url = url;
    }
    
    public void run() {
        XMLParser parser = new XMLParser(mediator, socket, url);
        try {
            parser.run();
        }
        catch(Exception e){
            mediator.sessionEnd();
        }
        
    }
}
