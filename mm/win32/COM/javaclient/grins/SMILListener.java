
package grins;

public interface SMILListener {
    void opened();
    void setDur(double dur);
    void setPos(double pos);
    void closed();
    void setWaiting();
    void setReady();
}