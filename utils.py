import json
import requests
from models import RoleEnum
from models import User
from flask import current_app, g
from exceptions import KeycloakUserNotFound, KeycloakIdNotFound
from werkzeug.exceptions import BadRequest, Forbidden


OIDC_CONFIG = None


def check_owners_on_keycloak(usernames):
    global OIDC_CONFIG

    if OIDC_CONFIG is None:
        with open(current_app.config['OIDC_CLIENT_SECRETS']) as json_file:
            OIDC_CONFIG = json.load(json_file)

    issuer = OIDC_CONFIG['web']['issuer']
    token_uri = OIDC_CONFIG['web']['token_uri']
    admin_uri = OIDC_CONFIG['web']['admin_uri']
    client_id = OIDC_CONFIG['web']['client_id']
    client_secret = OIDC_CONFIG['web']['client_secret']

    token_res = requests.post(token_uri, data={
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    }).json()
    access_token = token_res['access_token']

    for username in usernames:
        res = requests.get(f'{admin_uri}/users?username={username}',
                           headers={
                               'Accept': 'application/json',
                               'Authorization': f'Bearer {access_token}',
                           }).json()
        if not res:
            raise KeycloakUserNotFound(username)

def check_user_role(min_role):
    # Get user uid in keycloak from token
    kc_user_id = g.oidc_token_info['sub']
    try:
        kc_user = get_user_from_keycloak(kc_user_id)
        name = kc_user['username']
    except KeycloakIdNotFound as e:
        raise BadRequest(description=f'{e.missing_id} is an invalid id.')
    # Look for user role
    user = User.query.filter_by(name=name).one_or_none()

    # TODO: check does not always work (ie admin could match but not superadmin)
    if user.role != min_role:
        raise Forbidden

def get_user_from_keycloak(id):
    global OIDC_CONFIG

    if OIDC_CONFIG is None:
        with open(current_app.config['OIDC_CLIENT_SECRETS']) as json_file:
            OIDC_CONFIG = json.load(json_file)

    issuer = OIDC_CONFIG['web']['issuer']
    token_uri = OIDC_CONFIG['web']['token_uri']
    admin_uri = OIDC_CONFIG['web']['admin_uri']
    client_id = OIDC_CONFIG['web']['client_id']
    client_secret = OIDC_CONFIG['web']['client_secret']

    token_res = requests.post(token_uri, data={
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    }).json()
    access_token = token_res['access_token']

    res = requests.get(f'{admin_uri}/users/{id}',
                        headers={
                            'Accept': 'application/json',
                            'Authorization': f'Bearer {access_token}',
                        }).json()
    if not res:
        raise KeycloakIdNotFound(id)

    return res
