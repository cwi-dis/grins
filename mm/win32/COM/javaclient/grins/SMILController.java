
package grins;

public interface SMILController {
    void play();
    void stop();
    void pause();
       
    double getDuration();
    
    void setTime(double t);
    double getTime();
    
    void setSpeed(double v);
    double getSpeed();    
}

