
package grins;

 /**
 *   The exception is thrown by most GRiNS native mathods.
 */
public class GRiNSNativeInterfaceException extends Exception {
    /**
     * Constructs an <code>GRiNSNativeInterfaceException</code> with no specified detail message. 
     */
    public GRiNSNativeInterfaceException() {
	super();
    }

    /**
     * Constructs an <code>GRiNSNativeInterfaceException</code> with the specified detail message. 
     *
     * @param   s   the detail message.
     */
    public GRiNSNativeInterfaceException(String s) {
	super(s);
    }
}
