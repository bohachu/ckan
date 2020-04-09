# encoding: utf-8

import logging, datetime

from zope.interface import implements
from repoze.who.interfaces import IAuthenticator

from ckan.model import User

log = logging.getLogger(__name__)
user_login_fail_mapping = {}

class UsernamePasswordAuthenticator(object):
    implements(IAuthenticator)

    def check_if_user_has_been_lock(self, user_name):
        if user_name not in user_login_fail_mapping:
            return False
        user_login_fail_info = user_login_fail_mapping.get(user_name)
        if user_login_fail_info['count'] >= 3 and user_login_fail_info['unlock_time'] > datetime.datetime.now():
            return True
        return False

    def add_user_to_login_fail_mapping(self, user_name):
        user_login_fail_info = {'count': 1, 'unlock_time': datetime.datetime.now() + datetime.timedelta(seconds=60)}
        if user_name in user_login_fail_mapping:
            user_login_fail_info = user_login_fail_mapping.get(user_name)
            user_login_fail_info['count'] += 1
            user_login_fail_info['unlock_time'] = datetime.datetime.now() + datetime.timedelta(seconds=60)
        user_login_fail_mapping[user_name] = user_login_fail_info

    def authenticate(self, environ, identity):
        if not ('login' in identity and 'password' in identity):
            return None

        login = identity['login']
        if self.check_if_user_has_been_lock(login):
            print 'Login failed - username ' + login + ' been locked'
            return None
        print login + "----------------> no block"
        user = User.by_name(login)

        if user is None:
            log.debug('Login failed - username %r not found', login)
        elif not user.is_active():
            log.debug('Login as %r failed - user isn\'t active', login)
        elif not user.validate_password(identity['password']):
            log.debug('Login as %r failed - password not valid', login)
        else:
            if login in user_login_fail_mapping:
                del user_login_fail_mapping[login]
            return user.name

        self.add_user_to_login_fail_mapping(login)
        return None
