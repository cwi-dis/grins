
import java.awt.*;

public class GRiNSViewport extends Canvas {
	private int hgrins;
    private native int connect(Graphics g);
    private native void disconnect(int hgrins);
    private native void open(int hgrins, String str);
    private native void close(int hgrins);
    private native void play(int hgrins);
    private native void stop(int hgrins);
    private native void pause(int hgrins);
    private native void update(int hgrins);
    static {
         System.loadLibrary("grinsp");
     }

    public boolean connect() {
		hgrins = connect(getGraphics());
		return hgrins!=0;
		}

    public void disconnect() {
		if(hgrins!=0) disconnect(hgrins);
		hgrins = 0;
		}

    public void open(String str) {
		if(hgrins!=0) open(hgrins, str);
		}

	public void close() {
		if(hgrins!=0) close(hgrins);
		}

	public void play() {
		if(hgrins!=0) play(hgrins);
		}

	public void stop() {
		if(hgrins!=0) stop(hgrins);
		}

	public void pause() {
		if(hgrins!=0) pause(hgrins);
		}

	public void update() {
		if(hgrins!=0) update(hgrins);
		}

	public void paint(Graphics g){
		if(hgrins!=0) update(hgrins);
	}
}
