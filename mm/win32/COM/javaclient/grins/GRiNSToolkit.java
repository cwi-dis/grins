
package grins;

 /**
 *   The entry point to the GRiNS package.
 *   You use the factory method createDocument(String filenameOrUrl) 
 *   of a GRiNSToolkit to create a SMILDocument.
 */
public class GRiNSToolkit {
    /**
    *   Return a SMILDocument from the content located at the
    *   specified filename or URL.
    */
    static public SMILDocument createDocument(String filenameOrUrl){
        return new GRiNSPlayer(filenameOrUrl);
    }
}
