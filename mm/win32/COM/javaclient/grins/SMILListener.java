
package grins;

public interface SMILListener {
    public final int STOPPED = 0;
    public final int PAUSING = 1;
    public final int PLAYING = 2;
    
    void setPos(double pos);
    void setState(int state);
    void newViewport(int index);
}