
package grins;

public class GRiNSToolkit {
    static public SMILDocument createGRiNSDocument(SMILListener listener){
        return new GRiNSPlayer(listener);
    }
}
