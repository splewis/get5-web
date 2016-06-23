from get5 import app, db, flash_errors, config_setting
from models import User, Team

import countries
import util
import steamid

from flask import Blueprint, request, render_template, flash, g, redirect, url_for

from wtforms import (
    Form, validators,
    StringField, BooleanField,
    SelectField, ValidationError)

team_blueprint = Blueprint('team', __name__)


def valid_auth(form, field):
    # Ignore empty data fields
    if field.data is None or field.data == '':
        return

    # Otherwise validate and coerce to steam64
    suc, newauth = steamid.auth_to_steam64(field.data)
    if suc:
        field.data = newauth
    else:
        raise ValidationError('Invalid Steam ID')


class TeamForm(Form):
    name = StringField('Team Name', validators=[
                       validators.required(), validators.Length(min=-1, max=40)])

    choices = [('', 'None')] + countries.country_choices
    country_flag = SelectField('Country Flag', choices=choices)

    logo = StringField('Logo Name')
    auth1 = StringField('Player 1', validators=[valid_auth])
    auth2 = StringField('Player 2', validators=[valid_auth])
    auth3 = StringField('Player 3', validators=[valid_auth])
    auth4 = StringField('Player 4', validators=[valid_auth])
    auth5 = StringField('Player 5', validators=[valid_auth])
    auth6 = StringField('Player 6', validators=[valid_auth])
    auth7 = StringField('Player 7', validators=[valid_auth])
    public_team = BooleanField('Public Team')

    def get_auth_list(self):
        auths = []
        for i in range(1, 8):
            key = 'auth{}'.format(i)
            auths.append(self.data[key])

        return auths


@team_blueprint.route('/team/create', methods=['GET', 'POST'])
def team_create():
    if not g.user:
        return redirect('/login')

    form = TeamForm(request.form)

    if request.method == 'POST':
        num_teams = g.user.teams.count()
        max_teams = config_setting('USER_MAX_TEAMS', 0)
        if max_teams >= 0 and num_teams >= max_teams and not g.user.admin:
            flash(
                'You already have the maximum number of teams ({}) stored'.format(num_teams))

        elif form.validate():
            data = form.data
            public_team = data['public_team']
            auths = form.get_auth_list()

            team = Team.create(g.user, data['name'],
                               data['country_flag'], data['logo'], auths, public_team)

            db.session.commit()
            app.logger.info(
                'User {} created team {}'.format(g.user.id, team.id))

            return redirect('/teams/{}'.format(team.user_id))

        else:
            get5.flash_errors(form)

    return render_template('team_create.html', user=g.user, form=form,
                           edit=False, is_admin=g.user.admin)


@team_blueprint.route('/team/<int:teamid>', methods=['GET'])
def team(teamid):
    team = Team.query.get_or_404(teamid)
    return render_template('team.html', user=g.user, team=team)


@team_blueprint.route('/team/<int:teamid>/edit', methods=['GET', 'POST'])
def team_edit(teamid):
    team = Team.query.get_or_404(teamid)
    if not team.can_edit(g.user):
        return 'Not your team', 400

    public_team = (team.user_id == User.get_public_user().id)

    form = TeamForm(
        request.form,
        name=team.name,
        country_flag=team.flag,
        logo=team.logo,
        auth1=team.auths[0],
        auth2=team.auths[1],
        auth3=team.auths[2],
        auth4=team.auths[3],
        auth5=team.auths[4],
        auth6=team.auths[5],
        auth7=team.auths[6],
        public_team=public_team)

    if request.method == 'GET':
        return render_template('team_create.html', user=g.user, form=form,
                               edit=True, is_admin=g.user.admin)

    elif request.method == 'POST':
        if request.method == 'POST':
            if form.validate():
                data = form.data
                team.set_data(data['name'], data['country_flag'],
                              data['logo'], form.get_auth_list())
                db.session.commit()
                return redirect('/teams/{}'.format(team.user_id))
            else:
                flash_errors(form)

    return render_template('team_create.html', user=g.user, form=form, edit=True)


@team_blueprint.route('/team/<int:teamid>/delete')
def team_delete(teamid):
    team = Team.query.get_or_404(teamid)
    if not team.can_delete(g.user):
        return 'Cannot delete this team', 400

    if Team.query.filter_by(id=teamid).delete():
        db.session.commit()

    return redirect('/myteams')


@team_blueprint.route('/teams/<int:userid>', methods=['GET'])
def teams_user(userid):
    user = User.query.get_or_404(userid)
    page = util.as_int(request.values.get('page'), on_fail=1)
    my_teams = (g.user is not None and userid == g.user.id)
    teams = user.teams.paginate(page, 20)
    return render_template('teams.html', user=g.user, teams=teams, my_teams=my_teams, page=page, owner=user)


@team_blueprint.route('/teams/public', methods=['GET'])
def teams_public():
    return redirect(url_for('team.teams_user', userid=User.get_public_user().id))


@team_blueprint.route('/myteams', methods=['GET'])
def myteams():
    if not g.user:
        return redirect('/login')

    return redirect('/teams/' + str(g.user.id))
