
package grins;

public
class GRiNSException extends Exception {
    /**
     * Constructs an <code>GRiNSException</code> with no specified detail message. 
     */
    public GRiNSException() {
	super();
    }

    /**
     * Constructs an <code>GRiNSException</code> with the specified detail message. 
     *
     * @param   s   the detail message.
     */
    public GRiNSException(String s) {
	super(s);
    }
}
