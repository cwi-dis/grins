
package grins;

/**
*  SMILController specifies the interface for controlling the playback
*  of SMIL documents. SMILControllers are produced by SMILDocuments
*  using the method getController(); see interface SMILDocument
*/   
public interface SMILController {
    /**
    *  Start playback, of the SMIL document controlled
    *  by this SMILController.
    */    
    void play();
    
    
    /**
    *  Stop playback, of the SMIL document controlled
    *  by this SMILController.
    */    
    void stop();
    
    
    /**
    *  Pause playback, of the SMIL document controlled
    *  by this SMILController.
    */    
    void pause();
     
    /**
    *  Seek to time t in seconds within the SMIL document controlled
    *  by this SMILController.
    */       
    void setTime(double t);
    
    /**
    *  Get current position in seconds of the SMIL document controlled
    *  by this SMILController.
    */       
    double getTime();
    
    /**
    *  Set playback speed for the SMIL document controlled
    *  by this SMILController.
    *  (null implementation for now)
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
    */       
    void addListener(SMILListener listener);
    
    /**
    *  Remove playback event listener for the SMIL document controlled
    *  by this SMILController.
    */       
    void removeListener(SMILListener listener);
    
}

