
package grins;

import java.awt.*;
import java.util.Vector;

class GRiNSPlayer 
implements SMILDocument, SMILController, SMILRenderer
    {
    GRiNSPlayer(String filename)
        {
        open(filename);
        }
    
    public SMILController getController()
        {
        return this;
        }
    
    public SMILRenderer getRenderer() 
        {
        return this;
        }
    
    public void addListener(SMILListener listener){
        this.listener = listener;
    }
    
    public void removeListener(SMILListener listener){
        this.listener = null;
    }
    
    public int getViewportCount(){
        return ngetTopLayoutCount(hgrins);
    }
    
    public Dimension getViewportSize(int index)
        {
        return ngetTopLayoutDimensions(hgrins, index);
        }
        
    public String getViewportTitle(int index)
        {
        String title = ngetTopLayoutTitle(hgrins, index);
        if(title!=null) return title;
        return "";
        }
        
    public boolean isViewportOpen(int index)
        {
        return ngetTopLayoutState(hgrins, index)!=0;
        }
    
    public void setCanvas(int index, SMILCanvas c) throws Exception
        {
        if(c==null || !c.isDisplayable()) 
            throw new Exception("PlayerCanvas not displayable"); 
        canvas = c;
        c.setRenderer(this, index);
        if(hgrins!=0)
            {
            nsetTopLayoutWindow(hgrins, index, canvas);   
            nupdate(hgrins);
            }
        }
      
    public void open(String fn)
        {
        if(hgrins!=0) return;
        
        initializeThreadContext();
        hgrins = nconnect();
        if(hgrins!=0) 
            {
            nopen(hgrins, fn);
            if(canvas!=null && canvas.isDisplayable())
                {
                nsetTopLayoutWindow(hgrins, 0, canvas);   
                nupdate(hgrins);
                }
            //viewportSize = ngetTopLayoutDimensions(hgrins, 0);
            dur = ngetDuration(hgrins);
            monitor = new GRiNSPlayerMonitor(this, 100);
            monitor.start();
            }
        else
           uninitializeThreadContext(); 
        }
   
    
    public void close()
        {
        if(hgrins!=0) 
            {
            if(monitor!=null) monitor.interrupt();
            
            //nstop(hgrins);
            //nclose(hgrins);
            ndisconnect(hgrins);
            hgrins = 0;
            uninitializeThreadContext();
            }
         if(canvas!=null && canvas.isDisplayable())
            canvas.repaint();
        }
        
    public void update()
        {
        if(hgrins!=0) nupdate(hgrins);
        }
    
    public void mouseClicked(int index, int x, int y)
        {
        if(hgrins!=0) nmouseClicked(hgrins, index, x, y);
        }
    
    public boolean mouseMoved(int index, int x, int y)
        {
        if(hgrins!=0) return nmouseMoved(hgrins, index, x, y);
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
       
       
    // Friend methods
    int getCookie()
        {
        if(hgrins!=0) return ngetCookie(hgrins);
        return 0;
        }
        
    void updatePosition(double pos)
        {
        if(listener!=null) listener.setPos(pos);
        }
        
    void updateState(int state)
        {
        if(listener!=null) listener.setState(state);
        }
     
    void updateViewports(){
        if(listener!=null) listener.updateViewports();
        }
    
    private Dimension viewportSize;
    private double dur;
    private SMILListener listener;
    private GRiNSPlayerMonitor monitor;
	private Canvas canvas; 
	
	private int hgrins=0;
	
    private native void initializeThreadContext();
    private native void uninitializeThreadContext();
    
    private native int nconnect();
    private native void ndisconnect(int hgrins);
    private native void nopen(int hgrins, String str);
    private native void nclose(int hgrins);
    private native void nplay(int hgrins);
    private native void nstop(int hgrins);
    private native void npause(int hgrins);
    private native void nupdate(int hgrins);
    private native int ngetState(int hgrins);
    
    private native int ngetTopLayoutCount(int hgrins);
    private native void nsetTopLayoutWindow(int hgrins, int index, Component g);
    private native Dimension ngetTopLayoutDimensions(int hgrins, int index);
    private native String ngetTopLayoutTitle(int hgrins, int index);
    private native int ngetTopLayoutState(int hgrins, int index);
    private native void nmouseClicked(int hgrins, int index, int x, int y);
    private native boolean nmouseMoved(int hgrins, int index, int x, int y);
    
    private native double ngetDuration(int hgrins);
    private native void nsetTime(int hgrins, double t);
    private native double ngetTime(int hgrins);
    private native void nsetSpeed(int hgrins, double v);
    private native double ngetSpeed(int hgrins);
    private native int ngetCookie(int hgrins);
    static {
         System.loadLibrary("grinsp");
     }
    
}


    
    