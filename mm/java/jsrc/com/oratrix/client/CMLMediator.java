
package com.oratrix.client;

interface CMLMediator {
    // receiver interface
    void response(String cmdid, String msg);
    void sessionEnd();
    void errorMsg(String msg);
    
    // sender interface
    void sendcmd(String str);
}