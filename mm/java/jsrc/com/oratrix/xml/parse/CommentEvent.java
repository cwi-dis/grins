package com.oratrix.xml.parse;

/**
 * Information about a comment
 * @see com.oratrix.xml.parse.base.Application#comment
 * @version $Revision$ $Date$
 */
public interface CommentEvent extends LocatedEvent {
  /**
   * Returns the body of the comment occurring between
   * the <code>&lt;--</code> and <code>--&gt;</code>.
   */
  String getComment();
}
