def as_int(val, on_fail=0):
    if val is None:
        return on_fail
    try:
        return int(val)
    except ValueError:
        return on_fail


def format_mapname(mapname):
    formatted_names = {
        'de_cache': 'Cache',
        'de_cbble': 'Cobblestone',
        'de_dust2': 'Dust II',
        'de_mirage': 'Mirage',
        'de_nuke': 'Nuke',
        'de_overpass': 'Overpass',
        'de_train': 'Train',
        'de_inferno': 'Inferno',
        'de_season': 'Season',
    }
    if mapname in formatted_names:
        return formatted_names[mapname]
    else:
        return mapname


def check_server_connection(server):
    response = send_rcon_command(
        server.ip_string, server.port, server.rcon_password, 'status')
    return response is not None


def check_server_avaliability(server):
    import json

    if not server:
        return False, 'Server not found'

    response = send_rcon_command(
        server.ip_string, server.port, server.rcon_password, 'get5_web_avaliable')

    if response:
        json_error = False
        already_live = False
        try:
            json_status = json.loads(response)
            already_live = json_status['gamestate'] != 0
        except (ValueError, KeyError):
            json_error = True

    if response is None:
        return False, 'Failed to connect to server'

    elif 'Unknown command' in str(response):
        return False, 'get5 server plugin not found on server'

    elif already_live:
        return False, 'Server already has a get5 match setup'

    elif json_error:
        return False, 'Error reading get5_web_avaliable response'

    else:
        return True, ''


class RconError(ValueError):
    pass


def send_rcon_command(host, port, rcon_password, command, raise_errors=False, num_retries=3, timeout=3.0):
    from valve.source.rcon import RCON, IncompleteMessageError, AuthenticationError, NoResponseError
    import socket

    try:
        port = int(port)
    except ValueError:
        return None

    attempts = 0
    while attempts < num_retries:
        attempts += 1
        try:
            with RCON((host, port), rcon_password, timeout=timeout) as rcon:
                response = rcon(command)
                return strip_rcon_logline(response)

        except KeyError:
            # There seems to be a bug in python-vavle where a wrong password
            # trigger a KeyError at line 203 of valve/source/rcon.py,
            # so this is a work around for that.
            raise RconError('Incorrect rcon password')

        except (socket.error, socket.timeout,
                IncompleteMessageError, AuthenticationError, NoResponseError) as e:
            if attempts >= num_retries:
                if raise_errors:
                    raise RconError(str(e))
                else:
                    return None


def strip_rcon_logline(response):
    lines = response.splitlines()
    if len(lines) >= 1:
        last_line = lines[len(lines) - 1]
        if 'rcon from' in last_line:
            return '\n'.join(lines[:len(lines) - 1])

    return response
