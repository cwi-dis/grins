
import java.awt.Canvas;

interface SMILPlayer {
    Canvas getCanvas();
    void setCanvas(Canvas c);
    
    void open(String fn);
    void close();
    
    void play();
    void stop();
    void pause();
       
    double getDuration();
    
    void setTime(double t);
    double getTime();
    
    void setSpeed(double v);
    double getSpeed();
    
    void mouseClicked(int x, int y);
    boolean mouseMoved(int x, int y);
    
    void update();
}