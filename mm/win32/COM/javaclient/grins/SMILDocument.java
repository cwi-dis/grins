
package grins;

import java.awt.Canvas;
import java.awt.Dimension;

public interface SMILDocument {
    SMILController getController();
    SMILRenderer getRenderer();
    
    Dimension getViewportSize() throws Exception;
    
    void open(String fn);
    void close();
}