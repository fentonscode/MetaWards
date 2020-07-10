=========================
Creating a Custom Network
=========================

While the default networks supplied in ``MetaWardsData`` model the UK, there
is nothing to stop you creating your own network to model any country or
region. Indeed, you can use the concepts of ``wards``, ``workers`` and
``players`` in a more generic way to model lots of different environments,
e.g.

* Using wards to represent different university buildings, and then track
  disease spread between buildings as staff and students move around.
* Using wards to represent care homes, hospitals and homes in a single
  region, and then model the motion of staff, patients and the general
  population between these different environments.

Network file formats
--------------------

A lot of data needs to be loaded to define the network. There are two
file formats for specifying this data;

1. :doc:`A set of fixed-format files <../../fileformats/network>` that
   contain the data in a set of files that are contained in a single
   directory. This is an older format that is used predominantly for
   older model networks.

2. A JSON-format file that contains all of the data needed to describe the
   network in a single file. This file should only be manipulated or
   edited using the Python API described below.

Creating and editing Networks in Python
---------------------------------------

The best way to create a new network is to use the Python API. A
:class:`~metawards.Network` is edited or created via the
:class:`~metawards.Wards` class. This represents an editable collection
of individual :class:`~metawards.Ward` objects, each of which
represents a ward. The :class:`~metawards.Ward` provides functions
for setting the name and metadata for a ward, plus adding work and
play connections to other wards.

For example, we can interactively create a new :class:`~metawards.Network`
using the :class:`~metawards.Ward` and :class:`~metawards.Wards` classes
in, e.g. ipython or a jupyter notebook;

First, we will import the necessary classes and create our
:class:`~metawards.Wards` object, which we will call ``wards``;

.. code-block:: python

   >>> from metawards import Ward, Wards, Network
   >>> wards = Wards()

Next, we will create a :class:`~metawards.Ward` object to represent
Bristol (which we will call ``bristol``). We will give this the ID
number of ``1``, and will add `500`
workers who will work in Bristol, and ``750`` players.

.. code-block:: python

   >>> bristol = Ward(id=1, name="Bristol")
   >>> bristol.add_workers(500)
   >>> bristol.set_num_players(750)

Next, we will create a :class:`~metawards.Ward` object to represent
London (which we will call ``london``). We will give this the ID
number of ``2``, and will add ``8600``
workers and ``10000`` players.

   >>> london = Ward(id=2, name="London")
   >>> london.add_workers(8500)
   >>> london.set_num_players(10000)

.. note::

   You are free to use whatever ID number you wish, as long as it is positive
   and greater or equal to 1. For efficiency, you should identify the
   wards using ID numbers that start from 1 and increase consecutively.

Now, we will add some commuters. We will have ``500`` Bristolians
commute each day to London (``destination=2``), while ``100`` Londoners
will commute each day to Bristol (``destination=1``)

.. code-block:: python

   >>> bristol.add_workers(500, destination=2)
   >>> london.add_workers(100, destination=1)

We can confirm that the information is correct by printing, e.g.

.. code-block:: python

   >>> print(bristol)
   Ward( id=1, name=Bristol, num_workers=1000, num_players=750 )

   >>> print(london)
   Ward( id=2, name=London, num_workers=8600, num_players=10000 )

Next, we add the two :class:`~metawards.Ward` objects to our
:class:`~metawards.Wards` object that represents the entire model.

.. code-block:: python

   >>> wards.add(bristol)
   >>> wards.add(london)
   >>> print(wards)
   [ Ward( id=1, name=Bristol, num_workers=1000, num_players=750 ), Ward( id=2, name=London, num_workers=8600, num_players=10000 ) ]

We can now save this set of :class:`~metawards.Wards` to a file by converting
this to a data dictionary, and then serialising that dictionary to JSON,
which we will stream to the file ``custom_network.json.bz2``.

.. code-block:: python

   >>> wards.to_json("custom_network.json", indent=2)

The resulting JSON file will look something like this;

::

  [
    {
      "id": 1,
      "info": {
        "name": "Bristol"
      },
      "num_workers": 1000,
      "num_players": 750,
      "workers": {
        "destination": [
          1,
          2
        ],
        "population": [
          500,
          500
        ]
      }
    },
    {
      "id": 2,
      "info": {
        "name": "London"
      },
      "num_workers": 8600,
      "num_players": 10000,
      "workers": {
        "destination": [
          1,
          2
        ],
        "population": [
          100,
          8500
        ]
      }
    }
  ]

.. note::

   Note that the exact format of the JSON will change as ``metawards``
   evolves. We will retain backwards compatibility, meaning that newer
   versions of ``metawards`` will be able to read old files, but older
   versions may not be able to read new files.

   Note that the file will be automatically compressed using bzip2. You
   can disable this by setting ``auto_bzip=False``.

   Note also that ``indent=2`` just sets the indentation used for printing.
   You can set whatever indentation you want, including not setting any.
   It won't affect the included information - just its human-readability.

You can load this JSON file into a Wards object using;

.. code-block:: python

   >>> wards = Wards.from_json("custom_network.json.bz2")
   >>> print(wards)
   [ Ward( id=1, name=Bristol, num_workers=1000, num_players=750 ), Ward( id=2, name=London, num_workers=8600, num_players=10000 ) ]
