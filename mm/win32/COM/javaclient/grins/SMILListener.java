
package grins;

public interface SMILListener {
    void opened();
    void closed();
    void setWaiting();
    void setReady();
}