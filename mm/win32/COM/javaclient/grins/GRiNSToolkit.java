
package grins;

 /**
 *   The entry point to the GRiNS package.
 *   You use the factory method createDocument(String filenameOrUrl) 
 *   or createDocument(String filenameOrUrl, String license)
 *   of a GRiNSToolkit to create a SMILDocument.
 *   To use the first version of createDocument you must set GRiNS Player 
 *   license using the method setLicense(String license) before the createDocument call.
 */
public class GRiNSToolkit {
    /**
    *   Return a SMILDocument from the content located at the
    *   specified filename or URL authorize client with licence string.
    *
    * @param  filenameOrUrl   document location as filename or a URL string.
    * @param  licensestr   license string.
    *
    */
    static public SMILDocument createDocument(String filenameOrUrl, String licensestr) 
        throws GRiNSException {
        GRiNSToolkit.license = licensestr;
        return new GRiNSPlayer(filenameOrUrl, licensestr);
        }
        
    /**
    *   Return a SMILDocument from the content located at the
    *   specified filename or URL.
    *
    * @param  filenameOrUrl   document location as filename or a URL string.
    *
    */
    static public SMILDocument createDocument(String filenameOrUrl) 
        throws GRiNSException {
        return new GRiNSPlayer(filenameOrUrl, GRiNSToolkit.license);
        }
        
    /**
    *   Set GRiNS player license
    *
    * @param  licensestr   GRiNS Player license string.
    *
    */
    static public void setLicense(String licensestr){GRiNSToolkit.license = licensestr;}
    private static String license = "";
        
}
