package com.oratrix.xml.parse;

import java.util.Locale;

/**
 *
 * @version $Revision$ $Date$
 */
public class ParserBase {
  protected EntityManager entityManager = new EntityManagerImpl();
  protected Locale locale = Locale.getDefault();

  public void setEntityManager(EntityManager entityManager) {
    if (entityManager == null)
      throw new NullPointerException();
    this.entityManager = entityManager;
  }

  public void setLocale(Locale locale) {
    if (locale == null)
      throw new NullPointerException();
    this.locale = locale;
  }
}
