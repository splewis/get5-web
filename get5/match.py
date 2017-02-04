from flask import Blueprint, request, render_template, flash, g, redirect, jsonify, Markup

import steamid
import get5
from get5 import app, db, BadRequestError, config_setting
from models import User, Team, Match, GameServer
import util

from wtforms import (
    Form, widgets, validators,
    StringField, RadioField,
    SelectField, ValidationError, SelectMultipleField)

match_blueprint = Blueprint('match', __name__)


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


def different_teams_validator(form, field):
    if form.team1_id.data == form.team2_id.data:
        raise ValidationError('Teams cannot be equal')


def mappool_validator(form, field):
    if 'preset' in form.series_type.data and len(form.veto_mappool.data) != 1:
        raise ValidationError(
            'You must have exactly 1 map selected to do a bo1 with a preset map')

    max_maps = 1
    try:
        max_maps = int(form.series_type.data[2])
    except ValueError:
        max_maps = 1

    if len(form.veto_mappool.data) < max_maps:
        raise ValidationError(
            'You must have at least {} maps selected to do a Bo{}'.format(max_maps, max_maps))


class MatchForm(Form):
    server_id = SelectField('Server', coerce=int,
                            validators=[validators.required()])

    match_title = StringField('Match title text',
                              default='Map {MAPNUMBER} of {MAXMAPS}',
                              validators=[validators.Length(min=-1, max=Match.title.type.length)])

    series_type = RadioField('Series type',
                             validators=[validators.required()],
                             default='bo1',
                             choices=[
                                 ('bo1-preset', 'Bo1 with preset map'),
                                 ('bo1', 'Bo1 with map vetoes'),
                                 ('bo2', 'Bo2 with map vetoes'),
                                 ('bo3', 'Bo3 with map vetoes'),
                                 ('bo5', 'Bo5 with map vetoes'),
                                 ('bo7', 'Bo7 with map vetoes'),
                             ])

    team1_id = SelectField('Team 1', coerce=int,
                           validators=[validators.required()])

    team1_string = StringField('Team 1 title text',
                               default='',
                               validators=[validators.Length(min=-1,
                                                             max=Match.team1_string.type.length)])

    team2_id = SelectField('Team 2', coerce=int,
                           validators=[validators.required(), different_teams_validator])

    team2_string = StringField('Team 2 title text',
                               default='',
                               validators=[validators.Length(min=-1,
                                                             max=Match.team2_string.type.length)])

    mapchoices = config_setting('MAPLIST')
    default_mapchoices = config_setting('DEFAULT_MAPLIST')
    veto_mappool = MultiCheckboxField('Map pool',
                                      choices=map(lambda name: (
                                          name, util.format_mapname(name)), mapchoices),
                                      default=default_mapchoices,
                                      validators=[mappool_validator],
                                      )

    def add_teams(self, user):
        if self.team1_id.choices is None:
            self.team1_id.choices = []

        if self.team2_id.choices is None:
            self.team2_id.choices = []

        team_tuples = [(team.id, team.name) for team in user.teams]
        self.team1_id.choices += team_tuples
        self.team2_id.choices += team_tuples

    def add_servers(self, user):
        if self.server_id.choices is None:
            self.server_id.choices = []

        server_tuples = [(server.id, server.get_display())
                         for server in user.servers if not server.in_use]
        self.server_id.choices += server_tuples


@match_blueprint.route('/match/create', methods=['GET', 'POST'])
def match_create():
    if not g.user:
        return redirect('/login')

    form = MatchForm(request.form)
    form.add_teams(g.user)
    form.add_teams(User.get_public_user())
    form.add_servers(g.user)

    if request.method == 'POST':
        num_matches = g.user.matches.count()
        max_matches = config_setting('USER_MAX_MATCHES')

        if max_matches >= 0 and num_matches >= max_matches and not g.user.admin:
            flash('You already have the maximum number of matches ({}) created'.format(
                num_matches))

        if form.validate():
            mock = config_setting('TESTING')

            server = GameServer.query.get_or_404(form.data['server_id'])

            match_on_server = g.user.matches.filter_by(
                server_id=server.id, end_time=None, cancelled=False).first()

            server_avaliable = False
            json_reply = None

            if g.user.id != server.user_id:
                server_avaliable = False
                message = 'This is not your server!'
            elif match_on_server is not None:
                server_avaliable = False
                message = 'Match {} is already using this server'.format(
                    match_on_server.id)
            elif mock:
                server_avaliable = True
                message = 'Success'
            else:
                json_reply, message = util.check_server_avaliability(
                    server)
                server_avaliable = (json_reply is not None)

            if server_avaliable:
                skip_veto = 'preset' in form.data['series_type']
                try:
                    max_maps = int(form.data['series_type'][2])
                except ValueError:
                    max_maps = 1

                match = Match.create(
                    g.user, form.data['team1_id'], form.data['team2_id'],
                    form.data['team1_string'], form.data['team2_string'],
                    max_maps, skip_veto, form.data['match_title'],
                    form.data['veto_mappool'], form.data['server_id'])

                # Save plugin version data if we have it
                if json_reply and 'plugin_version' in json_reply:
                    match.plugin_version = json_reply['plugin_version']
                else:
                    match.plugin_version = 'unknown'

                server.in_use = True

                db.session.commit()
                app.logger.info('User {} created match {}, assigned to server {}'
                                .format(g.user.id, match.id, server.id))

                if mock or match.send_to_server():
                    return redirect('/mymatches')
                else:
                    flash('Failed to load match configs on server')
            else:
                flash(message)

        else:
            get5.flash_errors(form)

    return render_template('match_create.html', form=form, user=g.user, teams=g.user.teams,
                            match_text_option=config_setting('CREATE_MATCH_TITLE_TEXT'))


@match_blueprint.route('/match/<int:matchid>')
def match(matchid):
    match = Match.query.get_or_404(matchid)
    team1 = Team.query.get_or_404(match.team1_id)
    team2 = Team.query.get_or_404(match.team2_id)
    map_stat_list = match.map_stats.all()

    is_owner = False
    has_admin_access = False

    if g.user:
        is_owner = (g.user.id == match.user_id)
        has_admin_access = is_owner or (config_setting(
            'ADMINS_ACCESS_ALL_MATCHES') and g.user.admin)

    return render_template('match.html', user=g.user, admin_access=has_admin_access,
                           match=match, team1=team1, team2=team2,
                           map_stat_list=map_stat_list)


@match_blueprint.route('/match/<int:matchid>/config')
def match_config(matchid):
    match = Match.query.get_or_404(matchid)
    dict = match.build_match_dict()
    json_text = jsonify(dict)
    return json_text


def admintools_check(user, match):
    if user is None:
        raise BadRequestError('You do not have access to this page')

    grant_admin_access = user.admin and get5.config_setting(
        'ADMINS_ACCESS_ALL_MATCHES')
    if user.id != match.user_id and not grant_admin_access:
        raise BadRequestError('You do not have access to this page')

    if match.finished():
        raise BadRequestError('Match already finished')

    if match.cancelled:
        raise BadRequestError('Match is cancelled')


@match_blueprint.route('/match/<int:matchid>/cancel')
def match_cancel(matchid):
    match = Match.query.get_or_404(matchid)
    admintools_check(g.user, match)

    match.cancelled = True
    server = GameServer.query.get(match.server_id)
    if server:
        server.in_use = False

    db.session.commit()

    try:
        server.send_rcon_command('get5_endmatch', raise_errors=True)
    except util.RconError as e:
        flash('Failed to cancel match: ' + str(e))

    return redirect('/mymatches')


@match_blueprint.route('/match/<int:matchid>/rcon')
def match_rcon(matchid):
    match = Match.query.get_or_404(matchid)
    admintools_check(g.user, match)

    command = request.values.get('command')
    server = GameServer.query.get_or_404(match.server_id)

    if command:
        try:
            rcon_response = server.send_rcon_command(
                command, raise_errors=True)
            if rcon_response:
                rcon_response = Markup(rcon_response.replace('\n', '<br>'))
            else:
                rcon_response = 'No output'
            flash(rcon_response)
        except util.RconError as e:
            print(e)
            flash('Failed to send command: ' + str(e))

    return redirect('/match/{}'.format(matchid))


@match_blueprint.route('/match/<int:matchid>/pause')
def match_pause(matchid):
    match = Match.query.get_or_404(matchid)
    admintools_check(g.user, match)
    server = GameServer.query.get_or_404(match.server_id)

    try:
        server.send_rcon_command('sm_pause', raise_errors=True)
        flash('Paused match')
    except util.RconError as e:
        flash('Failed to send pause command: ' + str(e))

    return redirect('/match/{}'.format(matchid))


@match_blueprint.route('/match/<int:matchid>/unpause')
def match_unpause(matchid):
    match = Match.query.get_or_404(matchid)
    admintools_check(g.user, match)
    server = GameServer.query.get_or_404(match.server_id)

    try:
        server.send_rcon_command('sm_unpause', raise_errors=True)
        flash('Unpaused match')
    except util.RconError as e:
        flash('Failed to send unpause command: ' + str(e))

    return redirect('/match/{}'.format(matchid))


@match_blueprint.route('/match/<int:matchid>/adduser')
def match_adduser(matchid):
    match = Match.query.get_or_404(matchid)
    admintools_check(g.user, match)
    server = GameServer.query.get_or_404(match.server_id)
    team = request.values.get('team')
    if not team:
        raise BadRequestError('No team specified')

    auth = request.values.get('auth')
    suc, new_auth = steamid.auth_to_steam64(auth)
    if suc:
        try:
            command = 'get5_addplayer {} {}'.format(new_auth, team)
            response = server.send_rcon_command(command, raise_errors=True)
            flash(response)
        except util.RconError as e:
            flash('Failed to send command: ' + str(e))

    else:
        flash('Invalid steamid: {}'.format(auth))

    return redirect('/match/{}'.format(matchid))


# @match_blueprint.route('/match/<int:matchid>/sendconfig')
# def match_sendconfig(matchid):
#     match = Match.query.get_or_404(matchid)
#     admintools_check(g.user, match)
#     server = GameServer.query.get_or_404(match.server_id)

#     try:
#         server.send_rcon_command('mp_unpause_match', raise_errors=True)
#         flash('Unpaused match')
#     except util.RconError as e:
#         flash('Failed to send unpause command: ' + str(e))

#     return redirect('/match/{}'.format(matchid))


@match_blueprint.route('/match/<int:matchid>/backup', methods=['GET'])
def match_backup(matchid):
    match = Match.query.get_or_404(matchid)
    admintools_check(g.user, match)
    server = GameServer.query.get_or_404(match.server_id)
    file = request.values.get('file')

    if not file:
        # List backup files
        backup_response = server.send_rcon_command(
            'get5_listbackups ' + str(matchid))
        if backup_response:
            backup_files = sorted(backup_response.split('\n'))
        else:
            backup_files = []

        return render_template('match_backup.html', user=g.user,
                               match=match, backup_files=backup_files)

    else:
        # Restore the backup file
        command = 'get5_loadbackup {}'.format(file)
        response = server.send_rcon_command(command)
        if response:
            flash('Restored backup file {}'.format(file))
        else:
            flash('Failed to restore backup file {}'.format(file))
            return redirect('match/{}/backup'.format(matchid))

        return redirect('match/{}'.format(matchid))


@match_blueprint.route("/matches")
def matches():
    page = util.as_int(request.values.get('page'), on_fail=1)
    matches = Match.query.order_by(-Match.id).filter_by(
        cancelled=False).paginate(page, 20)
    return render_template('matches.html', user=g.user, matches=matches,
                           my_matches=False, all_matches=True, page=page)


@match_blueprint.route("/matches/<int:userid>")
def matches_user(userid):
    user = User.query.get_or_404(userid)
    page = util.as_int(request.values.get('page'), on_fail=1)
    matches = user.matches.order_by(-Match.id).paginate(page, 20)
    is_owner = (g.user is not None) and (userid == g.user.id)
    return render_template('matches.html', user=g.user, matches=matches,
                           my_matches=is_owner, all_matches=False, match_owner=user, page=page)


@match_blueprint.route("/mymatches")
def mymatches():
    if not g.user:
        return redirect('/login')

    return redirect('/matches/' + str(g.user.id))
