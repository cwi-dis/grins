package com.oratrix.xml.parse;

/**
 * Thrown to indicate that a method in <code>Application</code> has thrown
 * an Exception.
 * An <code>ApplicationException</code> is not thrown when a method
 * in <code>Application</code> throws an exception derived
 * from <code>RuntimeException</code>.
 * @version $Revision$ $Date$
 */

public class ApplicationException extends Exception {
  private final Exception exception;
  public ApplicationException(Exception e) {
    exception = e;
  }
  /**
   * Returns the exception thrown by the <code>Application</code> method.
   */
  public Exception getException() {
    return exception;
  }
}
