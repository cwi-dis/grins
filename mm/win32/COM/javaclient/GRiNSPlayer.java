
import java.awt.*;
import java.awt.event.*;

public class GRiNSPlayer implements Renderer {
    public GRiNSPlayer() {
    }
    
    public Component getComponent() {
        if(component==null)
            component = new GPCanvas();
        return component;
    }
    
    public void setComponent(Component c) {
        component = c;
        if(c!=null && c instanceof Renderable) {
            ((Renderable)c).setRenderer(this);
        }
    }
    
    public void update() {
        if(hgrins!=0) nupdate(hgrins);
    }
    
    public void open(String fn) {
        if(component!=null && component.isDisplayable())
            hgrins = nconnect(component);
        else
            hgrins = nconnect();
        if(hgrins!=0) {
            nopen(hgrins, fn);
            nupdate(hgrins);
        }
    }
    
    public void close() {
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
    
    public void play() {
        if(hgrins!=0) nplay(hgrins);
    }
    public void stop() {
        if(hgrins!=0) nstop(hgrins);
    }
    public void pause() {
        if(hgrins!=0) npause(hgrins);
    }
    public Dimension getPreferredSize() {
        if(hgrins!=0) return ngetPreferredSize(hgrins);
        return null;
    }
     
    private class GPCanvas extends Canvas implements Renderable {
        public void setRenderer(Renderer renderer) {
            this.renderer = renderer;
        }
    
	    public void paint(Graphics g) {
		    if(renderer!=null) renderer.update();
		    else super.paint(g);
	    }
        private Renderer renderer;
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
    private native Dimension ngetPreferredSize(int hgrins);
    static {
         System.loadLibrary("grinsp");
     }
}
