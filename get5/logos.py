import glob
import os


_logos = set()


def get_logo_dir():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(dir_path, 'static', 'img', 'logos')


def initialize_logos():
    global _logos
    logo_path = get_logo_dir()
    for filename in glob.glob(os.path.join(logo_path, '*.png')):
        team_tag_filename = os.path.basename(filename)
        # Remove the extension
        team_tag = os.path.splitext(team_tag_filename)[0]
        _logos.add(team_tag)


def add_new_logo(tag):
    global _logos
    _logos.insert(tag)


def has_logo(tag):
    return tag in _logos


def get_logo_choices():
    list = [('', 'None')] + [(x, x) for x in _logos]
    return sorted(list, key=lambda x: x[0])


def get_logo_img(tag):
    if has_logo(tag):
        return '/static/img/logos/{}.png'.format(tag)
    else:
        return None
