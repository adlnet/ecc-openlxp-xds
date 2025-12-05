import json
import logging
from collections import OrderedDict

import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.http import HttpResponse, HttpResponseServerError, JsonResponse
from requests.exceptions import ConnectionError, HTTPError
from rest_framework import status, viewsets, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from configurations.models import CourseInformationMapping, XDSConfiguration
from core.management.utils.xds_internal import bleach_data_to_json
from core.models import CourseSpotlight, Experience, InterestList, SavedFilter
from xds_api.serializers import (CourseMostSavedSerializer,
                                 InterestListMostSubscribedSerializer,
                                 InterestListSerializer,
                                 SavedFilterSerializer)
from xds_api.utils.xds_utils import (get_request,
                                     get_spotlight_courses_api_url,
                                     interest_list_check,
                                     interest_list_get_search_str,
                                     metadata_to_target, save_experiences)
from xds_api.xapi import (actor_with_account, actor_with_mbox,
                          filter_allowed_statements,
                          get_or_set_registration_uuid, jwt_account_name)

logger = logging.getLogger('dict_config_logger')


class GetSpotlightCoursesView(APIView):
    """Gets Spotlight Courses from XIS"""

    def get(self, request):
        """This method defines an API for fetching configured course
            spotlights from XIS"""

        errorMsg = {
            "message": "error fetching spotlight courses; " +
            "please check the XDS logs"
        }
        errorMsgJSON = json.dumps(errorMsg)

        try:
            if CourseSpotlight.objects.filter(active=True).count() > 0:
                api_url = get_spotlight_courses_api_url()
                logger.info(api_url)
                # make API call
                response = get_request(api_url)
                responseJSON = []
                while response.status_code // 10 == 20:
                    responseJSON += response.json()['results']

                    if 'next' in response.json() and \
                            response.json()['next'] is not None:
                        response = get_request(response.json()['next'])
                    else:
                        break

                if response.status_code == 200:
                    formattedResponse = json.dumps(
                        metadata_to_target(responseJSON))

                    return HttpResponse(formattedResponse,
                                        content_type="application/json")
                else:
                    return HttpResponse(responseJSON,
                                        content_type="application/json")
            else:
                return HttpResponse([])

        except requests.exceptions.RequestException as e:
            errorMsg = {"message": "error reaching out to configured XIS" +
                        " API; please check the XIS logs"}
            errorMsgJSON = json.dumps(errorMsg)
            logger.error(e)
            return HttpResponseServerError(errorMsgJSON,
                                           content_type="application/json")


class GetExperiencesView(APIView):
    """Gets a specific Experience from XIS"""

    def get(self, request, exp_hash):
        """This method defines an API for fetching a single course by ID
            from the XIS"""
        errorMsg = {
            "message": "error fetching course with hash: " + exp_hash +
            "; please check the XDS logs"
        }
        errorMsgJSON = json.dumps(errorMsg)

        try:
            composite_api_url = XDSConfiguration.objects.first() \
                .target_xis_metadata_api
            courseQuery = "?metadata_key_hash_list=" + exp_hash
            api_url = composite_api_url + courseQuery
            logger.info(api_url)
            # make API call
            response = get_request(api_url)
            logger.info(api_url)
            responseJSON = []
            # expected response is a list of 1 element
            if response.status_code//10 == 20:
                responseJSON += response.json()['results']

                if not responseJSON:
                    return Response({"message": "Key not found"},
                                    status.HTTP_404_NOT_FOUND)

                logger.info(responseJSON)
                formattedResponse = json.dumps(
                    metadata_to_target(responseJSON[0]))

                return HttpResponse(formattedResponse,
                                    content_type="application/json")
            else:
                return HttpResponse(response.json()['results'],
                                    content_type="application/json")

        except requests.exceptions.RequestException as e:
            errorMsg = {"message": "error reaching out to configured XIS "
                        + "API; please check the XIS logs"}
            errorMsgJSON = json.dumps(errorMsg)

            logger.error(e)
            return HttpResponseServerError(errorMsgJSON,
                                           content_type="application/json")
        except ObjectDoesNotExist as not_found_err:
            errorMsg = {"message": "No configured XIS URL found"}
            logger.error(not_found_err)
            return Response(errorMsg, status.HTTP_404_NOT_FOUND)

        except KeyError as no_element_err:
            logger.error(no_element_err)
            logger.error(response)
            return Response(errorMsg, status.HTTP_404_NOT_FOUND)


class InterestListsView(APIView):
    """Handles HTTP requests for interest lists"""

    def get(self, request):
        """Retrieves interest lists"""
        errorMsg = {
            "message": "Error fetching records please check the logs."
        }
        # initially fetch all public records not owned by the current user
        querySet = InterestList.objects.filter(
            public=True).exclude(owner=request.user)

        logger.info('GET InterestListView called')

        try:
            serializer_class = InterestListSerializer(
                                    querySet,
                                    many=True,
                                    context={'request': request}
                                )
        except HTTPError as http_err:
            logger.error(http_err)
            return Response(errorMsg,
                            status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as err:
            logger.error(err)
            return Response(errorMsg,
                            status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer_class.data, status.HTTP_200_OK)

    def post(self, request):
        """Updates interest lists"""

        logger.info('POST InterestListView called')

        # bleaching/cleaning HTML tags from request data
        bleach_data = bleach_data_to_json(request.data)

        # Assign data from request to serializer
        serializer = InterestListSerializer(data=bleach_data,
                                            context={'request': request})

        if not serializer.is_valid():
            # If not received send error and bad request status
            logger.info(json.dumps(request.data))
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        # If received save record in ledger and send response of UUID &
        # status created
        serializer.save(owner=request.user)
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED)


class InterestListView(APIView):
    """Handles HTTP requests for a specific interest list"""
    errorMsg = {
        "message": "error: no record for corresponding interest list id: " +
                   "please check the logs: "
    }

    def get(self, request, list_id):
        """This method gets a single interest list"""

        try:
            queryset = InterestList.objects.get(pk=list_id)

            # check if current user can view this list
            if (not (queryset.public or queryset.owner == request.user or
                     request.user in queryset.subscribers.all())):
                return Response({"message": "The current user can not access"
                                 + " this Interest List"},
                                status=status.HTTP_401_UNAUTHORIZED)

            serializer_class = InterestListSerializer(queryset)

            # fetch actual courses for each id in the courses array
            interestList = serializer_class.data
            courseQuery = "?metadata_key_hash_list="
            coursesDict = interestList['experiences']

            # for each hash key in the courses list, append them to the query
            coursesDict, courseQuery = (
                interest_list_check(coursesDict, courseQuery))

            if len(coursesDict) > 0:
                response, responseJSON = (
                    interest_list_get_search_str(courseQuery))

                self.errorMsg["message"] += str(response)

                if response.status_code == 200:
                    formattedResponse = metadata_to_target(responseJSON)
                    interestList['experiences'] = formattedResponse

                    return Response(interestList,
                                    status=status.HTTP_200_OK)
                else:
                    return Response(response.json(),
                                    status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except HTTPError as http_err:
            logger.error(http_err)
            return Response(self.errorMsg,
                            status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ObjectDoesNotExist as not_found_err:
            logger.error(not_found_err)
            return Response(self.errorMsg, status.HTTP_404_NOT_FOUND)
        except Exception as err:
            logger.error(err)
            return Response(self.errorMsg,
                            status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer_class.data, status.HTTP_200_OK)

    def patch(self, request, list_id):
        """This method updates a single interest list"""

        try:
            queryset = InterestList.objects.get(pk=list_id)

            # check user is owner of list
            if not request.user == queryset.owner:
                return Response({'Current user does not have access to '
                                'modify the list'},
                                status.HTTP_401_UNAUTHORIZED)
            # save new experiences
            save_experiences(request.data['experiences'])
            # Assign data from request to serializer
            serializer = InterestListSerializer(
                            queryset,
                            data=request.data,
                            context={'request': request}
                        )

            if not serializer.is_valid():
                # If not received send error and bad request status
                logger.info(json.dumps(request.data))
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)

            serializer.save(owner=request.user)

            return Response(serializer.data,
                            status=status.HTTP_200_OK)
        except serializers.ValidationError as err:
            logger.error(str(err))
            err_msg = err.detail
            return Response(err_msg, status=status.HTTP_400_BAD_REQUEST)
        except HTTPError as http_err:
            logger.error(http_err)
            return Response(self.errorMsg,
                            status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ObjectDoesNotExist as not_found_err:
            logger.error(not_found_err)
            return Response(self.errorMsg, status.HTTP_404_NOT_FOUND)
        except Exception as err:
            logger.error(err)
            return Response(err, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, list_id):
        """This method deletes a single interest list"""

        try:
            queryset = InterestList.objects.get(pk=list_id)

            # check user is owner of list
            if not request.user == queryset.owner:
                return Response({'Current user does not have access to '
                                'delete the list'},
                                status.HTTP_401_UNAUTHORIZED)
            # delete list
            queryset = InterestList.objects.get(pk=list_id)
            queryset.delete()

            return Response({"message": "List successfully deleted!"},
                            status=status.HTTP_200_OK)
        except HTTPError as http_err:
            logger.error(http_err)
            return Response(self.errorMsg,
                            status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ObjectDoesNotExist as not_found_err:
            logger.error(not_found_err)
            return Response(self.errorMsg, status.HTTP_404_NOT_FOUND)
        except Exception as err:
            logger.error(err)
            return Response(self.errorMsg,
                            status.HTTP_500_INTERNAL_SERVER_ERROR)


class AddCourseToListsView(APIView):
    """Add courses to multiple interest lists"""

    def post(self, request, exp_hash):
        """This method handles request for adding a single course to multiple
            interest lists at once"""
        errorMsg = {
            "message": "error: unable to add course to provided "
            + "interest lists."
        }

        try:
            # get user
            user = request.user

            # get or add course
            course, created = \
                Experience.objects.get_or_create(pk=exp_hash)
            data = request.data['lists']
            if not isinstance(data, list):
                data = [data]
            course.save()
            # check user is onwer of lists
            for list_id in data:
                currList = InterestList.objects.get(pk=list_id)

                if user == currList.owner:
                    currList.experiences.add(course)
                    currList.save()
            # add course to each list
        except HTTPError as http_err:
            logger.error(http_err)
            return Response(errorMsg, status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as err:
            logger.error(err)
            return Response(errorMsg, status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"message": "course successfully added!"},
                            status.HTTP_200_OK)


class InterestListsOwnedView(APIView):
    """Gets interest lists owned by the current user"""

    def get(self, request):
        """Handles HTTP requests for interest lists managed by request user"""
        errorMsg = {
            "message": "Error fetching records please check the logs."
        }
        # get user
        user = request.user

        try:
            querySet = InterestList.objects.filter(owner=user)
            serializer_class = InterestListSerializer(
                                    querySet,
                                    many=True,
                                    context={'request': request}
                                )
        except HTTPError as http_err:
            logger.error(http_err)
            return Response(errorMsg, status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as err:
            logger.error(err)
            return Response(errorMsg, status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer_class.data, status.HTTP_200_OK)


class InterestListsSubscriptionsView(APIView):
    """Gets interest lists the current user follows"""

    def get(self, request):
        """Handles HTTP requests for interest lists that the request user is
            subscribed to"""
        errorMsg = {
            "message": "Error fetching records please check the logs."
        }
        # get user
        user = request.user

        try:
            querySet = user.subscriptions
            serializer_class = InterestListSerializer(
                                    querySet,
                                    many=True,
                                    context={'request': request}
                                )
        except HTTPError as http_err:
            logger.error(http_err)
            return Response(errorMsg, status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as err:
            logger.error(err)
            return Response(errorMsg, status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer_class.data, status.HTTP_200_OK)


class InterestListSubscribeView(APIView):
    """Subscribes current user to a specific interest list"""

    def patch(self, request, list_id):
        """
        This method handles a request for subscribing to an interest list
        """
        errorMsg = {
            "message": "error: unable to subscribe user to list: "
            + str(list_id)
        }

        try:
            # get user
            user = request.user

            # get interest list
            interest_list = InterestList.objects.get(pk=list_id, public=True)
            interest_list.subscribers.add(user)
            interest_list.save()
        except HTTPError as http_err:
            logger.error(http_err)
            return Response(errorMsg, status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as err:
            logger.error(err)
            return Response(errorMsg, status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"message": "user successfully subscribed to "
                             + "list!"},
                            status.HTTP_200_OK)


class InterestListUnsubscribeView(APIView):
    """Removes a user from subscribing to a specific interest list"""

    def patch(self, request, list_id):
        """
        This method handles a request for unsubscribing from an interest list
        """
        errorMsg = {
            "message": "error: unable to unsubscribe user from list: " +
            str(list_id)
        }

        try:
            # get user
            user = request.user

            # get interest list
            interest_list = InterestList.objects.get(pk=list_id)
            interest_list.subscribers.remove(user)
            interest_list.save()
        except HTTPError as http_err:
            logger.error(http_err)
            return Response(errorMsg, status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as err:
            logger.error(err)
            return Response(errorMsg, status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return \
                Response({"message": "user successfully unsubscribed "
                          + "from list!"},
                         status.HTTP_200_OK)


class SavedFiltersOwnedView(APIView):
    """Returns filters saved by the current user"""

    def get(self, request):
        """
        Handles HTTP requests for saved filters managed by request user
        """
        errorMsg = {
            "message": "Error fetching records please check the logs."
        }
        # get user
        user = request.user

        try:
            querySet = SavedFilter.objects.filter(owner=user)
            serializer_class = SavedFilterSerializer(querySet, many=True)
        except HTTPError as http_err:
            logger.error(http_err)
            return Response(errorMsg, status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as err:
            logger.error(err)
            return Response(errorMsg, status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer_class.data, status.HTTP_200_OK)


class SavedFilterView(APIView):
    """Handles HTTP requests for a specific saved filter"""
    errorMsg = {
        "message": "error: no record for corresponding saved filter id: " +
                   "please check the logs"
    }

    def get(self, request, filter_id):
        """Retrieve a specific saved filter"""

        try:
            queryset = SavedFilter.objects.get(pk=filter_id)

            serializer_class = SavedFilterSerializer(queryset)

            return Response(serializer_class.data, status.HTTP_200_OK)

        except HTTPError as http_err:
            logger.error(http_err)
            return Response(self.errorMsg,
                            status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ObjectDoesNotExist as not_found_err:
            logger.error(not_found_err)
            return Response(self.errorMsg, status.HTTP_404_NOT_FOUND)
        except Exception as err:
            logger.error(err)
            return Response(self.errorMsg,
                            status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, filter_id):
        """Update a specific saved filter"""

        try:
            queryset = SavedFilter.objects.get(pk=filter_id)

            # check user is owner of filter
            if not request.user == queryset.owner:
                return Response({'Current user does not have access to '
                                 'modify the saved filter'},
                                status.HTTP_401_UNAUTHORIZED)
            # Assign data from request to serializer
            serializer = SavedFilterSerializer(queryset, data=request.data)

            if not serializer.is_valid():
                # If not received send error and bad request status
                logger.info(json.dumps(request.data))
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)

            serializer.save()

            return Response(serializer.data,
                            status=status.HTTP_200_OK)
        except HTTPError as http_err:
            logger.error(http_err)
            return Response(self.errorMsg,
                            status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ObjectDoesNotExist as not_found_err:
            logger.error(not_found_err)
            return Response(self.errorMsg, status.HTTP_404_NOT_FOUND)
        except Exception as err:
            logger.error(err)
            return Response(self.errorMsg,
                            status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, filter_id):
        """Delete a specific saved filter"""

        try:
            queryset = SavedFilter.objects.get(pk=filter_id)

            # check user is owner of list
            if not request.user == queryset.owner:
                return Response({'Current user does not have access to '
                                 'delete the saved filter'},
                                status.HTTP_401_UNAUTHORIZED)
            # delete filter
            queryset = SavedFilter.objects.get(pk=filter_id)
            queryset.delete()

            return Response({"message": "Filter successfully deleted!"},
                            status=status.HTTP_200_OK)
        except HTTPError as http_err:
            logger.error(http_err)
            return Response(self.errorMsg,
                            status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ObjectDoesNotExist as not_found_err:
            logger.error(not_found_err)
            return Response(self.errorMsg, status.HTTP_404_NOT_FOUND)
        except Exception as err:
            logger.error(err)
            return Response(self.errorMsg,
                            status.HTTP_500_INTERNAL_SERVER_ERROR)


class SavedFiltersView(APIView):
    """Handles HTTP requests for multiple saved filters"""

    def get(self, request):
        """Gets saved filters"""

        errorMsg = {
            "message": "Error fetching records please check the logs."
        }
        # initially fetch all saved filters
        querySet = SavedFilter.objects.all()

        try:
            serializer_class = SavedFilterSerializer(querySet, many=True)
        except HTTPError as http_err:
            logger.error(http_err)
            return Response(errorMsg,
                            status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as err:
            logger.error(err)
            return Response(errorMsg,
                            status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer_class.data, status.HTTP_200_OK)

    def post(self, request):
        """Update saved filters"""

        data = OrderedDict()
        data.update(request.data)
        # bleaching/cleaning HTML tags from request data
        data_bleach = bleach_data_to_json(data)

        # Assign data from request to serializer
        serializer = SavedFilterSerializer(data=data_bleach)

        if not serializer.is_valid():
            # If not received send error and bad request status
            logger.info(json.dumps(request.data))
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        serializer.save(owner=request.user)
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED)


class StatementForwardView(APIView):
    """Handles xAPI Requests"""

    def post(self, request):
        """Forward statements to an LRS"""

        config = XDSConfiguration.objects.first()
        if not config:
            return Response({'message': 'No XDS configuration found.'},
                            status.HTTP_500_INTERNAL_SERVER_ERROR)

        lrs_endpoint = config.lrs_endpoint
        lrs_username = config.lrs_username
        lrs_password = config.lrs_password

        if not (lrs_endpoint and lrs_username and lrs_password):
            return Response({'message': 'LRS credentials not configured.'},
                            status.HTTP_500_INTERNAL_SERVER_ERROR)

        statements = request.data
        if not isinstance(statements, list):
            # xAPI POST can be single or array
            statements = [statements]

        # Filter out statements whose verb is not in our whitelist
        allowed_statements = filter_allowed_statements(statements)

        if not allowed_statements:
            return Response({'message':
                             'No statements had whitelisted verbs.'},
                            status.HTTP_400_BAD_REQUEST)

        # Get statement actor identity
        if settings.XAPI_USE_JWT:
            account_name = jwt_account_name(
                request,
                settings.XAPI_ACTOR_ACCOUNT_NAME_JWT_FIELDS
            )
            if account_name is None:
                # Return a 400 if none matched
                return Response(
                    {"message": "No valid JWT field found."},
                    status.HTTP_400_BAD_REQUEST
                )
            actor = actor_with_account(settings.XAPI_ACTOR_ACCOUNT_HOMEPAGE,
                                       account_name)
        else:
            if request.user.is_authenticated:
                user_email = request.user.email  # Safe to access
            elif settings.XAPI_ALLOW_ANON:
                # request.user is AnonymousUser
                user_email = settings.XAPI_ANON_MBOX
            else:
                return Response({'message': 'Could not form xAPI Actor.'},
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
            actor = actor_with_mbox(user_email)

        # Get registration UUID
        registration = get_or_set_registration_uuid(request)

        # Set actor and context registration
        for statement in allowed_statements:
            statement["actor"] = actor
            context = statement.get('context', {})
            context['registration'] = registration
            statement['context'] = context

        headers = {
            'Content-Type': 'application/json',
            'X-Experience-API-Version': '1.0.3',
        }

        try:
            resp = requests.post(
                url=f"{lrs_endpoint}/statements",
                json=allowed_statements,
                headers=headers,
                auth=(lrs_username, lrs_password),
            )
        except ConnectionError:
            return Response({'message': 'Could not connect to LRS'},
                            status.HTTP_502_BAD_GATEWAY)

        return JsonResponse(resp.json(), status=resp.status_code, safe=False)


class InterestListMostSubscribedView(APIView):
    """Get the top 5 most subscribed interest lists"""

    def get(self, request):
        """Handles HTTP requests for top 5 interest lists"""
        errorMsg = {
            "message": "Error fetching interest lists please check the logs."
        }

        try:
            # Top 5 most subscribed interest lists,
            # Filtered to public only, annotated with subscriber count,
            # Ordered by number of subscribers
            querySet = InterestList.objects.all().filter(
                public=True).annotate(num_subscribers=Count(
                    'subscribers')).order_by('-num_subscribers')[:5]

            serializer_class = InterestListMostSubscribedSerializer(
                querySet, many=True)

        except Exception as err:
            logger.error(err)
            return Response(errorMsg, status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer_class.data, status.HTTP_200_OK)


class CourseMostSavedViewSet(viewsets.ReadOnlyModelViewSet):
    """Get the top 5 most saved courses across all interest lists"""
    serializer_class = CourseMostSavedSerializer
    queryset = (
        Experience.objects.all()
        .annotate(num_saved=Count("interestlist"))
        .order_by("-num_saved")[:5]
    )

    def get_serializer_context(self):
        """Get course mapping and formatted response for serializer context"""
        context = super().get_serializer_context()
        context['formatted_response'] = []
        context['course_mapping'] = CourseInformationMapping.objects.first()

        try:
            course_query = '?metadata_key_hash_list='
            courses = list(
                self.queryset.values_list('metadata_key_hash', flat=True)
            )

            courses, course_query = (
               interest_list_check(courses, course_query))

            if len(courses) > 0:
                response, response_json = (
                    interest_list_get_search_str(course_query))

                if response.status_code == 200:
                    context['formatted_response'] = \
                        metadata_to_target(response_json)
        except Exception as err:
            logger.error(err)
        return context
