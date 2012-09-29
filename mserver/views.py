import json
import hashlib
import hmac
from datetime import datetime, timedelta

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.forms.models import model_to_dict

from mserver.models import Server

def verify_json(request):
    if 'application/json' in request.META.get('CONTENT_TYPE'):
        try:
            data = json.loads(request.body)
            return True
        except ValueError:
            return False
    return False

def verify_signature(data, key):
    try:
        name = data['name']
        signature = data['signature']
        real_signature = hmac.new(key, name, hashlib.sha1).hexdigest()
        if real_signature == signature:
            return True
    except (TypeError, AttributeError, KeyError):
        return False
    return False

def json_response(data):
    return HttpResponse(json.dumps(data), content_type='application/json')

def success(message):
    return json_response({
        'status': 'success',
        'message': message,
    })

def error(message):
    return json_response({
        'status': 'error',
        'message': message,
    })


SIGNED_METHODS = ['POST', 'PUT',]
REQUIRED_FIELDS = ['name', 'port']

@csrf_exempt
def main(request, *args, **kwargs):
    # Get settings
    master_key = getattr(settings, 'MASTER_KEY')
    timeout = getattr(settings, 'HEARTBEAT_TIMEOUT')
    require_signature = getattr(settings, 'REQUIRE_SIGNATURE')

    # Prune server list
    for server in Server.objects.all():
        if datetime.now() - server.timestamp > timedelta(0, timeout):
            server.delete()

    # List view
    if request.method == 'GET':
        result = []
        for server in Server.objects.all():
            obj = model_to_dict(server)
            if obj.get('id'):
                del obj['id']
            result.append(obj)
        return json_response(result)

    # Other views
    elif request.method in SIGNED_METHODS:
        # Verify its a valid JSON request
        if not verify_json(request):
            return HttpResponseBadRequest("Invalid JSON.")

        data = json.loads(request.body)

        # Verify the HMAC-SHA1 signature is valid against master key
        if require_signature and not verify_signature(data, master_key):
            return HttpResponseBadRequest()

        # Register a new server
        if request.method == 'POST':
            if not all(map(lambda field: field in data.keys(), REQUIRED_FIELDS)):
                return error("Must include all fields: %s" % ', '.join(REQUIRED_FIELDS))
            if Server.objects.filter(name=data.get('name')).count() > 0:
                return error("Server with that name already exists.")
            Server.objects.create(
                name=data.get('name'),
                port=data.get('port'),
                address=request.META.get('REMOTE_ADDR'),
            )
            return success("Registered new server.")

        # Heartbeat server
        if request.method == 'PUT':
            try:
                server = Server.objects.get(name=data.get('name'))
                server.timestamp = datetime.now()
                server.save()
                return success("Accepted heartbeat for server.")
            except Server.DoesNotExist:
                return error("That server doesn't exist.")

    # Show allowed methods
    else:
        return HttpResponseNotAllowed(SIGNED_METHODS + ['GET'])
