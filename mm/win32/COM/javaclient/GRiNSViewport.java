
import java.awt.*;

public class GRiNSViewport extends Canvas {
	private int hgrins = 0;
    private boolean hasSource = false;
    private native int connect(Graphics g);
    private native void disconnect(int hgrins);
    private native void open(int hgrins, String str);
    private native void close(int hgrins);
    private native void play(int hgrins);
    private native void stop(int hgrins);
    private native void pause(int hgrins);
    private native void update(int hgrins);
    private native Dimension getSizeAdvice(int hgrins);
    
    static {
         System.loadLibrary("grinsp");
     }

    public boolean gpConnect() {
        if(hgrins==0)
		    hgrins = connect(getGraphics());
		return hgrins!=0;
		}

    public void gpDisconnect() {
		if(hgrins!=0) {
		    if(hasSource) close(hgrins);
		    hasSource = false;
		    disconnect(hgrins);
		    }
		hgrins = 0;
		invalidate();
		}

    public void gpOpen(String str) {
		if(hgrins!=0){
		    if(hasSource) close(hgrins);
		    open(hgrins, str);
		    update(hgrins);
		    hasSource = true;
		    }
		}

	public void gpClose() {
		if(hgrins!=0){
		    close(hgrins);
		    hasSource = false;
		    invalidate();
		    }
		}

	public void gpPlay() {
		if(hgrins!=0 && hasSource) play(hgrins);
		}

	public void gpStop() {
		if(hgrins!=0 && hasSource) stop(hgrins);
		}

	public void gpPause() {
		if(hgrins!=0 && hasSource) pause(hgrins);
		}

	public void gpUpdate() {
		if(hgrins!=0 && hasSource) update(hgrins);
		}
		
	public Dimension gpGetSizeAdvice() {
		if(hgrins!=0 && hasSource) return getSizeAdvice(hgrins);
		return null;
		}

	public void paint(Graphics g){
		if(hgrins!=0 && hasSource) update(hgrins);
		else super.paint(g);
	}
}
