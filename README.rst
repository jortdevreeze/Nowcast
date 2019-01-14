Nowcast
=======

Python script to extract data which can be used for nowcasting

I have invested a lot of time and effort in creating this Python script, please cite it when using it in the preparation of a manuscript.

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
  >>> for name in users_uk.intersection(users_ru):
  >>>     unique_users.append(name)
  >>>
  >>> wiki.extract_revisions_by_user(lang="ru", username=unique_users[0])
  >>> ...
  
