package com.oratrix.xml.tok;

/**
 * Thrown to indicate that the byte subarray being tokenized is a legal XML
 * token, but that subsequent bytes in the same entity could be part of
 * the token.  For example, <code>Encoding.tokenizeProlog</code>
 * would throw this if the byte subarray consists of a legal XML name.
 * @version $Revision$ $Date$
 */
public class ExtensibleTokenException extends TokenException {
  private int tokType;

  ExtensibleTokenException(int tokType) {
    this.tokType = tokType;
  }

  /**
   * Returns the type of token in the byte subarrary.
   */
  public int getTokenType() {
    return tokType;
  }
}
