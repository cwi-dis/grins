
package grins;

import java.awt.Canvas;
import java.awt.Dimension;

/**
*  The interface for managing SMIL documents.
*  SMILDocuments are produced by a GRiNSToolkit
*  using the factory method createDocument(String filenameOrURLString)
*  After using a SMILDocument you should <em>always</em> call close() 
*  to dispose used resources. 
*/   
public interface SMILDocument {
    /**
    *  To playback a SMIL document you need 
    *  an object implementing the interface of a SMILController.
    *  Use this method to acquire such an object
    */  
    SMILController getController();
    
    /**
    *   Returns an object implementing the interface of a SMILRenderer.
    *   A SMILRenderer is used to associate a SMILCanavas with a document viewport.
    */
    SMILRenderer getRenderer();
    
    /**
    *   Get the number of top level windows of this SMIL document.
    *   Top level windows are asigned an index.
    */
    int getViewportCount();
    
    /**
    *   Get the top level window size associated with the zero based index
    */
    Dimension getViewportSize(int index);
    
    /**
    *   Get the top level window title associated with the zero based index
    */
    String getViewportTitle(int index);
    
    /**
    *   Returns true if the the top level window associated with the zero based index is open.
    */
    boolean isViewportOpen(int index);
    
    /**
    *  Returns the duration of the document (indefinite: -1, unresolved: 0, else: >0)
    */
    double getDuration();
    
    
    /**
    *  Return the number of frames per second for this document.
    *  The number returned is the rate of the first video component if there is one, 
    *  or else of the first audio component if there's no video.  
    *  If there's neither one an ad hoc value is returned.
    */
    int getFrameRate();
   
   
    /**
    *  Returns the number of frames per second of the designated media element.
    *  The argument relativeUrlStr should be relative to the smil document
    */
    int getMediaFrameRate(String relativeUrlStr) throws GRiNSException;
    
    /**
    *  After using a SMILDocument you should <em>always</em> call this method 
    *  to dispose resources allocated for this document. 
    */
   void close();
}