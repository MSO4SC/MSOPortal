"""
Keyrock (Fiware) OAuth2 backend
"""
from urllib.parse import urlencode
from requests import HTTPError

from six.moves.urllib.parse import urljoin

from social_core.backends.oauth import BaseOAuth2
from social_core.exceptions import AuthFailed

from django.conf import settings

import base64


class KeyrockOAuth2(BaseOAuth2):
    """Keyrock OAuth authentication backend"""
    name = 'fiware'
    AUTHORIZATION_URL = urljoin(
        settings.FIWARE_IDM_ENDPOINT, '/oauth2/authorize')
    ACCESS_TOKEN_URL = urljoin(settings.FIWARE_IDM_ENDPOINT, '/oauth2/token')
    #LOGOUT_URL = urljoin(settings.FIWARE_IDM_ENDPOINT, '/auth/logout')
    ACCESS_TOKEN_METHOD = 'POST'

    REDIRECT_STATE = False

    EXTRA_DATA = [
        ('displayName', 'id'),
        ('id', 'uid'),
        ('email', 'email'),
        ('displayName', 'username'),
        ('roles', 'roles'),
        ('refresh_token', 'refresh_token'),
        ('expires_in', 'expires_in'),
        ('organizations', 'organizations')
    ]

    def get_user_id(self, details, response):
        # ---- v5.4.0
        # {'access_token': '53ERoBZXTDzjDrvSMAzEbLPW9JWX6f',
        #  'expires_in': 3600,
        #  'token_type': 'Bearer',
        #  'state': 'IVbDtzMyx9fZib77Eiwqb4jtBwFLxgt0',
        #  'scope': 'all_info',
        #  'refresh_token': 'VGyiMKgKMISjmUraVmMb8ALIrtYb3u',
        #  'organizations': [],
        #  'displayName': 'j*******',
        #  'roles': [{'name': 'Provider', 'id': 'provider'}],
        #  'app_id': '0db45bbbfe05409685c2e043892d7d00',
        #  'isGravatarEnabled': False,
        #  'email': 'j*****.c******@atos.net',
        #  'id': 'j*******'}
        # ---- v7.0.0
        # {'access_token': '4bb8dee1ea3e1f4523623af71d52e265f05304f3',
        #  'token_type': 'Bearer',
        #  'expires_in': 3599,
        #  'refresh_token': 'd200de308c8694a3edde6afe9e19c89196754d29',
        #  'organizations': [],
        #  'displayName': 'jcarnero',
        #  'roles': [
        #      {'id': 'b6208353-cd6d-4443-ad55-2a34b4c6df4f', 'name': 'Developer'},
        #      {'id': '8a2fc748-d7d9-48b9-be17-2cad3c1140c3', 'name': 'User'}],
        #  'app_id': '390f1cbf-0582-4d65-aa93-531c3aed9a3f',
        #  'email': 'javier.carnero@atos.net',
        #  'id': 'f8297ebc-4a60-4a43-9d74-cec472bbc01f',
        #  'app_azf_domain': ''})
        return response['displayName'].replace('-', '_')

    def get_user_details(self, response):
        """Return user details from FI-WARE account"""
        # ---- v5.4.0
        # {'access_token': 'uN1mFJKd9m0pGMdLyRFdvew5VLFMs3',
        #  'expires_in': 3600,
        #  'token_type': 'Bearer',
        #  'state': 'HuQGmypp6QjjIcp4Izw097egFV1wd55f',
        #  'scope': 'all_info',
        #  'refresh_token': '35pOUhNnaUOEAicjyF4C8F9ZAa3jG8',
        #  'organizations': [],
        #  'displayName': 'j*******',
        #  'roles': [{'name': 'Provider', 'id': 'provider'}],
        #  'app_id': '0db45bbbfe05409685c2e043892d7d00',
        #  'isGravatarEnabled': False,
        #  'email': 'j*****.c******@atos.net',
        #  'id': 'j*******'}
        # ---- v7.0.0
        # {'access_token': '4bb8dee1ea3e1f4523623af71d52e265f05304f3',
        #  'token_type': 'Bearer',
        #  'expires_in': 3599,
        #  'refresh_token': 'd200de308c8694a3edde6afe9e19c89196754d29',
        #  'organizations': [],
        #  'displayName': 'jcarnero',
        #  'roles': [
        #      {'id': 'b6208353-cd6d-4443-ad55-2a34b4c6df4f', 'name': 'Developer'},
        #      {'id': '8a2fc748-d7d9-48b9-be17-2cad3c1140c3', 'name': 'User'}],
        #  'app_id': '390f1cbf-0582-4d65-aa93-531c3aed9a3f',
        #  'email': 'javier.carnero@atos.net',
        #  'id': 'f8297ebc-4a60-4a43-9d74-cec472bbc01f',
        #  'app_azf_domain': ''}
        return {'username': response.get('displayName').replace('-', '_'),
                'email': response.get('email') or '',
                'roles': response.get('roles') or []}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        url = urljoin(settings.FIWARE_IDM_ENDPOINT, '/user?' + urlencode({
            'access_token': access_token
        }))
        # ---- v5.4.0
        # {'organizations': [],
        #  'displayName': 'j*******',
        #  'roles': [{'name': 'Provider', 'id': 'provider'}],
        #  'app_id': '0db45bbbfe05409685c2e043892d7d00',
        #  'isGravatarEnabled': False,
        #  'email': 'j*****.c******@atos.net',
        #  'id': 'j*******'}
        # ---- v7.0.0
        # {'organizations': [],
        #  'displayName': 'jcarnero',
        #  'roles': [
        #     {'id': 'b6208353-cd6d-4443-ad55-2a34b4c6df4f', 'name': 'Developer'},
        #     {'id': '8a2fc748-d7d9-48b9-be17-2cad3c1140c3', 'name': 'User'}],
        #  'app_id': '390f1cbf-0582-4d65-aa93-531c3aed9a3f',
        #  'email': 'javier.carnero@atos.net',
        #  'id': 'f8297ebc-4a60-4a43-9d74-cec472bbc01f',
        #  'app_azf_domain': ''}
        return self.get_json(url)

    def auth_headers(self):
        response = super(KeyrockOAuth2, self).auth_headers()

        keys = settings.SOCIAL_AUTH_FIWARE_KEY + \
            ":" + settings.SOCIAL_AUTH_FIWARE_SECRET
        authorization_basic = base64.b64encode(
            keys.encode('ascii')).decode('ascii')
        response['Authorization'] = 'Basic ' + authorization_basic

        return response

    def auth_complete_params(self, state=None):
        # response = super(KeyrockOAuth2, self).auth_complete_params(state)
        # response['grant_type'] = 'authorization_code' + \
        #     '&code=' + response['code'] + \
        #     '&redirect_uri=' + response['redirect_uri']
        # return response

        return {
            'grant_type': 'authorization_code',  # request auth code
            'code': self.data.get('code', ''),  # server response code
            'redirect_uri': self.get_redirect_uri(state)
        }
