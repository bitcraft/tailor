Tailor
======

Tailor is a set of hardware plans and software for a wedding/event photo
booth and includes image processing, camera control, live slideshow, and
touch based image browser for kiosk operation.  It is a project in
development and is sometimes broken.

This project aims for Windows, OS X, and Linux compatibility, but not all
features are supported on each platform now.  Currently, full features are
available on OS X and Linux; certain camera features are not stable on
Windows, but webcams work well.

The name "tailor" is currently just a stand-in and may change at any time.

I use Tailor for my professional photobooth service.


Cameras
-------

Any camera supported by libgphoto2 is supported by this software.  An up-to-date
list is available on their website.  Live-view is functional, with supported
cameras and can be used to preview photos before they are taken.

Webcams are supported but not recommended as they produce poor quality images.

Please check the following link for camera models:

http://www.gphoto.org/proj/libgphoto2/support.php


Interaction
-----------

Tailor supports the arduino for interfacing with physical buttons over USB
and also has a smartphone-inspired touch interface.  For computer systems
without a touch screen monitor, the mouse can be used.

There is basic support for servos and relay controls with an arduino connected
to the host PC.

The kiosk interface offers:
- print/reprint controls
- camera tilt
- social: email & twitter
- camera live view


Running the touch interface
---------------------------

From OS X or linux, run 'python3 run_local.py'
From windows, launch kivy.bat, then 'python run_local.py'

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
-  Pygame


Windows OS Support
------------------

Tailor works on Windows, but only supports webcams right now, and requires
kivy and pygame.  I will be investigating a stand-alone distribution Q1 2016.


Remote Operation
----------------

Currently, this project requires a dedicated PC, touch screen monitor, and an
arduino.  In the near future, it will be possible to run the the booth with
a dedicated embedded system and a tablet touch screen PC for control (no ios or
android...yet).

The vision is using a low cost system like the Raspberry Pi to operate the
camera and printer, while a PC tablet (like the microsoft surface x86 only,
or yoga) can be used to monitor the camera, request additional prints, change
template, set up events, or do social ops like upload to twitter or facebook.

The result will be a compact and easy-to-transport booth with a portable tablet
interface.  Of course, it will still be possible to operate everything on a pc.

Gods willing, an iOS and android app will be available.


Arduino Support
---------------

The arduino platform is supported to trigger the camera, control servo motor
for camera tilt and relays for turning on lights.  Please use the included
sketch.  I cannot support firmata at this time, but it is being considered.


Linux
-----

Tailor is a python3 only project, so please make sure you are using the correct
python version.  On some systems, you will need to install cython before the rest
the the dependancies.  If you have problems installing kivy from pip, then install
cython first, then the kivy and the rest.


Getting Started
---------------

Tailor is really used by just me, and I keep this repo open for others, so there
are quirks that are specific to getting it going on other computers.  I'm slowly
making it easier for others.  Right now, here are a few step to get going:

* Check run_local.py and verify the python version is correct
* Make sure your camera settings are correct
* Change the working folders to match your system
* Make sure the printer settings are correct
* Use run_local.py to start


Camera Settings
---------------

Found in config/service.json.  Change "camera" "plugin" to one of the following:

* "shutter" for tethered dslr cameras
* "opencv" for webcams
* "dummy" for a color generator, no camera needed


Working Folders
---------------

Found in config/service.json.  Change the enteries under "paths":

* The printer-ready output goes to "print-hot-folder"
* The camera output and other images all go under "images"


Printer Settings
----------------

WIP


Advanced Use
------------

Tailor exposes a webserver on port 5000.  The api can be found in:
apps/server/server.py


Using a Mouse
-------------

Under some conditions, you may not be able to see the mouse cursor after
starting Tailor.  If this is the case, find your Kivy's config.ini and
add the following to the [modules] section:
```
    touchring = show_cursor=true
```
https://kivy.org/docs/api-kivy.modules.touchring.html


Legal
-----

All files under the 'tailor' and 'apps' directories are copyright
Leif Theden, 2012-2016 and licensed under the GPLv3.

All other code may or not be the same; please check the source of each file.
