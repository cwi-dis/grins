
package com.oratrix.client;

interface CmdHandler {
    public void execute(Element e);
    public String getName();
    public void setMediator(CMLMediator mediator);
    public void toLog();
}
