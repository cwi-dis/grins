
package grins;

/**
*  The interface for controlling playback of SMIL documents.
*  SMILControllers are produced by SMILDocuments
*  using the method getController(); see interface SMILDocument
*/   
public interface SMILController {
    /**
    *  Start playback from current position, of the SMIL document controlled
    *  by this SMILController.
    */    
    void play();
    
    
    /**
    *  Pause playback, of the SMIL document controlled
    *  by this SMILController.
    */    
    void pause();
    
    
    /**
    *  Stop playback, of the SMIL document controlled
    *  by this SMILController and reset.
    */    
    void stop();
    
          
    /**
    *  Seek to time t in seconds within the SMIL document controlled
    *  by this SMILController.
    *
    * @param  t  time in seconds to seek to.
    */       
    void setTime(double t);
    
    /**
    *  Get current position in seconds of the SMIL document controlled
    *  by this SMILController.
    *  A client receives playback notifications through the SMILListener interface.
    */       
    double getTime();
    
    /**
    *  Set playback speed for the SMIL document controlled
    *  by this SMILController.
    *  (null implementation for now)
    *
    * @param  v   new speed.
    *
    */       
    void setSpeed(double v);
    
    /**
    *  Get playback speed for the SMIL document controlled
    *  by this SMILController.
    *  (returns always 1.0 for now)
    */       
    double getSpeed(); 
    
    /**
    *  Add a playback event listener for the SMIL document controlled
    *  by this SMILController.
    *
    * @param  listener the object that will receive playback notifications.
    */       
    void addListener(SMILListener listener);
    
    /**
    *  Remove playback event listener for the SMIL document controlled
    *  by this SMILController.
    */       
    void removeListener(SMILListener listener);
    
}

