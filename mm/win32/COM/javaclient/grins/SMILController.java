
package grins;

public interface SMILController {
    void play();
    void stop();
    void pause();
       
    void setTime(double t);
    double getTime();
    
    void setSpeed(double v);
    double getSpeed(); 
    
    void addListener(SMILListener listener);
    void removeListener(SMILListener listener);
    
}

