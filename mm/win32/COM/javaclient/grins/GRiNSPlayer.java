
package grins;

import java.awt.*;
import java.util.Vector;

class GRiNSPlayer 
implements SMILDocument, SMILController, SMILRenderer
    {
    GRiNSPlayer(SMILListener listener)
        {
        this.listener = listener;
        }
    
    public SMILController getController() 
        {
        return this;
        }
    
    public SMILRenderer getRenderer() 
        {
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
      
    public void open(String fn)
        {
        if(hgrins!=0) return;
        
        listener.setWaiting();
        initializeThreadContext();
        hgrins = nconnect();
        if(hgrins!=0) 
            {
            nopen(hgrins, fn);
            if(canvas!=null && canvas.isDisplayable())
                {
                nsetWindow(hgrins, canvas);   
                nupdate(hgrins);
                }
            viewportSize = ngetPreferredSize(hgrins);
            listener.setReady();
            listener.opened();
            dur = ngetDuration(hgrins);
            listener.setDur(dur);
            monitor = new GRiNSPlayerMonitor(ngetCookie(hgrins), 100);
            monitor.addListener(listener);
            monitor.start();
            }
        else
           uninitializeThreadContext(); 
        }
   
    public void close()
        {
        if(hgrins!=0) 
            {
            monitor.interrupt();
            nstop(hgrins);
            nclose(hgrins);
            ndisconnect(hgrins);
            hgrins = 0;
            uninitializeThreadContext();
            try {Thread.sleep(100);}
            catch(InterruptedException e){}
            }
         if(canvas!=null && canvas.isDisplayable())
            canvas.repaint();
        if(listener!=null) listener.closed();
        }
        
    public void update()
        {
        if(hgrins!=0) nupdate(hgrins);
        }
    
    public void mouseClicked(int x, int y)
        {
        if(hgrins!=0) nmouseClicked(hgrins, x, y);
        }
    
    public boolean mouseMoved(int x, int y)
        {
        if(hgrins!=0) nmouseMoved(hgrins, x, y);
        return false;
        }
        
    public void play()
        {
        if(hgrins!=0) nplay(hgrins);
        }    
        
    public void stop()
        {
        if(hgrins!=0) nstop(hgrins);
        }  
        
    public void pause()
        {
        if(hgrins!=0) npause(hgrins);
        } 
               
    public int getState()
    {
        if(hgrins!=0) return ngetState(hgrins);
        return -1;
    }
             
    public double getDuration() {return dur;}
    
    public void setTime(double t)
        {
        if(hgrins!=0) nsetTime(hgrins, t);   
        }
    
    public double getTime() 
        {
        if(hgrins!=0) return ngetTime(hgrins);
        return 0;
        }
    
    public void setSpeed(double v) {}
    
    public double getSpeed() {return 1.0;}
       
    
    
    private Dimension viewportSize;
    private double dur;
    private SMILListener listener;
    private GRiNSPlayerMonitor monitor;
	private Canvas canvas; 
	
	private int hgrins=0;
	
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
    private native int ngetCookie(int hgrins);
    static {
         System.loadLibrary("grinsp");
     }
    
}


    
    