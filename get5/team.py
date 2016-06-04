from get5 import app, db, flash_errors
from models import User, Team

import countries
import util
import steamid

from flask import Blueprint, request, render_template, flash, g, redirect

from wtforms import (
    Form, validators,
    StringField,
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
        teams = g.user.teams.all()
        if len(teams) >= 100:
            flash('You already have the maximum number of teams (100) stored')

        elif form.validate():
            data = form.data
            auths = form.get_auth_list()

            team = Team.create(g.user, data['name'],
                data['country_flag'], data['logo'], auths)

            db.session.commit()
            app.logger.info(
                'User {} created team {}'.format(g.user.id, team.id))
            return redirect('/myteams')

        else:
            get5.flash_errors(form)

    return render_template('team_create.html', user=g.user, form=form, edit=False)


@team_blueprint.route('/team/<int:teamid>', methods=['GET'])
def team(teamid):
    team = Team.query.get_or_404(teamid)
    return render_template('team.html', user=g.user, team=team)


@team_blueprint.route('/team/<int:teamid>/edit', methods=['GET', 'POST'])
def team_edit(teamid):
    team = Team.query.get_or_404(teamid)
    is_owner = (g.user.id == team.user_id)
    if not is_owner:
        return 'Not your team', 400

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
        auth7=team.auths[6])

    if request.method == 'GET':
        return render_template('team_create.html', user=g.user, form=form, owner=is_owner, edit=True)

    elif request.method == 'POST':
        if request.method == 'POST':
            if form.validate():
                data = form.data
                team.set_data(data['name'], data['country_flag'],
                              data['logo'], form.get_auth_list())
                db.session.commit()
                return redirect('/myteams')
            else:
                flash_errors(form)

    return render_template('team_create.html', user=g.user, form=form, owner=is_owner, edit=True)


@team_blueprint.route('/teams/<int:userid>', methods=['GET'])
def teams_user(userid):
    user = User.query.get_or_404(userid)
    page = util.as_int(request.values.get('page'), on_fail=1)
    my_teams = (g.user is not None and userid == g.user.id)
    teams = user.teams.paginate(page, 20)
    return render_template('teams.html', user=g.user, teams=teams, my_teams=my_teams, page=page)


@team_blueprint.route('/myteams', methods=['GET'])
def myteams():
    if not g.user:
        return redirect('/login')

    return redirect('/teams/' + str(g.user.id))
