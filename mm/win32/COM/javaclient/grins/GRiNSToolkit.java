
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
    *
    * @param  filenameOrUrl   document location as filename or a URL string.
    * @param  license   GRiNS license string.
    *
    */
    static public SMILDocument createDocument(String filenameOrUrl, String license){
        return new GRiNSPlayer(filenameOrUrl, license);
        }
}
