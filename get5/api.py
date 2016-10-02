from get5 import app, limiter, db, BadRequestError
from util import as_int
from models import Match, MapStats, PlayerStats, GameServer

from flask import Blueprint, request
import flask_limiter

import re
import datetime

api_blueprint = Blueprint('api', __name__)


_matchid_re = re.compile('/match/(\d*)/.*')


def rate_limit_key():
    try:
        match = _matchid_re.search(request.path)
        matchid = int(match.group(1))
        if matchid:
            # If the key matches, rate limit by the api key
            api_key = Match.query.get_or_404(matchid).api_key
            if api_key == request.values.get('key'):
                return api_key

    except Exception:
        pass

    # Otherwise, rate limit by IP address
    return flask_limiter.util.get_remote_address()


def match_api_check(request, match):
    if match.api_key != request.values.get('key'):
        raise BadRequestError('Wrong API key')

    if match.finalized():
        raise BadRequestError('Match already finalized')


@api_blueprint.route('/match/<int:matchid>/finish', methods=['POST'])
@limiter.limit('60 per hour', key_func=rate_limit_key)
def match_finish(matchid):
    match = Match.query.get_or_404(matchid)
    match_api_check(request, match)

    winner = request.values.get('winner')
    if winner == 'team1':
        match.winner = match.team1_id
    elif winner == 'team2':
        match.winner = match.team2_id
    else:
        match.winner = None

    forfeit = request.values.get('forfeit', 0)
    if forfeit == 1:
        match.forfeit = True
        # Reassign scores
        if winner == 'team1':
            match.team1_score = 1
            match.team2_score = 0
        elif winner == 'team2':
            match.team1_score = 0
            match.team2_score = 1

    match.end_time = datetime.datetime.utcnow()
    server = GameServer.query.get(match.server_id)
    if server:
        server.in_use = False

    db.session.commit()
    app.logger.info('Finished match {}, winner={}'.format(match, winner))

    return 'Success'


@api_blueprint.route('/match/<int:matchid>/map/<int:mapnumber>/start', methods=['POST'])
@limiter.limit('60 per hour', key_func=rate_limit_key)
def match_map_start(matchid, mapnumber):
    match = Match.query.get_or_404(matchid)
    match_api_check(request, match)

    if match.start_time is None:
        match.start_time = datetime.datetime.utcnow()

    map_name = request.values.get('mapname')

    # Create mapstats object if needed
    MapStats.get_or_create(matchid, mapnumber, map_name)
    db.session.commit()

    return 'Success'


@api_blueprint.route('/match/<int:matchid>/map/<int:mapnumber>/update', methods=['POST'])
@limiter.limit('1000 per hour', key_func=rate_limit_key)
def match_map_update(matchid, mapnumber):
    match = Match.query.get_or_404(matchid)
    match_api_check(request, match)

    map_stats = match.map_stats.filter_by(map_number=mapnumber).first()
    if map_stats:
        t1 = as_int(request.values.get('team1score'))
        t2 = as_int(request.values.get('team2score'))
        if t1 != -1 and t2 != -1:
            map_stats.team1_score = t1
            map_stats.team2_score = t2
            db.session.commit()
    else:
        return 'Failed to find map stats object', 400

    return 'Success'


@api_blueprint.route('/match/<int:matchid>/map/<int:mapnumber>/finish', methods=['POST'])
@limiter.limit('60 per hour', key_func=rate_limit_key)
def match_map_finish(matchid, mapnumber):
    match = Match.query.get_or_404(matchid)
    match_api_check(request, match)

    map_stats = match.map_stats.filter_by(map_number=mapnumber).first()
    if map_stats:
        map_stats.end_time = datetime.datetime.utcnow()

        winner = request.values.get('winner')
        if winner == 'team1':
            map_stats.winner = match.team1_id
            match.team1_score += 1
        elif winner == 'team2':
            map_stats.winner = match.team2_id
            match.team2_score += 1
        else:
            map_stats.winner = None

        db.session.commit()
    else:
        return 'Failed to find map stats object', 404

    return 'Success'


@api_blueprint.route('/match/<int:matchid>/map/<int:mapnumber>/player/<steamid64>/update', methods=['POST'])
@limiter.limit('100 per minute', key_func=rate_limit_key)
def match_map_update_player(matchid, mapnumber, steamid64):
    match = Match.query.get_or_404(matchid)
    api_key = request.values.get('key')
    if match.api_key != api_key:
        return 'Wrong API key', 400

    map_stats = match.map_stats.filter_by(map_number=mapnumber).first()
    if map_stats:
        player_stats = PlayerStats.get_or_create(matchid, mapnumber, steamid64)
        if player_stats:
            player_stats.name = request.values.get('name')
            team = request.values.get('team')
            if team == 'team1':
                player_stats.team_id = match.team1_id
            elif team == 'team2':
                player_stats.team_id = match.team2_id

            player_stats.kills = as_int(request.values.get('kills'))
            player_stats.assists = as_int(request.values.get('assists'))
            player_stats.deaths = as_int(request.values.get('deaths'))
            player_stats.flashbang_assists = as_int(
                request.values.get('flashbang_assists'))
            player_stats.teamkills = as_int(request.values.get('teamkills'))
            player_stats.suicides = as_int(request.values.get('suicides'))
            player_stats.damage = as_int(request.values.get('damage'))
            player_stats.headshot_kills = as_int(
                request.values.get('headshot_kills'))
            player_stats.roundsplayed = as_int(
                request.values.get('roundsplayed'))
            player_stats.bomb_plants = as_int(
                request.values.get('bomb_plants'))
            player_stats.bomb_defuses = as_int(
                request.values.get('bomb_defuses'))
            player_stats.k1 = as_int(request.values.get('1kill_rounds'))
            player_stats.k2 = as_int(request.values.get('2kill_rounds'))
            player_stats.k3 = as_int(request.values.get('3kill_rounds'))
            player_stats.k4 = as_int(request.values.get('4kill_rounds'))
            player_stats.k5 = as_int(request.values.get('5kill_rounds'))
            player_stats.v1 = as_int(request.values.get('v1'))
            player_stats.v2 = as_int(request.values.get('v2'))
            player_stats.v3 = as_int(request.values.get('v3'))
            player_stats.v4 = as_int(request.values.get('v4'))
            player_stats.v5 = as_int(request.values.get('v5'))
            db.session.commit()
    else:
        return 'Failed to find map stats object', 404

    return 'Success'
