
==============
pibooth-qrcode
==============

|PythonVersions| |PypiPackage| |Downloads|

``pibooth-qrcode`` is a plugin for the `pibooth`_ application.

It adds the display of a custom qrcode at the print and wait state

Install
-------

::

    $ pip3 install pibooth-qrcode

Configuration
-------------

Here below the new configuration options available in the `pibooth`_ configuration.
**The keys and their default values are automatically added to your configuration after first** `pibooth`_ **restart.**

.. code-block:: ini

[QRCODE]
# URL which may be composed of variables: {picture}, {count}, {url}
# Required by 'qrcode' plugin
prefix_url = https://mypicturewebsite.com/MyGallery/index.html?img={picture}&key=MYPASSWORD

# Foreground color
# Required by 'qrcode' plugin
foreground = (255, 255, 255)

# Background color
# Required by 'qrcode' plugin
background = (0, 0, 0)

# Optional text displayed close to the QR code
# Required by 'qrcode' plugin
side_text = "Scan with phone"

# Offset (x, y) from location
# Required by 'qrcode' plugin
offset = (20, 40)

# Location on 'wait' state: topleft, topright, bottomleft, bottomright, midtop-left, midtop-right, midbottom-left, midbottom-right
# Required by 'qrcode' plugin
wait_location = bottomright

# Location on 'print' state: topleft, topright, bottomleft, bottomright, midtop-left, midtop-right, midbottom-left, midbottom-right
# Required by 'qrcode' plugin
print_location = bottomright

# Save the generated QR image next to the picture file
# Required by 'qrcode' plugin
save = True

# Suffix to add to picture basename for saved QR file
# Required by 'qrcode' plugin
suffix = _qrcode

# Extension for saved QR file
# Required by 'qrcode' plugin
ext = png

# Optional directory to save QR images (overrides GENERAL.directory)
# Required by 'qrcode' plugin
save_path = /home/pi/Pictures

.. note:: Edit the configuration by running the command ``pibooth --config``.

QR code URL
-----------

The URL linked to the QR code can be define dynamically using some state variables or configuration
options. Available variables to forge the URL are:

- **picture** : current picture filename
- **count** : current counters. You can access to values using ``{count.xxx}`` (see counters
  in configuration menu)
- **url** : current picture URL as defined in ``app.previous_picture_url`` attribute (this attribute is
  generally defined by another plugin).

For instance, ``https://photos.google.com/share/AxFF4t56kiJiu89m/{picture}`` will generate::

    https://photos.google.com/share/AxFF4t56kiJiu89m/2021-06-11-10-14-08_pibooth.jpg

QR code locations
-----------------

Here is the possible QR code location at screen:

.. image:: https://raw.githubusercontent.com/peteoheat/pibooth-qrcode/master/docs/images/locations.png
   :align: center
   :alt: Locations

Example
-------

Here is an example of the rendering you can get with this plugin on the wait screen:

.. image:: https://raw.githubusercontent.com/peteoheat/pibooth-qrcode/master/docs/images/screenshot.png
   :align: center
   :alt: Example screenshot

.. --- Links ------------------------------------------------------------------

.. _`pibooth`: https://pypi.org/project/pibooth

.. |PythonVersions| image:: https://img.shields.io/badge/python-3.6+-red.svg
   :target: https://www.python.org/downloads
   :alt: Python 3.6+

.. |PypiPackage| image:: https://badge.fury.io/py/pibooth-qrcode.svg
   :target: https://pypi.org/project/pibooth-qrcode
   :alt: PyPi package

.. |Downloads| image:: https://img.shields.io/pypi/dm/pibooth-qrcode?color=purple
   :target: https://pypi.org/project/pibooth-qrcode
   :alt: PyPi downloads
