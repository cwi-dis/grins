
package grins;

import java.awt.Canvas;
import java.awt.Dimension;

public interface SMILDocument {
    SMILController getController();
    SMILRenderer getRenderer();
    int getViewportCount();
    Dimension getViewportSize(int index);
    String getViewportTitle(int index);
    double getDuration();
    void close();
}