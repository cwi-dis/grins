package com.oratrix.xml.tok;

/**
 * Thrown to indicate that the byte subarray being tokenized does not start
 * with a legal XML token but might be one if the subarray were extended.
 * @version $Revision$ $Date$
 */
public class PartialTokenException extends TokenException {
}
