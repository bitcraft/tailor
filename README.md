Tailor
======

Tailor is a set of hardware plans and software for a wedding/event photo booth
and includes image processing, camera control, live slideshow, and touch based
image browser for kiosk operation.  It is a project in development and is
currently in a broken state as I add better template support.

This project aims for Windows, OS X, and Linux compatibility, but not all
features are supported on each platform now.  Currently, full features are
available on OS X and Linux;  camera capture is currently unavailable on
Windows, but it is being worked on.

I use Tailor for my professional photobooth service.

The name "tailor" is currently just a stand-in and may change at any time.


Cameras
-------

Any camera supported by libgphoto2 is supported by this software.  An up-to-date
list is available on their website.  Live-view is functional, and can be used
to preview photos before they are taken.

Webcams are supported but not recommended as they produce poor quality images.

http://www.gphoto.org/proj/libgphoto2/support.php


Interaction
-----------

Tailor supports the arduino for interfacing with physical buttons over USB
and also has a smartphone-inspired touch interface.  For computer systems
without a touch screen monitor, the mouse can be used.

The kiosk interface offers print/reprint controls, camera tilt, email,
camera live view, and twitter.


Running the touch interface
---------------------------

service.py runs the camera capture service.
kiosk.py runs the touch interface.

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
use this software and need help getting your system going I will be accepting
paypal donations in exchange for my time.

I reserve all rights to determine what features will be added and how the
interface is used for this software that is hosted here.  You are welcome to
fork this project at any time and customize it as you wish, subject to the
restrictions outlined in the file called 'license' found in the repository.


General Requirements
--------------------

This is a general list of requirements.  Certain functions of this
software may require additional dependencies.

-  Debian Linux, OS X 10.x, or Windows 7+
-  Python 3.4+
-  Kivy 1.9+
-  Arduino with firmata firmware


Windows OS Support
------------------

I'm working towards support of Windows OS.

Kivy and pygame can be downloaded from here:
http://www.lfd.uci.edu/~gohlke/pythonlibs/


Remote Operation
----------------

Currently, this project requires a dedicated PC, touch screen monitor, and an arduino.  In 
the near future, it will be possible to run the the booth with a dedicated embedded system
and a tablet touch screen PC for control (no apple or android...yet).

The vision is using a low cost system like the Raspberry Pi to operate the camera and printer,
while a PC tablet (like the microsoft surface x86 only, or yoga) can be used to monitor the
camera, request additional prints, change template, set up events, or do social ops like
upload to twitter or facebook.

The result will be a compact and easy-to-transport booth with a portable tablet interface.

Of course, it will still be possible to operate everything on one pc.

Gods willing, an iOS and android app will be available.


Legal
-----

All files under the 'tailor' directory are copyright Leif Theden, 2012-2015
and licensed under the GPLv3.

All other code may or not be GPLv3, please check the source of each file.
