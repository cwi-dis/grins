
package grins;

import java.awt.Canvas;
import java.awt.Dimension;

public interface SMILDocument {
    SMILController getController();
    SMILRenderer getRenderer();
    Dimension getViewportSize();
    double getDuration();
    void close();
}