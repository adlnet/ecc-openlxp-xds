import json

import requests
from configurations.models import XDSConfiguration
from core.models import CourseSpotlight, Experience
from rest_framework import status
from rest_framework.response import Response


def get_request(request_url):
    """This method handles a simple HTTP get request to the passe in
        request_url"""
    response = requests.get(request_url, timeout=3.0)

    return response


def get_spotlight_courses_api_url():
    """This method gets the list of configured course spotlight IDs, the
        configured XIS api url and generates the query to request records"""
    # get XIS API url
    course_spotlights = CourseSpotlight.objects.filter(active=True)
    # get search string
    composite_api_url = XDSConfiguration.objects.first()\
        .target_xis_metadata_api
    queryString = '?metadata_key_hash_list='

    for num, spotlight in enumerate(course_spotlights):
        if num >= (len(course_spotlights) - 1):
            queryString += spotlight.course_id
        else:
            queryString += spotlight.course_id + ','

    full_api_string = composite_api_url + queryString

    return full_api_string


def format_metadata(exp_record):
    """This method takes in a record and converts it to an XSE format"""
    result = None

    if 'metadata' in exp_record:
        metadataObj = exp_record['metadata']

        if 'Metadata_Ledger' in metadataObj:
            result = metadataObj['Metadata_Ledger']
            result["Supplemental_Ledger"] = \
                (metadataObj["Supplemental_Ledger"] if "Supplemental_Ledger" in
                 metadataObj else None)
            meta = {}

            meta["id"] = exp_record["unique_record_identifier"]
            meta["metadata_key_hash"] = exp_record["metadata_key_hash"]
            result["meta"] = meta

    return result


def metadata_to_target(metadata_JSON):
    """This method takes in a JSON representation of a record and transforms it
        into the search engine format"""
    if isinstance(metadata_JSON, list) or isinstance(metadata_JSON, dict):
        metadata_dict = metadata_JSON
    else:
        metadata_dict = json.loads(metadata_JSON)
    result = None

    if isinstance(metadata_dict, list):
        result_list = []

        for record in metadata_dict:
            formatted_record = format_metadata(record)
            result_list.append(formatted_record)

        result = result_list

    elif isinstance(metadata_dict, dict):
        formatted_record = format_metadata(metadata_dict)
        result = formatted_record

    return result


def get_courses_api_url(course_id):
    """This method gets the metadata api url to fetch single records"""
    composite_api_url = XDSConfiguration.objects.first()\
        .target_xis_metadata_api
    full_api_url = composite_api_url + course_id

    return full_api_url


def save_experiences(course_list):
    """This method handles the saving of each course in the list"""
    for course_hash in course_list:
        newExperience, created = \
            Experience.objects.get_or_create(pk=course_hash)
        newExperience.save()


def handle_unauthenticated_user():
    """This method returns an HTTP response if user is not authenticated"""
    return Response({'Access Denied: Unauthenticated user.'},
                    status.HTTP_401_UNAUTHORIZED)


def interest_list_check(coursesDict, courseQuery):
    # for each hash key in the courses list, append them to the query
    for idx, metadata_key_hash in enumerate(coursesDict):
        if idx == len(coursesDict) - 1:
            courseQuery += metadata_key_hash
        else:
            courseQuery += (metadata_key_hash + ",")
    return coursesDict, courseQuery


def interest_list_get_search_str(courseQuery):
    # get search string
    composite_api_url = XDSConfiguration.objects.first() \
        .target_xis_metadata_api
    api_url = composite_api_url + courseQuery

    # make API call
    response = get_request(api_url)
    responseJSON = []
    while response.status_code//10 == 20:
        responseJSON += response.json()['results']

        if 'next' in response.json() and\
                response.json()['next'] is not None:
            response = get_request(response.json()['next'])
        else:
            break
    return response, responseJSON


def get_multilevel_dict(dictionary, path):
    """
    Recursive function to traverse dict to path and retrive value.
    :param dictionary: the dictionary to traverse
    :param path: a list of keys to navigate through to the final item
    :return: returns the value at the path
    """
    if path == []:
        return dictionary

    if isinstance(dictionary, dict) and path[0] in dictionary:
        return get_multilevel_dict(dictionary[path[0]], path[1:])

    return None


def get_course_title_from_response(formatted_response,
                                   meta_key_hash, course_mapping):
    """Get course title from formatted API response
        using metadata_key_hash and course_mapping"""

    if '.' not in course_mapping.course_title:
        return None

    # Split into list for traversal
    path = course_mapping.course_title.split('.')

    for course in formatted_response:
        if course.get('meta', {}).get('metadata_key_hash') == meta_key_hash:
            return get_multilevel_dict(course, path)

    return None
