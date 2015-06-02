#!/usr/bin/env python
# encoding: utf-8

import routes
import json
import webob.dec
import webob
import httplib
import traceback
from oslo.config import cfg

from torconf import wsgi
from torconf import sapi
from torconf import exceptions

exception_map = {
        exceptions.SapiNotFound: webob.exc.HTTPNotFound,
        exceptions.SapiBadRequest: webob.exc.HTTPBadRequest,
        exceptions.SapiTorConfigError: webob.exc.HTTPServiceUnavailable,
        exceptions.SapiNoAvaVlanError: webob.exc.HTTPServiceUnavailable}

RESOURCES = {
        'network': {
            "collection_actions": ['create'],
            "member_actions": ['show', 'update', 'delete']
        },
        'port': {
            "collection_actions": ['create'],
            "member_actions": ['show', 'update', 'delete']
        },
        'subnet': {
            "collection_actions": ['create'],
            "member_actions": ['show', 'update', 'delete']
        },
        'localvlan': {
            "collection_actions":['create'],
            "member_actions":['delete']
        },
        'topology': {
            "collection_actions":['index'],
            "member_actions":[]
        },
        'sync': {
            "collection_actions":['create'],
            "member_actions":[]
        },
        'tor': {
            "collection_actions":['create'],
            "member_actions":['delete']
        }
}
COLLECTION_ACTIONS = 'collection_actions'
MEMBER_ACTIONS = 'member_actions'

#uuid regex pattern
REQUIREMENTS = {'id': R"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}"}
IP_REQUIREMENTS = {'id': R"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}"}

class APIRouter(wsgi.Router):
    def __init__(self, mapper=None):
        if not mapper:
            mapper = routes.Mapper()
        instance = sapi.get_instance()

        def _do_mapper_resource(resource, actions, requirements):
            controller = Controller(instance, resource,
                    actions[COLLECTION_ACTIONS], actions[MEMBER_ACTIONS])
            mapper_kwargs = dict(controller=Convert2Resource(controller),
                                requirements=requirements,
                                collection_actions=actions[COLLECTION_ACTIONS],
                                member_actions=actions[MEMBER_ACTIONS])
            return mapper.collection(resource, resource, **mapper_kwargs)

        #api index for "/"
        index = APIIndex()
        mapper.connect("index", "/", controller=index)
        for resource in RESOURCES:
            if resource == 'tor':
                requirements = IP_REQUIREMENTS
            else:
                requirements = REQUIREMENTS
            _do_mapper_resource(resource, RESOURCES[resource], requirements)
        super(APIRouter, self).__init__(mapper)

#api index for app name and version.
class APIIndex(object):
    def __init__(self):
        self.version = cfg.CONF['version']
        self.name = cfg.CONF['app']

    def get(self, request):
        resp  = webob.Response(request=request,
                status=httplib.OK,
                content_type="application/json")
        resp.body = json.dumps(dict(application=self.name,
                                    version=self.version))
        return resp

    @webob.dec.wsgify
    def __call__(self, request):
        return self.get(request)

class Controller(object):
    SHOW = 'show'
    INDEX = 'index'
    CREATE = 'create'
    DELETE = 'delete'
    UPDATE = 'update'

    def __init__(self, instance, resource, collection_actions, member_actions):
        self._instance = instance
        self.resource = resource
        self._instance_handlers = {}
        for action in collection_actions + member_actions:
            self._instance_handlers[action] = '%s_%s' %(action, self.resource)
        print self._instance_handlers

    def show(self, request, id, **kwargs):
        action = self._instance_handlers[self.SHOW]
        obj = getattr(self._instance, action)(request, id, **kwargs)
        return obj

    def create(self, request, body=None, **kwargs):
        action = self._instance_handlers[self.CREATE]
        obj = getattr(self._instance, action)(request, body=body, **kwargs)
        return obj

    def update(self, request, id, body=None, **kwargs):
        action = self._instance_handlers[self.UPDATE]
        obj = getattr(self._instance, action)(request, id, body=body, **kwargs)
        return obj

    def delete(self, request, id, **kwargs):
        action = self._instance_handlers[self.DELETE]
        obj = getattr(self._instance, action)(request, id, **kwargs)
        return obj

    def index(self, request, **kwargs):
        action = self._instance_handlers[self.INDEX]
        obj = getattr(self._instance, action)(request, **kwargs)
        return obj

class Request(wsgi.Request):
    pass

def Convert2Resource(controller):
    default_deserializers = {'application/json':wsgi.JSONDeserializer()}
    default_serializers = {'application/json':wsgi.JSONDictSerializer()}
    format_types = {'json':'application/json'}

    @webob.dec.wsgify(RequestClass=Request)
    def resource(request):
        route_args = request.environ.get('wsgiorg.routing_args')
        if route_args:
            args = route_args[1].copy()
        else:
            args = {}

        print "args: %s" %(args)

        args.pop('controller', None)
        format = args.pop('format', None)
        action = args.pop('action', None)
        content_type = format_types.get(format, request.best_match_content_type())
        content_type = "application/json"
        deserializer = default_deserializers.get(content_type)
        serializer = default_serializers.get(content_type)

        print action, content_type
        try:
            if request.body:
                args['body'] = deserializer.deserialize(request.body)['body']
            method = getattr(controller, action)

            result = method(request=request, **args)
        except exceptions.SapiException as e:
            for exce in exception_map:
                if isinstance(e, exce):
                    mapped_exc = exception_map[exce]
                    break
            else:
                mapped_exc = webob.exc.HTTPInternalServerError

            kwargs = {"body":str(e)}
            raise mapped_exc(**kwargs)
        except:
            print traceback.format_exc()

        status = 200
        body = serializer.serialize(result)

        return webob.Response(request=request, status=status,
                content_type=content_type, body=body)
    return resource
