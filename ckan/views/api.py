# encoding: utf-8

import cgi
import logging

from flask import Blueprint, request, make_response

from ckan.common import json


log = logging.getLogger(__name__)

CONTENT_TYPES = {
    u'text': u'text/plain;charset=utf-8',
    u'html': u'text/html;charset=utf-8',
    u'json': u'application/json;charset=utf-8',
    u'javascript': u'application/javascript;charset=utf-8',
}


API_DEFAULT_VERSION = 3
API_MAX_VERSION = 3


api = Blueprint(u'api', __name__, url_prefix=u'/api')


def _finish(status_int, response_data=None,
            content_type=u'text', headers=None):
    u'''When a controller method has completed, call this method
    to prepare the response.

    :param status_int: The HTTP status code to return
    :type status_int: int
    :param response_data: The body of the response
    :type response_data: object if content_type is `text`, a string otherwise
    :param content_type: One of `text`, `html` or `json`. Defaults to `text`
    :type content_type: string
    :param headers: Extra headers to serve with the response
    :type headers: dict

    :rtype: response object. Return this value from the view function
        e.g. return _finish(404, 'Dataset not found')
    '''
    assert(isinstance(status_int, int))
    response_msg = u''
    if headers is None:
        headers = {}
    if response_data is not None:
        headers[u'Content-Type'] = CONTENT_TYPES[content_type]
        if content_type == u'json':
            response_msg = json.dumps(
                response_data,
                for_json=True)  # handle objects with for_json methods
        else:
            response_msg = response_data
        # Support "JSONP" callback.
        if (status_int == 200 and u'callback' in request.args and
                request.method == u'GET'):
            # escape callback to remove '<', '&', '>' chars
            callback = cgi.escape(request.args[u'callback'])
            response_msg = _wrap_jsonp(callback, response_msg)
            headers[u'Content-Type'] = CONTENT_TYPES[u'javascript']
    return make_response((response_msg, status_int, headers))


def _finish_ok(response_data=None,
               content_type=u'json',
               resource_location=None):
    u'''If a controller method has completed successfully then
    calling this method will prepare the response.

    :param response_data: The body of the response
    :type response_data: object if content_type is `text`, a string otherwise
    :param content_type: One of `text`, `html` or `json`. Defaults to `json`
    :type content_type: string
    :param resource_location: Specify this if a new resource has just been
        created and you need to add a `Location` header
    :type headers: string

    :rtype: response object. Return this value from the view function
        e.g. return _finish_ok(pkg_dict)
    '''
    status_int = 200
    headers = None
    if resource_location:
        status_int = 201
        try:
            resource_location = str(resource_location)
        except Exception, inst:
            msg = \
                u"Couldn't convert '%s' header value '%s' to string: %s" % \
                (u'Location', resource_location, inst)
            raise Exception(msg)
        headers = {u'Location': resource_location}

    return _finish(status_int, response_data, content_type, headers)


def _wrap_jsonp(callback, response_msg):
    return u'{0}({1});'.format(callback, response_msg)


def get_api(ver=1):
    response_data = {
        u'version': ver
    }
    return _finish_ok(response_data)


def dataset_autocomplete(ver=API_REST_DEFAULT_VERSION):
    q = request.args.get(u'incomplete', u'')
    limit = request.args.get(u'limit', 10)
    package_dicts = []
    if q:
        context = {u'model': model, u'session': model.Session,
                   u'user': g.user, u'auth_user_obj': g.userobj}

        data_dict = {u'q': q, u'limit': limit}

        package_dicts = get_action(
            u'package_autocomplete')(context, data_dict)

    resultSet = {u'ResultSet': {u'Result': package_dicts}}
    return _finish_ok(resultSet)


def tag_autocomplete(ver=API_REST_DEFAULT_VERSION):
    q = request.args.get(u'incomplete', u'')
    limit = request.args.get(u'limit', 10)
    vocab = request.args.get(u'vocabulary_id', u'')
    tag_names = []
    if q:
        context = {u'model': model, u'session': model.Session,
                   u'user': g.user, u'auth_user_obj': g.userobj}

        data_dict = {u'q': q, u'limit': limit}
        if vocab != u'':
            data_dict[u'vocabulary_id'] = vocab

        tag_names = get_action(u'tag_autocomplete')(context, data_dict)

    resultSet = {
        u'ResultSet': {
            u'Result': [{u'Name': tag} for tag in tag_names]
        }
    }
    return _finish_ok(resultSet)


def format_autocomplete(ver=API_REST_DEFAULT_VERSION):
    q = request.args.get(u'incomplete', u'')
    limit = request.args.get(u'limit', 5)
    formats = []
    if q:
        context = {u'model': model, u'session': model.Session,
                   u'user': g.user, u'auth_user_obj': g.userobj}
        data_dict = {u'q': q, u'limit': limit}
        formats = get_action(u'format_autocomplete')(context, data_dict)

    resultSet = {
        u'ResultSet': {
            u'Result': [{u'Format': format} for format in formats]
        }
    }
    return _finish_ok(resultSet)


def user_autocomplete(ver=API_REST_DEFAULT_VERSION):
    q = request.args.get(u'q', u'')
    limit = request.args.get(u'limit', 20)
    ignore_self = request.args.get(u'ignore_self', False)
    user_list = []
    if q:
        context = {u'model': model, u'session': model.Session,
                   u'user': g.user, u'auth_user_obj': g.userobj}

        data_dict = {u'q': q, u'limit': limit, u'ignore_self': ignore_self}

        user_list = get_action(u'user_autocomplete')(context, data_dict)
    return _finish_ok(user_list)


def group_autocomplete(ver=API_REST_DEFAULT_VERSION):
    q = request.args.get(u'q', u'')
    limit = request.args.get(u'limit', 20)
    group_list = []

    if q:
        context = {u'user': g.user, u'model': model}
        data_dict = {u'q': q, u'limit': limit}
        group_list = get_action(u'group_autocomplete')(context, data_dict)
    return _finish_ok(group_list)


def organization_autocomplete(ver=API_REST_DEFAULT_VERSION):
    q = request.args.get(u'q', u'')
    limit = request.args.get(u'limit', 20)
    organization_list = []

    if q:
        context = {u'user': g.user, u'model': model}
        data_dict = {u'q': q, u'limit': limit}
        organization_list = get_action(
            u'organization_autocomplete')(context, data_dict)
    return _finish_ok(organization_list)


def snippet(snippet_path, ver=API_REST_DEFAULT_VERSION):
    u'''Renders and returns a snippet used by ajax calls

        We only allow snippets in templates/ajax_snippets and its subdirs
    '''
    snippet_path = u'ajax_snippets/' + snippet_path
    # werkzeug.datastructures.ImmutableMultiDict.to_dict
    # by default returns flattened dict with first occurences of each key.
    # For retrieving multiple values per key, use named argument `flat`
    # set to `False`
    extra_vars = request.args.to_dict()
    return render(snippet_path, extra_vars=extra_vars)


def i18n_js_translations(lang, ver=API_REST_DEFAULT_VERSION):
    ckan_path = os.path.join(os.path.dirname(__file__), u'..')
    source = os.path.abspath(os.path.join(ckan_path, u'public',
                             u'base', u'i18n', u'{0}.js'.format(lang)))
    if not os.path.exists(source):
        return u'{}'
    translations = json.load(open(source, u'r'))
    return _finish_ok(translations)


# Routing

# Root

api.add_url_rule(u'/', view_func=get_api, strict_slashes=False)
api.add_url_rule(u'/<int(min=1, max={0}):ver>'.format(API_MAX_VERSION),
                 view_func=get_api, strict_slashes=False)
