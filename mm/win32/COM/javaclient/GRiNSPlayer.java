
import java.awt.*;
import java.awt.event.*;

public class GRiNSPlayer implements Renderer {
    public GRiNSPlayer() {
    }
    
    public Component getComponent() 
    {
        if(component==null)
            component = new PlayerCanvas();
        return component;
    }
    
    public void setComponent(Component c) 
    {
        component = c;
        if(c!=null && c instanceof PlayerCanvas) {
            ((Renderable)c).setRenderer(this);
        }
    }
    
    public void update()
    {
        if(hgrins!=0) nupdate(hgrins);
    }
    
    public void mouseClicked(int x, int y)
    {
        if(hgrins!=0) nmouseClicked(hgrins, x, y);
        System.out.println("mouseClicked "+x+", "+y);
    }
    public boolean mouseMoved(int x, int y)
    {
        if(hgrins!=0) return nmouseMoved(hgrins, x, y);
        return false;
    }
    
    public void open(String fn) throws GRiNSInterfaceException
    {
        if(component!=null && component.isDisplayable())
            hgrins = nconnect(component);
        else
            hgrins = nconnect();
        if(hgrins!=0) {
            nopen(hgrins, fn);
            nupdate(hgrins);
        }
    }
    
    public void close() throws GRiNSInterfaceException
        {
        if(hgrins!=0) {
            nclose(hgrins);
            ndisconnect(hgrins);
            hgrins = 0;
            }
         try {
            Thread.sleep(500);
         }
         catch(InterruptedException e){}
         if(component!=null && component.isDisplayable())
            component.repaint();
    }
    
    public void play() throws GRiNSInterfaceException
    {
        if(hgrins!=0) nplay(hgrins);
    }
    public void stop() throws GRiNSInterfaceException
    {
        if(hgrins!=0) nstop(hgrins);
    }
    public void pause() throws GRiNSInterfaceException
    {
        if(hgrins!=0) npause(hgrins);
    }
    
    public int getState() throws GRiNSInterfaceException
    {
        if(hgrins!=0) return ngetState(hgrins);
        return -1;
    }
        
    public Dimension getPreferredSize() throws GRiNSInterfaceException
    {
        if(hgrins!=0) return ngetPreferredSize(hgrins);
        return null;
    }
     
    public double getDuration() throws GRiNSInterfaceException
    {
        if(hgrins!=0) return ngetDuration(hgrins);
        return -1;
    }
    public void setTime(double t) throws GRiNSInterfaceException
    {
        if(hgrins!=0) nsetTime(hgrins, t);
    }
    
    public double getTime() throws GRiNSInterfaceException
    {
        if(hgrins!=0) return ngetTime(hgrins);
        return -1.0;
    }
     
    public void setSpeed(double v) throws GRiNSInterfaceException
    {
        if(hgrins!=0) nsetSpeed(hgrins, v);
    }
    
    public double getSpeed() throws GRiNSInterfaceException
    {
        if(hgrins!=0) return ngetSpeed(hgrins);
        return 1.0;
    }
                
	private int hgrins;
	private Component component; 
    private native int nconnect();
    private native int nconnect(Component g);
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
