
import java.awt.*;

public class GRiNSCanvas extends Canvas {
    public native void paint(Graphics g);
    public native void connect(Graphics g);
    public native void disconnect();
    public native void open(String str);
    public native void close();
    public native void play();
    public native void stop();
    public native void pause();
    static {
         System.loadLibrary("grinsp");
     }
}
