from django.conf import settings
import requests


def get_headers(access_token):
    """
    Build the headers for each authorised request
    """
    return {
        'Authorization': 'Bearer %s' % access_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }


def get_user_with_no_id(instance_url, access_token):
    """
    Get the Salesforce user details without knowing the user id
    """
    # Build the URL
    url = '%s%schatter/users/me' % (instance_url, settings.SALESFORCE_REST_URL)

    # Query for the user record
    result = requests.get(url, headers=get_headers(access_token))
    
    return result.json()