
package grins;

public class GRiNSToolkit {
    static public SMILDocument createDocument(String filename){
        return new GRiNSPlayer(filename);
    }
}
