
import java.awt.Component;

interface Renderer {
    void setComponent(Component c);
    Component getComponent();
    void update();
    void mouseClicked(int x, int y);
    boolean mouseMoved(int x, int y);
    
}
