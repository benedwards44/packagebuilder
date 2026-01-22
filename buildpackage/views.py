from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from buildpackage.forms import LoginForm
from buildpackage.models import Package
from django.conf import settings
from buildpackage.tasks import query_components_from_org
from time import sleep

from . import utils

import json
import requests
import datetime
import uuid

def index(request):
    
    if request.method == 'POST':

        login_form = LoginForm(request.POST)

        if login_form.is_valid():

            environment = login_form.cleaned_data['environment']

            domain = 'https://login.salesforce.com'
            if environment == 'Sandbox':
                domain = 'https://test.salesforce.com'
            elif environment == 'Custom':
                domain = 'https://' + login_form.cleaned_data['domain']
 
            oauth_url = domain + '/services/oauth2/authorize?response_type=code&client_id=' + settings.SALESFORCE_CONSUMER_KEY + '&redirect_uri=' + settings.SALESFORCE_REDIRECT_URI + '&state='+ domain
            
            return HttpResponseRedirect(oauth_url)
    else:
        login_form = LoginForm()

    return render(request, 'index.html', {'login_form': login_form})

def oauth_response(request):

    error_exists = False
    error_message = ''
    username = ''
    org_name = ''

    if request.GET:

        oauth_code = request.GET.get('code')
        domain = request.GET.get('state')
        access_token = ''
        instance_url = ''
        org_id = ''
        
        r = requests.post(
            domain + '/services/oauth2/token', 
            headers={ 
                'Content-Type':'application/x-www-form-urlencoded'
            }, 
            data={
                'grant_type': 'authorization_code',
                'client_id': settings.SALESFORCE_CONSUMER_KEY,
                'client_secret': settings.SALESFORCE_CONSUMER_SECRET,
                'redirect_uri': settings.SALESFORCE_REDIRECT_URI,
                'code': oauth_code
            }
        )
        auth_response = json.loads(r.text)

        if 'error_description' in auth_response:
            error_exists = True
            error_message = auth_response['error_description']
        else:
            access_token = auth_response['access_token']
            instance_url = auth_response['instance_url']
            user_id = auth_response['id'][-18:]
            org_id = auth_response['id'][:-19]
            org_id = org_id[-18:]

            # get username of the authenticated user
            r = requests.get(instance_url + '/services/data/v' + str(settings.SALESFORCE_API_VERSION) + '.0/sobjects/User/' + user_id + '?fields=Username', headers={'Authorization': 'OAuth ' + access_token})
            query_response = json.loads(r.text)
            username = query_response['Username']

            # get the org name of the authenticated user
            r = requests.get(instance_url + '/services/data/v' + str(settings.SALESFORCE_API_VERSION) + '.0/sobjects/Organization/' + org_id + '?fields=Name', headers={'Authorization': 'OAuth ' + access_token})
            if 'Name' in json.loads(r.text):
                org_name = json.loads(r.text)['Name']
            else:
                org_name = ''

        login_form = LoginForm(initial={
            'access_token': access_token, 
            'instance_url': instance_url, 
            'org_id': org_id, 
            'package_option': 'wildcard_only'
        }) 

    if request.POST:

        login_form = LoginForm(request.POST)

        if login_form.is_valid():

            access_token = login_form.cleaned_data['access_token']
            instance_url = login_form.cleaned_data['instance_url']
            org_id = login_form.cleaned_data['org_id']
            package_option = login_form.cleaned_data['package_option']

            if 'logout' in request.POST:
                r = requests.post(instance_url + '/services/oauth2/revoke', headers={'content-type':'application/x-www-form-urlencoded'}, data={'token': access_token})
                instance = instance_url.replace('https://','').replace('.salesforce.com','')
                return HttpResponseRedirect('/logout?instance=' + instance)

            if 'get_components' in request.POST:

                # create the package record to store results
                package = Package()
                package.random_id = uuid.uuid4()
                package.created_date = datetime.datetime.now()
                package.username = org_id
                package.api_version = str(settings.SALESFORCE_API_VERSION) + '.0'
                package.access_token = access_token
                package.instance_url = instance_url
                package.component_option = package_option
                package.status = 'Not Started'
                package.save()

                # Queue job to run async
                try:
                    query_components_from_org.delay(package.id)
                except:
                    # If fail above, wait 5 seconds and try again. Not ideal but should work for now
                    sleep(5)
                    try:
                        query_components_from_org.delay(package.id)
                    except:
                        # Sleep another 5
                        sleep(5)
                        query_components_from_org.delay(package.id)

                return HttpResponseRedirect('/loading/' + str(package.random_id))

    return render(
        request, 
        'oauth_response.html',
        {
            'error': error_exists, 
            'error_message': error_message, 
            'username': username, 
            'org_name': org_name, 
            'login_form': login_form
        }
    )

# AJAX endpoint for page to constantly check if job is finished
def job_status(request, package_id):

    package = get_object_or_404(Package, random_id = package_id)

    response_data = {
        'status': package.status,
        'error': package.error,
        'done': package.status in ['Finished', 'Error'],
        'success': package.status == 'Finished'
    }

    return HttpResponse(json.dumps(response_data), content_type='application/json')

# Page for user to wait for job to run
def loading(request, package_id):

    package = get_object_or_404(Package, random_id=package_id)

    # If finished already (unlikely) direct to schema view
    if package.status == 'Finished':
        return HttpResponseRedirect('/package/' + str(package.random_id))
    else:
        return render(
            request, 
            'loading.html',
            {'package': package}
        )

def package(request, package_id):

    package = get_object_or_404(Package, random_id=package_id)
    package_xml = package.package
    package.delete()
    return render(
        request, 
        'package.html',
        {'package_xml': package_xml}
    )


def logout(request):

    instance = request.GET.get('instance')
    return render(
        request, 
        'logout.html',
        {'instance': instance}
    )


@csrf_exempt
def auth_details(request):
    """
        RESTful endpoint to pass authentication details
    """

    try:

        request_data = json.loads(request.body)

        # Check for all required fields
        if 'org_id' not in request_data or 'access_token' not in request_data or 'instance_url' not in request_data:

            response_data = {
                'status': 'Error',
                'success':  False,
                'error_text': 'Not all required fields were found in the message. Please ensure org_id, access_token and instance_url are all passed in the payload'
            }

        # All fields exist. Start job and send response
        else:

            # create the package record to store results
            package = Package()
            package.random_id = uuid.uuid4()
            package.created_date = datetime.datetime.now()
            package.username = request_data['org_id']
            package.access_token = request_data['access_token']
            package.instance_url = request_data['instance_url']
            package.api_version = str(settings.SALESFORCE_API_VERSION) + '.0'
            package.status = 'Not Started'
            package.save()

            # Run job
            query_components_from_org.delay(package.id)

            # Build response 
            response_data = {
                'job_url': 'https://packagebuilder.cloudtoolkit.co/loading/' + str(package.random_id) + '/?noheader=1',
                'status': 'Success',
                'success': True
            }

    except Exception as error:

        # If there is an error, raise exception and return
        response_data = {
            'status': 'Error',
            'success':  False,
            'error_text': str(error)
        }
    
    return HttpResponse(json.dumps(response_data), content_type = 'application/json')


@csrf_exempt
def api_create_job(request):

    try:

        # Load the Json request
        json_body = json.loads(request.body)

        instance_url = json_body.get('instanceUrl')
        access_token = json_body.get('accessToken')
        component_option = json_body.get('componentOption','all')

        if not instance_url:
            return HttpResponse(
                json.dumps({
                    'success': False,
                    'error': 'instanceUrl is required. Please send the instanceUrl for your Salesforce Org. Eg. https://ap2.salesforce.com or https://mydomain.my.salesforce.com'
                }),
                content_type='application/json',
                status=400
            )

        if not access_token:
            return HttpResponse(
                json.dumps({
                    'success': False,
                    'error': 'accessToken is required. Please pass through a valid Salesforce access token (or Session Id)'
                }),
                content_type='application/json',
                status=400
            )

        # If we have an instance_url and access token, we can start the job
        # Attempt login with the details provided
        try:

            user = utils.get_user_with_no_id(instance_url, access_token)

            # If response is a list, there's an error
            # Not a great approahc, but the API returns a list when an error and a single object whe not
            if type(user) is list:
                user_response = user[0]        
                return HttpResponse(
                    json.dumps({
                        'success': False,
                        'error': '%s: %s' % (user_response.get('errorCode'), user_response.get('message'))
                    }),
                    content_type='application/json',
                    status=401
                )

            # We've logged in, create the job
            package = Package()
            package.random_id = uuid.uuid4()
            package.created_date = datetime.datetime.now()
            package.username = user.get('username')
            package.api_version = str(settings.SALESFORCE_API_VERSION) + '.0'
            package.access_token = access_token
            package.instance_url = instance_url
            package.component_option = component_option
            package.status = 'Running'
            package.save()

            # Start the job to scan the job
            query_components_from_org.delay(package.id)

            return HttpResponse(
                json.dumps({
                    'success': True,
                    'id': str(package.random_id)
                }),
                content_type='application/json',
                status=200
            )

        except Exception as ex:
            return HttpResponse(
                json.dumps({
                    'success': False,
                    'error': 'Error logging into Salesforce: ' + str(ex)
                }),
                content_type='application/json',
                status=401
            )

    except Exception as ex:
        return HttpResponse(
            json.dumps({
                'success': False,
                'error': str(ex)
            }),
            content_type='application/json',
            status=500
        )


@csrf_exempt
def get_package(request, package_id):

    package = get_object_or_404(Package, random_id=package_id)

    return HttpResponse(
        json.dumps({
            'id': package.random_id,
            'status': package.status,
            'componentOption': package.component_option,
            'xml': package.package
        }),
        content_type='application/json',
        status=200
    )