
import java.awt.Component;

interface Renderer {
    void setComponent(Component c);
    Component getComponent();
    void update();
}
