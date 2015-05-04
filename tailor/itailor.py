from zope.interface import Interface, Attribute


class ITailorPlugin(Interface):
    process = Attribute('do something with another thing')


class ITrigger(Interface):
    process = Attribute('do something with another thing')


class IImageOp(Interface):
    process = Attribute('do something with another thing')


class IFileOp(Interface):
    process = Attribute('do something with another thing')


class ITemplate(Interface):
    pass


class ILayer(Interface):
    pass


class ICamera(Interface):
    save_preview = Attribute("capture preview")
    save_capture = Attribute("capture full image")
    download_preview = Attribute("capture and download preview")
    download_capture = Attribute("capture and download full image")
    reset = Attribute("reset the camera")
