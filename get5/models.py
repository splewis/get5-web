from get5 import app, db, cache
import countries
import logos
import util

from flask import url_for, Markup
import requests

import datetime
import string
import random


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    steam_id = db.Column(db.String(40), unique=True)
    name = db.Column(db.String(40))
    admin = db.Column(db.Boolean, default=False)
    servers = db.relationship('GameServer', backref='user', lazy='dynamic')
    teams = db.relationship('Team', backref='user', lazy='dynamic')
    matches = db.relationship('Match', backref='user', lazy='dynamic')

    @staticmethod
    def get_or_create(steam_id):
        rv = User.query.filter_by(steam_id=steam_id).first()
        if rv is None:
            rv = User()
            rv.steam_id = steam_id
            db.session.add(rv)
            app.logger.info('Creating user for {}'.format(steam_id))
            rv.admin = ('ADMIN_IDS' in app.config) and (
                steam_id in app.config['ADMIN_IDS'])
        return rv

    def get_url(self):
        return url_for('user', userid=self.id)

    def get_steam_url(self):
        return 'http://steamcommunity.com/profiles/{}'.format(self.steam_id)

    def get_recent_matches(self, limit=10):
        return self.matches.filter_by(cancelled=False).limit(limit)

    def __repr__(self):
        return 'User(id={}, steam_id={}, name={}, admin={})'.format(
            self.id, self.steam_id, self.name, self.admin)


class GameServer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    display_name = db.Column(db.String(32), default='')
    ip_string = db.Column(db.String(32))
    port = db.Column(db.Integer)
    rcon_password = db.Column(db.String(32))
    in_use = db.Column(db.Boolean, default=False)

    @staticmethod
    def create(user, display_name, ip_string, port, rcon_password):
        rv = GameServer()
        rv.user_id = user.id
        rv.display_name = display_name
        rv.ip_string = ip_string
        rv.port = port
        rv.rcon_password = rcon_password
        db.session.add(rv)
        return rv

    def send_rcon_command(self, command, raise_errors=False, num_retries=3, timeout=3.0):
        return util.send_rcon_command(self.ip_string, self.port, self.rcon_password,
                                      command, raise_errors, num_retries, timeout)

    def get_hostport(self):
        return '{}:{}'.format(self.ip_string, self.port)

    def get_display(self):
        if self.display_name:
            return '{} ({})'.format(self.display_name, self.get_hostport())
        else:
            return self.get_hostport()

    def __repr__(self):
        return 'GameServer({})'.format(self.get_hostport())


class Team(db.Model):
    MAXPLAYERS = 7

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(40))
    tag = db.Column(db.String(40), default='')
    flag = db.Column(db.String(4), default='')
    logo = db.Column(db.String(10), default='')
    auths = db.Column(db.PickleType)

    # TODO: add an index for teams with public_team=True
    public_team = db.Column(db.Boolean, index=True)

    @staticmethod
    def create(user, name, tag, flag, logo, auths, public_team=False):
        rv = Team()
        rv.user_id = user.id
        rv.set_data(name, tag, flag, logo, auths, public_team and user.admin)
        db.session.add(rv)
        return rv

    def set_data(self, name, tag, flag, logo, auths, public_team):
        self.name = name
        self.tag = tag
        self.flag = flag.lower() if flag else ''
        self.logo = logo
        self.auths = auths
        self.public_team = public_team

    def can_edit(self, user):
        if not user:
            return False
        if self.user_id == user.id:
            return True
        return False

    def get_players(self):
        results = []
        for steam64 in self.auths:
            if steam64:
                name = get_steam_name(steam64)
                if not name:
                    name = ''

                results.append((steam64, name))
        return results

    def can_delete(self, user):
        if not self.can_edit(user):
            return False
        return self.get_recent_matches().count() == 0

    def get_recent_matches(self, limit=10):
        if self.public_team:
            matches = Match.query.order_by(-Match.id).limit(100).from_self()
        else:
            owner = User.query.get_or_404(self.user_id)
            matches = owner.matches

        recent_matches = matches.filter(
            ((Match.team1_id == self.id) | (Match.team2_id == self.id)) & (
                Match.cancelled == False) & (Match.start_time != None)  # noqa: E712
        ).order_by(-Match.id).limit(5)

        if recent_matches is None:
            return []
        else:
            return recent_matches

    def get_vs_match_result(self, match_id):
        other_team = None
        my_score = 0
        other_team_score = 0

        match = Match.query.get(match_id)
        if match.team1_id == self.id:
            my_score = match.team1_score
            other_team_score = match.team2_score
            other_team = Team.query.get(match.team2_id)
        else:
            my_score = match.team2_score
            other_team_score = match.team1_score
            other_team = Team.query.get(match.team1_id)

        # for a bo1 replace series score with the map score
        if match.max_maps == 1:
            mapstat = match.map_stats.first()
            if mapstat:
                if match.team1_id == self.id:
                    my_score = mapstat.team1_score
                    other_team_score = mapstat.team2_score
                else:
                    my_score = mapstat.team2_score
                    other_team_score = mapstat.team1_score

        if match.live():
            return 'Live, {}:{} vs {}'.format(my_score, other_team_score, other_team.name)
        if my_score < other_team_score:
            return 'Lost {}:{} vs {}'.format(my_score, other_team_score, other_team.name)
        elif my_score > other_team_score:
            return 'Won {}:{} vs {}'.format(my_score, other_team_score, other_team.name)
        else:
            return 'Tied {}:{} vs {}'.format(other_team_score, my_score, other_team.name)

    def get_flag_html(self, scale=1.0):
        # flags are expected to be 32x21
        width = int(round(32.0 * scale))
        height = int(round(21.0 * scale))

        html = '<img src="{}"  width="{}" height="{}">'
        output = html.format(
            countries.get_flag_img_path(self.flag), width, height)
        return Markup(output)

    def get_logo_html(self, scale=1.0):
        if logos.has_logo(self.logo):
            width = int(round(32.0 * scale))
            height = int(round(32.0 * scale))
            html = ('<img src="{}"  width="{}" height="{}">')
            return Markup(html.format(logos.get_logo_img(self.logo), width, height))
        else:
            return ''

    def get_url(self):
        return url_for('team.team', teamid=self.id)

    def get_name_url_html(self):
        return Markup('<a href="{}">{}</a>'.format(self.get_url(), self.name))

    def get_logo_or_flag_html(self, scale=1.0, other_team=None):
        if logos.has_logo(self.logo) and (other_team is None or logos.has_logo(other_team.logo)):
            return self.get_logo_html(scale)
        else:
            return self.get_flag_html(scale)

    def __repr__(self):
        return 'Team(id={}, user_id={}, name={}, flag={}, logo={}, public={})'.format(
            self.id, self.user_id, self.name, self.flag, self.logo, self.public_team)


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    server_id = db.Column(db.Integer, db.ForeignKey('game_server.id'))
    team1_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team2_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team1_string = db.Column(db.String(32), default='')
    team2_string = db.Column(db.String(32), default='')
    winner = db.Column(db.Integer, db.ForeignKey('team.id'))
    plugin_version = db.Column(db.String(32), default='unknown')

    forfeit = db.Column(db.Boolean, default=False)
    cancelled = db.Column(db.Boolean, default=False)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    max_maps = db.Column(db.Integer)
    title = db.Column(db.String(60), default='')
    skip_veto = db.Column(db.Boolean)
    api_key = db.Column(db.String(32))

    veto_mappool = db.Column(db.String(160))
    map_stats = db.relationship('MapStats', backref='match', lazy='dynamic')

    team1_score = db.Column(db.Integer, default=0)
    team2_score = db.Column(db.Integer, default=0)

    @staticmethod
    def create(user, team1_id, team2_id, team1_string, team2_string,
               max_maps, skip_veto, title, veto_mappool, server_id=None):
        rv = Match()
        rv.user_id = user.id
        rv.team1_id = team1_id
        rv.team2_id = team2_id
        rv.skip_veto = skip_veto
        rv.title = title
        rv.veto_mappool = ' '.join(veto_mappool)
        rv.server_id = server_id
        rv.max_maps = max_maps
        rv.api_key = ''.join(random.SystemRandom().choice(
            string.ascii_uppercase + string.digits) for _ in range(24))
        db.session.add(rv)
        return rv

    def get_status_string(self, show_winner=True):
        if self.pending():
            return 'Pending'
        elif self.live():
            team1_score, team2_score = self.get_current_score()
            return 'Live, {}:{}'.format(team1_score, team2_score)
        elif self.finished():
            t1score, t2score = self.get_current_score()
            min_score = min(t1score, t2score)
            max_score = max(t1score, t2score)
            score_string = '{}:{}'.format(max_score, min_score)

            if not show_winner:
                return 'Finished'
            elif self.winner == self.team1_id:
                return 'Won {} by {}'.format(score_string, self.get_team1().name)
            elif self.winner == self.team2_id:
                return 'Won {} by {}'.format(score_string, self.get_team2().name)
            else:
                return 'Tied {}'.format(score_string)

        else:
            return 'Cancelled'

    def get_vs_string(self):
        team1 = self.get_team1()
        team2 = self.get_team2()
        scores = self.get_current_score()

        str = '{} vs {} ({}:{})'.format(
            team1.get_name_url_html(), team2.get_name_url_html(), scores[0], scores[1])

        return Markup(str)

    def finalized(self):
        return self.cancelled or self.finished()

    def pending(self):
        return self.start_time is None and not self.cancelled

    def finished(self):
        return self.end_time is not None and not self.cancelled

    def live(self):
        return self.start_time is not None and self.end_time is None and not self.cancelled

    def get_server(self):
        return GameServer.query.filter_by(id=self.server_id).first()

    def get_current_score(self):
        if self.max_maps == 1:
            mapstat = self.map_stats.first()
            if not mapstat:
                return (0, 0)
            else:
                return (mapstat.team1_score, mapstat.team2_score)

        else:
            return (self.team1_score, self.team2_score)

    def send_to_server(self):
        server = GameServer.query.get(self.server_id)
        if not server:
            return False

        url = url_for('match.match_config', matchid=self.id,
                      _external=True, _scheme='http')
        # Remove http protocal since the get5 plugin can't parse args with the
        # : in them.
        url = url.replace("http://", "")
        url = url.replace("https://", "")

        loadmatch_response = server.send_rcon_command(
            'get5_loadmatch_url ' + url)

        server.send_rcon_command(
            'get5_web_api_key ' + self.api_key)

        if loadmatch_response:  # There should be no response
            return False

        return True

    def get_team1(self):
        return Team.query.get(self.team1_id)

    def get_team2(self):
        return Team.query.get(self.team2_id)

    def get_user(self):
        return User.query.get(self.user_id)

    def get_winner(self):
        if self.team1_score > self.team2_score:
            return self.get_team1()
        elif self.team2_score > self.team1_score:
            return self.get_team2()
        else:
            return None

    def get_loser(self):
        if self.team1_score > self.team2_score:
            return self.get_team2()
        elif self.team2_score > self.team1_score:
            return self.get_team1()
        else:
            return None

    def build_match_dict(self):
        d = {}
        d['matchid'] = str(self.id)
        d['match_title'] = self.title

        d['skip_veto'] = self.skip_veto
        if self.max_maps == 2:
            d['bo2_series'] = True
        else:
            d['maps_to_win'] = self.max_maps / 2 + 1

        def add_team_data(teamkey, teamid, matchtext):
            team = Team.query.get(teamid)
            if not team:
                return

            d[teamkey] = {}
            d[teamkey]['name'] = team.name
            d[teamkey]['tag'] = team.tag
            d[teamkey]['flag'] = team.flag.upper()
            d[teamkey]['logo'] = team.logo
            d[teamkey]['matchtext'] = matchtext
            d[teamkey]['players'] = filter(lambda x: x != '', team.auths)

        add_team_data('team1', self.team1_id, self.team1_string)
        add_team_data('team2', self.team2_id, self.team2_string)

        d['cvars'] = {}

        d['cvars']['get5_web_api_url'] = url_for(
            'home', _external=True, _scheme='http')

        if self.veto_mappool:
            d['maplist'] = []
            for map in self.veto_mappool.split():
                d['maplist'].append(map)

        return d

    def __repr__(self):
        return 'Match(id={})'.format(self.id)


class MapStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'))
    map_number = db.Column(db.Integer)
    map_name = db.Column(db.String(64))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    winner = db.Column(db.Integer, db.ForeignKey('team.id'))
    team1_score = db.Column(db.Integer, default=0)
    team2_score = db.Column(db.Integer, default=0)
    player_stats = db.relationship(
        'PlayerStats', backref='mapstats', lazy='dynamic')

    @staticmethod
    def get_or_create(match_id, map_number, map_name=''):
        match = Match.query.get(match_id)
        if match is None or map_number >= match.max_maps:
            return None

        rv = MapStats.query.filter_by(
            match_id=match_id, map_number=map_number).first()
        if rv is None:
            rv = MapStats()
            rv.match_id = match_id
            rv.map_number = map_number
            rv.map_name = map_name
            rv.start_time = datetime.datetime.utcnow()
            rv.team1_score = 0
            rv.team2_score = 0
            db.session.add(rv)
        return rv

    def __repr__(self):
        return 'MapStats(' + str(self.id) + ',' + str(self.map_name) + ')'


class PlayerStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'))
    map_id = db.Column(db.Integer, db.ForeignKey('map_stats.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    steam_id = db.Column(db.String(40))
    name = db.Column(db.String(40))
    kills = db.Column(db.Integer, default=0)
    deaths = db.Column(db.Integer, default=0)
    roundsplayed = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    flashbang_assists = db.Column(db.Integer, default=0)
    teamkills = db.Column(db.Integer, default=0)
    suicides = db.Column(db.Integer, default=0)
    headshot_kills = db.Column(db.Integer, default=0)
    damage = db.Column(db.Integer, default=0)
    bomb_plants = db.Column(db.Integer, default=0)
    bomb_defuses = db.Column(db.Integer, default=0)
    v1 = db.Column(db.Integer, default=0)
    v2 = db.Column(db.Integer, default=0)
    v3 = db.Column(db.Integer, default=0)
    v4 = db.Column(db.Integer, default=0)
    v5 = db.Column(db.Integer, default=0)
    k1 = db.Column(db.Integer, default=0)
    k2 = db.Column(db.Integer, default=0)
    k3 = db.Column(db.Integer, default=0)
    k4 = db.Column(db.Integer, default=0)
    k5 = db.Column(db.Integer, default=0)
    firstkill_t = db.Column(db.Integer, default=0)
    firstkill_ct = db.Column(db.Integer, default=0)
    firstdeath_t = db.Column(db.Integer, default=0)
    firstdeath_Ct = db.Column(db.Integer, default=0)

    def get_steam_url(self):
        return 'http://steamcommunity.com/profiles/{}'.format(self.steam_id)

    def get_rating(self):
        AverageKPR = 0.679
        AverageSPR = 0.317
        AverageRMK = 1.277
        KillRating = float(self.kills) / float(self.roundsplayed) / AverageKPR
        SurvivalRating = float(self.roundsplayed -
                               self.deaths) / self.roundsplayed / AverageSPR
        killcount = float(self.k1 + 4 * self.k2 + 9 *
                          self.k3 + 16 * self.k4 + 25 * self.k5)
        RoundsWithMultipleKillsRating = killcount / self.roundsplayed / AverageRMK
        rating = (KillRating + 0.7 * SurvivalRating +
                  RoundsWithMultipleKillsRating) / 2.7
        return rating

    def get_kdr(self):
        if self.deaths == 0:
            return float(self.kills)
        else:
            return float(self.kills) / self.deaths

    def get_hsp(self):
        if self.kills == 0:
            return 0.0
        else:
            return float(self.headshot_kills) / self.kills

    def get_adr(self):
        if self.roundsplayed == 0:
            return 0.0
        else:
            return float(self.damage) / self.roundsplayed

    def get_fpr(self):
        if self.roundsplayed == 0:
            return 0.0
        else:
            return float(self.kills) / self.roundsplayed

    @staticmethod
    def get_or_create(matchid, mapnumber, steam_id):
        mapstats = MapStats.get_or_create(matchid, mapnumber)
        if len(mapstats.player_stats.all()) >= 40:  # Cap on players per map
            return None

        rv = mapstats.player_stats.filter_by(steam_id=steam_id).first()

        if rv is None:
            rv = PlayerStats()
            rv.match_id = matchid
            rv.map_number = mapstats.id
            rv.steam_id = steam_id
            rv.map_id = mapstats.id
            db.session.add(rv)

        return rv


@cache.memoize(timeout=60 * 60 * 24)  # 1 day timeout
def get_steam_name(steam64):
    url = 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={}&steamids={}'
    url = url.format(app.config['STEAM_API_KEY'], steam64)
    response = requests.get(url)
    if response.status_code == 200:
        try:
            player_list = response.json()['response']['players']
            return player_list[0]['personaname']
        except (KeyError, IndexError):
            return None

    return None
