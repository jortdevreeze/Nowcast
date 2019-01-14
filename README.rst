Nowcast
=======

Python script to extract data which can be used for nowcasting

I have invested a lot of time and effort in creating this Python script, please cite it when using it in the preparation of a manuscript.

To install ParseWiki, simply run:

::

  $ pip install parsewiki

.. code:: python

  >>> from parsewiki import page
  >>>
  >>> wiki = page.Parse("Annexation of Crimea by the Russian Federation")
  >>> wiki.extract()
  >>> wiki.extract(lang="uk")
  >>> wiki.extract(lang="ru")
  >>>
  >>> users_uk = set(wiki.get_users(lang="uk"))
  >>> users_ru = set(wiki.get_users(lang="ru"))
  >>>
  >>> unique_users = []
  >>> for name in users_ca.intersection(users_es):
  >>>     users.append(name)
  >>>
  >>> page.extract_revisions_by_user(lang="ru", username=users[0])
  
