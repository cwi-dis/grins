
package grins;

import java.awt.*;
import java.util.Vector;

class GRiNSPlayer 
implements SMILDocument, SMILController, SMILRenderer, Runnable
    {
    GRiNSPlayer(SMILListener listener){
        this.listener = listener;
        }
    
    public SMILController getController() {
        return this;
    }
    
    public SMILRenderer getRenderer() {
        return this;
    }
    
    public Dimension getViewportSize() throws Exception
    {
        if(viewportSize==null || viewportSize.width==0)
            throw new Exception("Not ready"); 
        return viewportSize;
    }
    
    public void setCanvas(PlayerCanvas c) throws Exception
        {
        if(c==null || !c.isDisplayable()) 
            throw new Exception("PlayerCanvas not displayable"); 
        canvas = c;
        c.setRenderer(this);
        if(hgrins!=0)
            {
            nsetWindow(hgrins, canvas);   
            nupdate(hgrins);
            }
        }
            
    public void update() {push(new Cmd("update"));}
    
    public void mouseClicked(int x, int y){push(new Cmd("mouseClicked", x, y));}
    
    public boolean mouseMoved(int x, int y){
        push(new Cmd("mouseMoved", x, y));
        return ishot;
        }
        
    public void open(String fn) {   
        push(new Cmd("open", fn));
        if(isRunning) return;
        new Thread(this).start();
        }
        
    public void close(){push(new Cmd("close"));}
    
    public void play(){push(new Cmd("play"));}
    
    public void stop(){push(new Cmd("stop"));}
    
    public void pause(){push(new Cmd("pause"));}
       
    public int getState() throws GRiNSInterfaceException
    {
        if(hgrins!=0) return ngetState(hgrins);
        return -1;
    }
             
    public double getDuration() {return dur;}
    
    public void setTime(double t) {push(new Cmd("setTime", t));}
    
    public double getTime() {return pos;}
    
    public void setSpeed(double v) {}
    
    public double getSpeed() {return 1.0;}
       
    class Cmd {
        Cmd(String fname){
            this.fname = fname;
        }
        Cmd(String fname, String strarg){
            this.fname = fname;
            this.strarg = strarg;
        }
    
        Cmd(String fname, int xarg, int yarg){
            this.fname = fname;
            this.xarg = xarg;
            this.yarg = yarg;
        }
        Cmd(String fname, double darg){
            this.fname = fname;
            this.darg = darg;
        }
    
        String fname;
        int xarg, yarg;
        String strarg;
        double darg;
    }
    
    public void run(){
        initializeThreadContext();
        isRunning = true;
        try {
            while(!Thread.currentThread().interrupted()){
                Cmd cmd = peek();
                if(cmd==null){
                    if(updatepos)
                        {
                        pos = ngetTime(hgrins);
                        listener.setPos(pos);
                        }
                    Thread.sleep(interval);
                    continue;
                }
                try {
                if(cmd.fname.equals("open")){
                    listener.setWaiting();
                    hopen(cmd.strarg);
                    push(new Cmd("getPreferredSize"));
                    }
                else if(cmd.fname.equals("close"))
                    {hclose();listener.closed(); updatepos = false;break;}
                else if(cmd.fname.equals("play"))
                    {
                    nplay(hgrins);
                    updatepos = true;
                    }
                else if(cmd.fname.equals("stop"))
                    {
                    nstop(hgrins);
                    updatepos = false;
                    }
                else if(cmd.fname.equals("pause"))
                    {
                    npause(hgrins);
                    updatepos = false;
                    }
                else if(cmd.fname.equals("update"))
                    nupdate(hgrins);
                else if(cmd.fname.equals("setTime"))
                    nsetTime(hgrins, cmd.darg);
                else if(cmd.fname.equals("mouseClicked"))
                    nmouseClicked(hgrins, cmd.xarg, cmd.yarg);
                else if(cmd.fname.equals("mouseMoved"))
                    ishot = nmouseMoved(hgrins, cmd.xarg, cmd.yarg);
                else if(cmd.fname.equals("getPreferredSize")){
                     viewportSize = ngetPreferredSize(hgrins);
                     if(viewportSize.width!=0){
                        listener.opened();
                        dur = ngetDuration(hgrins);
                        listener.setDur(dur);
                        listener.setReady();
                        }
                     else 
                        {
                        push(new Cmd("getPreferredSize"));
                        Thread.sleep(interval);
                        }
                    }
                }
                catch(GRiNSInterfaceException e){System.out.println(""+e);}
                }
            }
        catch(InterruptedException e){System.out.println(""+e);}
        isRunning = false;
        uninitializeThreadContext();
    }

    private synchronized void push(Cmd cmd){
        cmds.add(cmd);
        notifyAll();
    }
    
    private synchronized Cmd peek() {
	    int	len = cmds.size();
	    if (len == 0)
	        return null;
	    Cmd cmd = (Cmd)cmds.elementAt(0);
	    cmds.removeElementAt(0);
	    return cmd;
     }
    
    private void hopen(String fn) throws GRiNSInterfaceException
    {
        hgrins = nconnect();
        if(hgrins!=0) {
            nopen(hgrins, fn);
            if(canvas!=null && canvas.isDisplayable())
                {
                nsetWindow(hgrins, canvas);   
                nupdate(hgrins);
                }
        }
    }
    
    private void hclose() throws GRiNSInterfaceException
        {
        if(hgrins!=0) {
            nstop(hgrins);
            nclose(hgrins);
            ndisconnect(hgrins);
            hgrins = 0;
            }
         try {
            Thread.sleep(500);
         }
         catch(InterruptedException e){}
         if(canvas!=null && canvas.isDisplayable())
            canvas.repaint();
    }
    
    private boolean ishot = false;
    private boolean isRunning = false;
    private Vector cmds = new Vector(10);
    private int interval = 50;
    private Dimension viewportSize;
    private double dur;
    private double pos;
    private boolean updatepos = false;
    private SMILListener listener;
    
	private Canvas canvas; 
	
	private int hgrins;
	
    private native void initializeThreadContext();
    private native void uninitializeThreadContext();
    
    private native int nconnect();
    private native void nsetWindow(int hgrins, Component g);
    private native void ndisconnect(int hgrins);
    private native void nopen(int hgrins, String str);
    private native void nclose(int hgrins);
    private native void nplay(int hgrins);
    private native void nstop(int hgrins);
    private native void npause(int hgrins);
    private native void nupdate(int hgrins);
    private native int ngetState(int hgrins);
    private native Dimension ngetPreferredSize(int hgrins);
    private native double ngetDuration(int hgrins);
    private native void nsetTime(int hgrins, double t);
    private native double ngetTime(int hgrins);
    private native void nsetSpeed(int hgrins, double v);
    private native double ngetSpeed(int hgrins);
    private native void nmouseClicked(int hgrins, int x, int y);
    private native boolean nmouseMoved(int hgrins, int x, int y);
    static {
         System.loadLibrary("grinsp");
     }
    
}

