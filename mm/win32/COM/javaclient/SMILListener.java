

interface SMILListener {
    void opened();
    void closed();
    void setWaiting();
    void setReady();
    void setViewportSize(int w, int h);
}