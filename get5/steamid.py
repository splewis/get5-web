from valve.steam.id import SteamID, SteamIDError

import json
import re
import urllib
import urllib2
from xml.dom import minidom
from xml.parsers.expat import ExpatError


def steam2_to_steam64(steam2):
    try:
        return True, SteamID.from_text(steam2).as_64()
    except SteamIDError:
        return False, ''


def steam3_to_steam2(steam3):
    if '[U:1:' not in steam3:
        return False, ''

    try:
        x = int(steam3[5: len(steam3) - 1])
    except ValueError:
        return False, ''

    if x == 0:
        return False, ''

    a = x % 2
    b = (x - a) / 2
    steam2 = 'STEAM_0:{}:{}'.format(a, b)
    return True, steam2


def steam64_from_dom(dom):
    elements = dom.getElementsByTagName('steamID64')
    if len(elements) >= 1:
        return True, str(elements[0].firstChild.data)
    else:
        return False, ''


def custom_url_to_steam3(url):
    if not '?xml=1' in url:
        url += '?xml=1'

    try:
        dom = minidom.parse(urllib2.urlopen(url))
    except ExpatError:
        return False, ''

    return steam64_from_dom(dom)


def custom_name_to_steam3(name):
    url = re.sub("{USER}", name, 'http://steamcommunity.com/id/{USER}/?xml=1')
    return custom_url_to_steam3(url)


def auth_to_steam64(auth):
    auth = auth.strip()
    if 'steamcommunity.com/id/' in auth:
        return custom_url_to_steam3(auth)

    elif 'steamcommunity.com/profiles/' in auth:
        try:
            return True, SteamID.from_community_url(auth.rstrip('/')).as_64()
        except SteamIDError:
            return False, ''

    elif auth.startswith('1:0:') or auth.startswith('1:1'):
        return steam2_to_steam64('STEAM_' + auth)

    elif auth.startswith('STEAM_'):
        return steam2_to_steam64(auth)

    elif auth.startswith('7656119') and not 'steam' in auth:
        return True, auth

    elif auth.startswith('[U:1:'):
        suc, steam2 = steam3_to_steam2(auth)
        if suc:
            return steam2_to_steam64(steam2)
        else:
            return False, ''

    else:
        return custom_name_to_steam3(auth)


def is_valid_steamid(auth):
    valid, _ = auth_to_steam64(auth)
    return valid


def get_steam_userinfo(steamid, api_key):
    options = {
        'key': api_key,
        'steamids': steamid,
    }
    url = 'http://api.steampowered.com/ISteamUser/' \
          'GetPlayerSummaries/v0001/?%s' % urllib.urlencode(options)
    rv = json.load(urllib2.urlopen(url))
    return rv['response']['players']['player'][0] or {}
