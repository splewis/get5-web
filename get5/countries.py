def get_flag_img_path(country_code):
    if valid_country(country_code):
        return '/static/img/valve_flags/{}.png'.format(country_code.lower())
    else:
        return '/static/img/_unknown.png'


def valid_country(country_code):
    if not country_code:
        return False

    return country_code.lower() in data


def country_name(country_code):
    if not valid_country(country_code):
        return None

    return data[country_code.lower()]


data = {
    'ae': 'United Arab Emirates',
    'ar': 'Argentina',
    'at': 'Austria',
    'au': 'Australia',
    'be': 'Belgium',
    'bg': 'Bulgaria',
    'br': 'Brazil',
    'by': 'Belarus',
    'ca': 'Canada',
    'cc': 'Cocos Islands',
    'ch': 'Switzerland',
    'cl': 'Chile',
    'cn': 'China',
    'cz': 'Czech Republic',
    'de': 'Germany',
    'dk': 'Denmark',
    'dz': 'Algeria',
    'ee': 'Estonia',
    'es': 'Spain',
    'eu': 'European Union',
    'fi': 'Finland',
    'fr': 'France',
    'gb': 'United Kingdom',
    'gp': 'Guadeloupe',
    'gr': 'Greece',
    'hk': 'Hong Kong',
    'hr': 'Croatia',
    'hu': 'Hungary',
    'id': 'Indonesia',
    'ie': 'Ireland',
    'il': 'Israel',
    'in': 'India',
    'ir': 'Iran',
    'is': 'Iceland',
    'it': 'Italy',
    'jp': 'Japan',
    'kr': 'South Korea',
    'kz': 'Kazahkstan',
    'lt': 'Liechtenstein',
    'lu': 'Luxembourg',
    'lv': 'Latvia',
    'ly': 'Libya',
    'mk': 'Macedonia',
    'mo': 'Macao',
    'mx': 'Mexico',
    'my': 'Malaysia',
    'nl': 'Netherlands',
    'no': 'Norway',
    'nz': 'New Zealand',
    'pe': 'Peru',
    'ph': 'Phillippines',
    'pk': 'Pakistan',
    'pl': 'Poland',
    'pt': 'Portugal',
    're': 'Reunion',
    'ro': 'Romania',
    'rs': 'Serbia',
    'ru': 'Russia',
    'sa': 'Saudi Arabia',
    'se': 'Sweden',
    'sg': 'Singapore',
    'si': 'Slovenia',
    'sk': 'Slovokia',
    # 'sq' : '', # ???
    'th': 'Thailand',
    'tr': 'Turkey',
    'tw': 'Taiwan',
    'ua': 'Ukraine',
    'us': 'United States',
    've': 'Venezuela',
    'vn': 'Vietnam',
    'za': 'South Africa',
}


country_choices = sorted(
    [(code, '{} - {}'.format(country_name(code), code.upper()))
     for code in data],
    key=lambda x: x[1]
)
