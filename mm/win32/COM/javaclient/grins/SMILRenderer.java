
package grins;

import java.awt.Dimension;

public interface SMILRenderer {
    void setCanvas(PlayerCanvas c) throws Exception;
    void mouseClicked(int x, int y);
    boolean mouseMoved(int x, int y);
    void update();
}