Tailor
======

Tailor is a set of hardware plans and software for a wedding/event photo and
includes image processing, camera control, live slideshow, and touch based
image browser for kiosk operation.  It is a project in development, but is
stable enough for general use.

This project aims for Windows, OS X, and Linux compatibility, but not all
features are supported on each platform now.  Currently, full features are
available on OS X and Linux;  Camera capture is currently unavailable on
Windows, but it is being worked on.

I use PURIKURA for my professional photobooth service.


Cameras
-------

Any camera supported by libgphoto2 is supported by this software.  An up-to-date
list is available on their website.  Live-view is functional, and can be used
to preview photos before they are taken.

http://www.gphoto.org/proj/libgphoto2/support.php

Webcams are not supported at this time.


Interaction
-----------

PURIKURA supports the arduino for interfacing with physical buttons over USB
and also has a smartphone-inspired touch interface.  For computer systems
without a touch screen monitor, the mouse can be used.

The kiosk interface offers print/reprint controls, camera tilt, email,
camera live view, and twitter.


Running the touch interface
---------------------------

Service.py runs the camera capture service.
Kiosk.py runs the touch interface.

Operation under windows will be documented in the future.  Stay tuned.


Slideshow
---------

A simple slideshow is included that will automatically add new images from a
hot folder.  There are currently 3 formats that rotate: a ken burns effect, a
stacked photos effect, and simple scrolling photos effect.


Getting Help
------------

If you encounter any errors, please issue a bug report.  Also, please note that
while I am providing the software for free, my time is not free.  If you wish to
use this software and need help getting you system going I will be accepting
paypal donations in exchange for my time.

I reserve all rights to determine what features will be added and how the
interface is used for this software that is hosted here.  You are welcome to
fork this project at any time and customize it as you wish.


The Name
--------

'purukura' is a term used in Japan for their ubiquitous style of photo booths.


Requirements
------------

This is a general list of software requirements.  Certain functions of this
software may require additional dependancies.

-  Debian Linux, OS X 10.x, Windows 7+
-  Python 2.7
-  Twisted
-  Kivy


All files under the 'tailor' directory are copyright Leif Theden, 2012-2014
and licensed under the GPLv3.

All other code may or not be GPLv3, please check the source of each file.
