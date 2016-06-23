from get5 import app, db, flash_errors, config_setting
from models import GameServer
import util

from flask import Blueprint, request, render_template, flash, g, redirect

from wtforms import Form, validators, StringField, IntegerField


server_blueprint = Blueprint('server', __name__)


class ServerForm(Form):
    ip_string = StringField('Server IP',
                            validators=[
                                validators.required(),
                                validators.IPAddress()])

    port = IntegerField('Server port', default=27015,
                        validators=[validators.required()])

    rcon_password = StringField('RCON password',
                                validators=[
                                    validators.required(),
                                    validators.Length(min=-1, max=GameServer.rcon_password.type.length)])


@server_blueprint.route('/server/create', methods=['GET', 'POST'])
def server_create():
    if not g.user:
        return redirect('/login')

    form = ServerForm(request.form)
    if request.method == 'POST':
        num_servers = g.user.servers.count()
        max_servers = config_setting('USER_MAX_SERVERS', 0)
        if max_servers >= 0 and num_servers >= max_servers and not g.user.admin:
            flash('You already have the maximum number of servers ({}) stored'.format(
                num_servers))

        elif form.validate():
            mock = config_setting('TESTING', False)

            data = form.data
            server = GameServer.create(
                g.user, data['ip_string'], data['port'], data['rcon_password'])

            if mock or util.check_server_connection(server):
                db.session.commit()
                app.logger.info(
                    'User {} created server {}'.format(g.user.id, server.id))
                return redirect('/myservers')
            else:
                db.session.remove()
                flash('Failed to connect to server')

        else:
            flash_errors(form)

    return render_template('server_create.html', user=g.user, form=form, edit=False)


@server_blueprint.route('/server/<int:serverid>/edit', methods=['GET', 'POST'])
def server_edit(serverid):
    server = GameServer.query.get_or_404(serverid)
    is_owner = (g.user.id == server.user_id)
    if not is_owner:
        return 'Not your server', 400

    form = ServerForm(request.form, ip_string=server.ip_string,
                      port=server.port, rcon_password=server.rcon_password)

    if request.method == 'POST':
        if form.validate():
            mock = app.config['TESTING']

            data = form.data
            server.ip_string = data['ip_string']
            server.port = data['port']
            server.rcon_password = data['rcon_password']

            if mock or util.check_server_connection(server):
                db.session.commit()
                return redirect('/myservers')
            else:
                db.session.remove()
                flash('Failed to connect to server')

        else:
            flash_errors(form)

    return render_template('server_create.html', user=g.user, form=form, edit=True)


@server_blueprint.route('/server/<int:serverid>/delete', methods=['GET'])
def server_delete(serverid):
    server = GameServer.query.get_or_404(serverid)
    is_owner = (g.user is not None) and (g.user.id == server.user_id)
    if not is_owner:
        return 'Not your server', 400

    if server.in_use:
        return 'Cannot delete when in use', 400

    matches = g.user.matches.filter_by(server_id=serverid)
    for m in matches:
        m.server_id = None

    GameServer.query.filter_by(id=serverid).delete()
    db.session.commit()
    return redirect('myservers')


@server_blueprint.route("/myservers")
def myservers():
    if not g.user:
        return redirect('/login')

    servers = GameServer.query.filter_by(
        user_id=g.user.id).order_by(-GameServer.id).limit(50)

    return render_template('servers.html', user=g.user, servers=servers)
