import gphoto2 as gp
import yaml
import platform, sys


def get_value(config):
    return gp.check_result(gp.gp_widget_get_value(config))


def count_children(config):
    return gp.check_result(gp.gp_widget_count_children(config))


class HandlerThing:
    def get(self, config):
        pass

    def set(self, config, value):
        raise NotImplementedError


class Menu(HandlerThing):
    """ Has one value from set of many.  Value is the index in list of options.
    """

    def get(self, config):
        assert count_children(config) == 0  # not sure
        layout = dict()
        options = list()
        value = get_value(config)
        layout['options'] = options
        layout['value'] = value
        choice_count = gp.check_result(gp.gp_widget_count_choices(config))
        for n in range(choice_count):
            choice = gp.check_result(gp.gp_widget_get_choice(config, n))
            if choice:
                options.append(choice)

        return layout


class Text(HandlerThing):
    def get(self, config):
        assert count_children(config) == 0  # not sure
        layout = dict()
        value = get_value(config)
        if sys.version_info[0] < 3:
            value = value.decode('utf-8')
        layout['value'] = value
        return layout


class Radio(HandlerThing):
    """ Has one value from set of many.  Value is copy of a choice.
    """

    def get(self, config):
        assert count_children(config) == 0  # not sure
        layout = dict()
        options = list()
        value = get_value(config)
        layout['options'] = options
        layout['value'] = value
        for choice in gp.check_result(gp.gp_widget_get_choices(config)):
            if choice:
                options.append(choice)
        return layout

    def set(self, config, value):
        assert value['value'] in value['options']
        gp.check_result(gp.gp_widget_set_value(config, value['value']))


class Toggle(HandlerThing):
    def get(self, config):
        assert gp.check_result(gp.gp_widget_count_children(config)) == 0
        value = gp.check_result(gp.gp_widget_get_value(config))
        return {'value': bool(value)}


class Section(HandlerThing):
    def get(self, config):
        parent_options = dict()

        child_count = gp.check_result(gp.gp_widget_count_children(config))
        if child_count < 1:
            return parent_options

        for child in gp.check_result(gp.gp_widget_get_children(config)):
            label = gp.check_result(gp.gp_widget_get_label(child))
            name = gp.check_result(gp.gp_widget_get_name(child))
            child_type = gp.check_result(gp.gp_widget_get_type(child))

            try:
                handler_class = handlers[child_type]
            except KeyError:
                print('Cannot make widget type %d for %s' % (child_type, label))
                child_options = dict()

            else:
                handler = handler_class()
                child_options = handler.get(child)

            finally:
                child_options['prototype'] = child_type
                child_options['label'] = label
                child_options['name'] = name
                parent_options[name] = child_options

        return parent_options

    def set(self, config, value):
        child_count = gp.check_result(gp.gp_widget_count_children(config))
        if child_count < 1:
            return

        for child in gp.check_result(gp.gp_widget_get_children(config)):
            name = gp.check_result(gp.gp_widget_get_name(child))
            child_type = gp.check_result(gp.gp_widget_get_type(child))

            # do we have a config to change?
            try:
                child_value = value[name]

            except KeyError:
                pass

            else:
                # yes, let's change it
                try:
                    handler_class = handlers[child_type]
                except KeyError:
                    pass

                else:
                    handler = handler_class()
                    try:
                        handler.set(child, child_value)
                    except NotImplementedError:
                        pass


handlers = {
    gp.GP_WIDGET_MENU: Menu,
    gp.GP_WIDGET_RADIO: Radio,
    gp.GP_WIDGET_SECTION: Section,
    gp.GP_WIDGET_TEXT: Text,
    gp.GP_WIDGET_TOGGLE: Toggle,
    # gp.GP_WIDGET_BUTTON: None,
    # gp.GP_WIDGET_DATE: None,
    # gp.GP_WIDGET_RANGE: None,
    # gp.GP_WIDGET_WINDOW: None,
}

system = platform.system()
if system == 'Linux':
    from tailor.platform.unix import release_gvfs_from_camera

    try:
        release_gvfs_from_camera()
    except FileNotFoundError:
        pass

camera = gp.check_result(gp.gp_camera_new())
gp.check_result(gp.gp_camera_init(camera))
camera_config = gp.check_result(gp.gp_camera_get_config(camera))

handler = Section()
default_values = handler.get(camera_config)

print(yaml.dump(default_values))

default_values['capturesettings']['shutterspeed']['value'] = '1/400'
default_values['capturesettings']['aperture']['value'] = '7.1'
default_values['imgsettings']['iso']['value'] = '400'
handler.set(camera_config, default_values)
gp.check_result(gp.gp_camera_set_config(camera, camera_config))  # root config
