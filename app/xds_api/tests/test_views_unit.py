import json
import requests
from unittest.mock import Mock, patch

from configurations.models import XDSConfiguration
from core.models import CourseSpotlight, InterestList, SavedFilter
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.test import tag
from django.urls import reverse
from requests.exceptions import HTTPError, RequestException
from rest_framework import status

from .test_setup import TestSetUp


@tag('unit')
class InterestListsTests(TestSetUp):
    def test_interest_lists_unauthenticated(self):
        """
        Test that an unauthenticated user can not fetch any interest lists
        Endpoint: /api/interest_lists
        """
        url = reverse('xds_api:interest-lists')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_interest_lists_authenticated(self):
        """
        Test that an authenticated user only gets their created interest lists
        when calling the /api/interest-lists api
        """
        url = reverse('xds_api:interest-lists')

        # login user
        self.client.login(email=self.auth_email, password=self.auth_password)

        response = self.client.get(url)
        responseDict = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(responseDict[0]["owner"]["email"], self.user_1.email)

    def test_interest_lists_not_valid_authenticated(self):
        """
        Test that an http error 400 occurs when no data is provided
        """

        url = reverse('xds_api:interest-lists')

        # login user
        self.client.login(email=self.auth_email, password=self.auth_password)

        with patch('xds_api.views.InterestListsView') as mock:
            mock.side_effect = Exception

            response = self.client.post(url)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_interest_list_unauthenticated(self):
        """
        Test that an unauthenticated user can not create an interest list.
        """
        url = reverse('xds_api:interest-lists')

        # create interest list
        interest_list_data = {
            "name": "Test Interest List",
            "description": "Test Description",
        }

        response = self.client.post(url, interest_list_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_interest_list_authenticated(self):
        """
        Test that an authenticated user can create an interest list.
        """
        url = reverse('xds_api:interest-lists')

        # login user
        self.client.login(email=self.auth_email, password=self.auth_password)

        # create interest list
        interest_list_data = {
            "name": "Test Interest List",
            "description": "Test Description",
            "courses": []
        }

        response = self.client.post(url, interest_list_data, format="json")
        response_dict = json.loads(response.content)
        print(response_dict)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_dict["name"], "Test Interest List")

    def test_get_interest_list_unauthenticated(self):
        """
        Test that an unauthenticated user can not get an interest list.
        """

        list_id = '1234'
        url = reverse('xds_api:interest-list', args=(list_id,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_interest_list_authenticated(self):
        """
        Test that an authenticated user can get an interest list by id.
        """
        list_id = self.list_3.pk
        url = reverse('xds_api:interest-list', args=(list_id,))

        # login user
        self.client.login(email=self.auth_email, password=self.auth_password)

        response = self.client.get(url)
        response_dict = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_dict["name"], self.list_3.name)

    def test_get_interest_list_authenticated_without_permission(self):
        """
        Test that an authenticated user can't get another user's interest list.
        """
        list_4 = InterestList(
            owner=self.user_2,
            name="list 4",
            description="private list",
            public=False,
        )
        list_4.save()
        list_id = list_4.pk
        url = reverse('xds_api:interest-list', args=(list_id,))

        # login user
        self.client.login(email=self.auth_email, password=self.auth_password)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_interest_list_with_courses_authenticated(self):
        """
        Test that an authenticated user can get an interest list by id,
        and the list has a formatted course.
        """

        list_id = self.list_1.pk
        url = reverse('xds_api:interest-list', args=(list_id,))

        # login user
        self.client.login(email=self.auth_email, password=self.auth_password)

        with patch('xds_api.utils.'
                   'xds_utils.get_request') as get_request, \
                patch('configurations.views.XDSConfiguration.objects') \
                as conf_obj:
            # mock the configuration object
            conf_obj.return_value = conf_obj
            conf_obj.first.return_value = \
                XDSConfiguration(target_xis_metadata_api="www.test.com")

            # mock the get request
            mock_response = get_request.return_value
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {
                        "test": "value",
                    }, ]
            }

            # re-assign the mock to the get request
            get_request.return_value = mock_response

            response = self.client.get(url)
            responseDict = json.loads(response.content)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(responseDict["experiences"], [None])

    def test_get_interest_list_by_id_no_xis(self):
        """
        Test that an authenticated user can get an interest list by id,
        and the list has a formatted course.
        """

        list_id = self.list_1.pk
        url = reverse('xds_api:interest-list', args=(list_id,))

        # login user
        self.client.login(email=self.auth_email, password=self.auth_password)

        with patch('xds_api.utils.'
                   'xds_utils.get_request') as get_request, \
                patch('configurations.views.XDSConfiguration.objects') \
                as conf_obj:
            # mock the configuration object
            conf_obj.return_value = conf_obj
            conf_obj.first.return_value = \
                XDSConfiguration(target_xis_metadata_api="www.test.com")

            # mock the get request
            mock_response = get_request.return_value
            mock_response.status_code = 500
            mock_response.json.return_value = [{
                "test": "value",
            }]

            # re-assign the mock to the get request
            get_request.return_value = mock_response

            response = self.client.get(url)

            self.assertEqual(response.status_code,
                             status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_get_interest_list_by_id_not_found(self):
        """
        Test that requesting an interest list by ID using the
        /api/interest-lists/id api returns an error if none is found
        """
        id = '1234'
        self.client.login(email=self.auth_email, password=self.auth_password)
        url = reverse('xds_api:interest-list', args=(id,))
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_edit_interest_list_unauthenticated(self):
        """
        Test that an unauthenticated user cannot edit an interest list.
        """
        list_id = self.list_1.pk
        url = reverse('xds_api:interest-list', args=(list_id,))

        response = self.client.patch(url, {'name': 'new name'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_edit_interest_list_authenticated_not_owner(self):
        """
        Test that an authenticated user cannot edit an interest list that is
        not theirs.
        """
        list_id = self.list_2.pk
        url = reverse('xds_api:interest-list', args=(list_id,))

        # login user
        self.client.login(email=self.auth_email, password=self.auth_password)

        response = self.client.patch(url, {'name': 'new name'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_edit_interest_list_authenticated_no_list(self):
        """
        Test that an authenticated user cannot edit an interest list that
        does not exist.
        """
        list_id = 99
        url = reverse('xds_api:interest-list', args=(list_id,))

        # login user
        self.client.login(email=self.auth_email, password=self.auth_password)

        response = self.client.patch(url, {'name': 'new name'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_edit_interest_list_authenticated_owner(self):
        """
        Test that an authenticated user can edit an interest list that
        is theirs.
        """
        list_id = self.list_1.id
        url = reverse('xds_api:interest-list', args=(list_id,))

        new_name = "edited name"
        empty_list = []
        new_list = {"name": new_name,
                    "description": self.list_1.description,
                    "experiences": empty_list}

        cont_type = ContentType.objects.get(app_label='xds_api',
                                            model='interestlist')
        permission = Permission.objects. \
            get(name='Can change interest list', content_type=cont_type)
        self.user_1.user_permissions.add(permission)
        self.client.login(email=self.user_1_email,
                          password=self.user_1_password)

        response = \
            self.client.patch(url,
                              data=json.dumps(new_list),
                              content_type="application/json")
        responseDict = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(responseDict["name"], new_name)
        self.assertEqual(responseDict["experiences"], [])

    def test_edit_interest_list_authenticated_invalid_change(self):
        """
        Test that an authenticated user making an invalid change to a
        list returns a 400.
        """
        list_id = self.list_1.id
        url = reverse('xds_api:interest-list', args=(list_id,))

        empty_list = []
        new_list = {"description": self.list_1.description,
                    "experiences": empty_list}

        cont_type = ContentType.objects.get(app_label='xds_api',
                                            model='interestlist')
        permission = Permission.objects. \
            get(name='Can change interest list', content_type=cont_type)
        self.user_1.user_permissions.add(permission)
        self.client.login(email=self.user_1_email,
                          password=self.user_1_password)

        response = \
            self.client.patch(url,
                              data=json.dumps(new_list),
                              content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_interest_list_unauthenticated(self):
        """
        Test that an unauthenticated user cannot delete an interest list.
        """
        list_id = self.list_1.pk
        url = reverse('xds_api:interest-list', args=(list_id,))

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_interest_list_authenticated_not_owner(self):
        """
        Test that an authenticated user cannot delete an interest list
        that is not theirs.
        """
        list_id = self.list_2.pk
        url = reverse('xds_api:interest-list', args=(list_id,))

        # login user
        self.client.login(email=self.auth_email, password=self.auth_password)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_interest_list_authenticated_no_list(self):
        """
        Test that an authenticated user cannot delete an interest list
        that does not exist.
        """
        list_id = 99
        url = reverse('xds_api:interest-list', args=(list_id,))

        # login user
        self.client.login(email=self.auth_email, password=self.auth_password)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_interest_list_authenticated_owner(self):
        """
        Test that an authenticated user can delete an interest list
        that is theirs.
        """
        list_id = self.list_1.id
        url = reverse('xds_api:interest-list', args=(list_id,))

        cont_type = ContentType.objects.get(app_label='xds_api',
                                            model='interestlist')
        permission = Permission.objects. \
            get(name='Can delete interest list', content_type=cont_type)
        self.user_1.user_permissions.add(permission)
        self.client.login(email=self.user_1_email,
                          password=self.user_1_password)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_course_multiple_lists_unauthenticated(self):
        """
        Test that an unauthenticated user cannot add a course to a list.
        """
        list_id = self.list_1.pk
        url = reverse('xds_api:add_course_to_lists', args=(list_id,))

        response = self.client.post(url, {'name': 'new name'})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_course_multiple_lists_success(self):
        """
        Test that adding a course to multiple lists is successful when
        user is owner for the /api/add-course-to-lists POST api
        """
        course_id = self.course_1.pk
        url = reverse('xds_api:add_course_to_lists', args=(course_id,))
        permission = Permission.objects. \
            get(name='Can add add course to lists')
        self.user_2.user_permissions.add(permission)
        self.client.force_authenticate(user=self.user_2)
        data = {
            "lists": [self.list_3.pk]
        }
        response = \
            self.client.post(url,
                             data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.list_3.experiences.all()), 1)

    def test_get_owned_interest_lists_auth(self):
        """Test that an authenticated user only gets their created interest
            lists when calling the /api/interest-lists/owned api"""
        url = reverse('xds_api:owned-lists')
        permission = Permission.objects. \
            get(name='Can view interest lists owned')
        self.user_1.user_permissions.add(permission)
        self.client.force_authenticate(user=self.user_1)
        response = self.client \
            .get(url)
        responseDict = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(responseDict[0]["owner"]["email"], self.user_1.email)
        self.assertEqual(len(self.user_1.interest_lists.all()),
                         len(responseDict))

    def test_get_subscriptions_auth(self):
        """Test that an authenticated user can get a list of interest lists
            that they are subscribed to when calling the endpoint
            /api/interest-lists/subscriptions"""
        url = reverse('xds_api:interest-list-subscriptions')
        permission = Permission.objects. \
            get(name='Can view interest lists subscriptions')
        self.user_1.user_permissions.add(permission)
        self.client.force_authenticate(user=self.user_1)
        # subscribe user 1 to interest list 3
        self.list_3.subscribers.add(self.user_1)
        self.list_3.save()
        response = self.client \
            .get(url)
        response_dict = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.list_3.subscribers.all()),
                         len(response_dict))

    def test_interest_list_subscribe(self):
        """Test that an authenticated user can subscribe to an interest list
            when calling the endpoint /api/interest-lists/<id>/subscribe"""
        list_id = self.list_2.pk
        url = reverse('xds_api:interest-list-subscribe', args=(list_id,))
        permission = Permission.objects. \
            get(name='Can change interest list subscribe')
        self.user_1.user_permissions.add(permission)
        self.client.force_authenticate(user=self.user_1)
        response = self.client \
            .patch(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.list_2.subscribers.all()), 1)

    def test_interest_list_unsubscribe(self):
        """Test that an authenticated user can unsubscribe to an interest list
            when calling the endpoint /api/interest-lists/<id>/unsubscribe"""
        list_id = self.list_2.pk
        url = reverse('xds_api:interest-list-unsubscribe', args=(list_id,))
        permission = Permission.objects. \
            get(name='Can change interest list unsubscribe')
        self.user_1.user_permissions.add(permission)
        self.client.force_authenticate(user=self.user_1)
        # subscribe user 1 to interest list 3
        self.list_2.subscribers.add(self.user_1)
        self.list_2.save()
        response = self.client \
            .patch(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.list_2.subscribers.all()), 0)


@tag('unit')
class SavedFiltersTests(TestSetUp):
    def test_get_saved_filters_owned_unauthorized(self):
        """Test that an unauthenticated user cannot get a list of their
            saved filters when calling the endpoint
            /api/interest-lists/saved-filters/owned"""
        url = reverse('xds_api:owned-filters')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_saved_filters_owned_authorized(self):
        """
        Test that a user can view their saved filters
        """
        url = reverse('xds_api:owned-filters')
        permission = Permission.objects. \
            get(name='Can view saved filters owned')
        self.user_1.user_permissions.add(permission)
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.user_1.saved_filters.all()), 2)

    def test_get_saved_filters(self):
        """Test that trying to get saved filter through the
            /api/saved-filters api succeeds"""
        url = reverse('xds_api:saved-filters')

        saved_config = SavedFilter(owner=self.user_1,
                                   name="Devops", query="randomQuery")
        saved_config.save()
        permission = Permission.objects. \
            get(name='Can view saved filters')
        self.user_1.user_permissions.add(permission)
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(url)
        responseDict = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(responseDict[0]["name"], "Devops")

    def test_create_saved_filters_owned_authorized(self):
        """Test that trying to create saved filter through the
            /api/saved-filters api succeeds"""
        url = reverse('xds_api:saved-filters')
        saved_filter = {
            "name": "Devops",
            "query": "randomQuery"
        }
        permission = Permission.objects. \
            get(name='Can add saved filters')
        self.user_1.user_permissions.add(permission)
        self.client.force_authenticate(user=self.user_1)
        response = \
            self.client.post(url,
                             saved_filter)
        response_dict = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED),
        self.assertEqual(response_dict["name"], "Devops")

    def test_create_saved_filters_owned_invalid_authorized(self):
        """
        Test that trying to create saved filter through the
        /api/saved-filters api fails with an invalid query
        """
        url = reverse('xds_api:saved-filters')
        saved_filter = {
            "query": "randomQuery"
        }
        permission = Permission.objects. \
            get(name='Can add saved filters')
        self.user_1.user_permissions.add(permission)
        self.client.force_authenticate(user=self.user_1)
        response = \
            self.client.post(url,
                             saved_filter)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST),

    def test_create_saved_filters_no_auth(self):
        """Test that trying to create a saved filter through the
            /api/saved-filters api returns an error"""
        url = reverse('xds_api:saved-filters')
        saved_filter = {
            "name": "Devops",
            "query": "randomQuery"
        }

        response = self.client.post(url, saved_filter)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_saved_filter_unauthorized(self):
        """Test that an unauthenticated user cannot get a saved filter
            when calling the endpoint /api/interest-lists/saved-filters/<id>"""
        url = reverse('xds_api:saved-filter', args=(self.filter_1.pk,))

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_saved_filter_authorized(self):
        """Test that trying to get saved filter through the
            /api/saved-filter api succeeds"""
        filter_id = self.filter_1.pk
        url = reverse('xds_api:saved-filter', args=(filter_id,))

        cont_type = ContentType.objects.get(app_label='xds_api',
                                            model='savedfilter')
        permission = Permission.objects. \
            get(name='Can view saved filter', content_type=cont_type)
        self.user_1.user_permissions.add(permission)
        self.client.login(email=self.user_1_email,
                          password=self.user_1_password)

        response = self.client.get(url)
        responseDict = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(responseDict["name"], "Devops")

    def test_edit_saved_filter_not_owner(self):
        """Test that users cannot made edits to filters they do not own
        using the /api/saved-filter/id PATCH"""
        filter_id = self.filter_1.pk
        url = reverse('xds_api:saved-filter', args=(filter_id,))
        self.client.login(email=self.auth_email, password=self.auth_password)
        response = \
            self.client.patch(url,
                              data={"test": "test"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_edit_saved_filter_unauthorized(self):
        """Test that unauthenticated users cannot made edits to filters
        using the /api/saved-filter/id PATCH"""
        filter_id = self.filter_1.pk
        url = reverse('xds_api:saved-filter', args=(filter_id,))
        self.client.login(email=self.auth_email, password=self.auth_password)
        response = self.client.patch(url, data={"test": "test"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_edit_saved_filter_invalid_authorized(self):
        """Test that trying to edit a saved filter through the"""

        filter_id = self.filter_1.pk
        edit_filter = {
            "name": "Devops",
        }

        url = reverse('xds_api:saved-filter', args=(filter_id,))
        cont_type = ContentType.objects.get(app_label='xds_api',
                                            model='savedfilter')
        permission = Permission.objects. \
            get(codename='change_savedfilter', content_type=cont_type)
        self.user_1.user_permissions.add(permission)
        self.client.login(email=self.user_1_email,
                          password=self.user_1_password)

        response = self.client.patch(url, data=edit_filter)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_saved_filter_success(self):
        """Test that editing an filter is successful using the \
            /api/saved-filter/id PATCH"""
        filter_id = self.filter_1.pk
        url = reverse('xds_api:saved-filter', args=(filter_id,))
        cont_type = ContentType.objects.get(app_label='xds_api',
                                            model='savedfilter')
        permission = Permission.objects. \
            get(name='Can change saved filter', content_type=cont_type)
        self.user_1.user_permissions.add(permission)
        self.client.force_authenticate(user=self.user_1)
        new_name = "edited name"
        new_list = {"name": new_name,
                    "query": self.filter_2.query
                    }
        response = \
            self.client.patch(url,
                              data=json.dumps(new_list),
                              content_type="application/json")
        responseDict = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(responseDict["name"], new_name)
        self.assertEqual(responseDict["query"], self.filter_2.query)

    def test_delete_saved_filter_not_owner(self):
        """Test that users cannot remove filters they do not own
        using the /api/saved-filter/id DELETE"""
        filter_id = self.filter_1.pk
        url = reverse('xds_api:saved-filter', args=(filter_id,))
        self.client.login(email=self.auth_email, password=self.auth_password)
        response = \
            self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_saved_filter_success(self):
        """Test that removing an filter is successful using the \
            /api/saved-filter/id DELETE"""
        filter_id = self.filter_1.pk
        url = reverse('xds_api:saved-filter', args=(filter_id,))
        cont_type = ContentType.objects.get(app_label='xds_api',
                                            model='savedfilter')
        permission = Permission.objects. \
            get(name='Can delete saved filter', content_type=cont_type)
        self.user_1.user_permissions.add(permission)
        self.client.login(email=self.user_1_email,
                          password=self.user_1_password)

        response = \
            self.client.delete(url,
                               content_type="application/json")
        responseDict = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(responseDict["message"])


@tag('unit')
class SpotlightCoursesTests(TestSetUp):
    def test_get_spotlight_courses(self):
        """test that calling the endpoint /api/spotlight-courses returns a
            list of documents for configured spotlight courses"""
        url = reverse('xds_api:spotlight-courses')

        permission = Permission.objects. \
            get(name='Can view get spotlight courses')
        self.auth_user.user_permissions.add(permission)

        self.client.login(email=self.auth_email, password=self.auth_password)

        with patch('xds_api.views.get_request') as get_request, \
                patch('xds_api.views.'
                      'get_spotlight_courses_api_url') as get_api_url:
            get_api_url.return_value = "www.test.com"
            http_resp = Mock()
            get_request.return_value = http_resp
            http_resp.json.return_value = [{
                "test": "value"
            }]
            http_resp.status_code = 200

            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_spotlight_courses_error(self):
        """test that calling the endpoint /api/spotlight-courses returns an
            http error if an exception a thrown while reaching out to XIS"""
        url = reverse('xds_api:spotlight-courses')
        errorMsg = "error reaching out to configured XIS API; " + \
                   "please check the XIS logs"
        permission = Permission.objects. \
            get(name='Can view get spotlight courses')
        self.auth_user.user_permissions.add(permission)
        self.client.login(email=self.auth_email, password=self.auth_password)
        CourseSpotlight(course_id='abc123').save()

        with patch('xds_api.views.get_request') as get_request, \
                patch('xds_api.views.'
                      'get_spotlight_courses_api_url') as get_api_url:
            get_api_url.return_value = "www.test.com"
            get_request.side_effect = [HTTPError]

            response = self.client.get(url)
            responseDict = json.loads(response.content)

            self.assertEqual(response.status_code,
                             status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(responseDict['message'], errorMsg)

    def test_get_spotlight_courses_empty(self):
        """test that calling the endpoint /api/spotlight-courses returns
            nothing if there are no spotlight courses"""
        url = reverse('xds_api:spotlight-courses')
        permission = Permission.objects. \
            get(name='Can view get spotlight courses')
        self.auth_user.user_permissions.add(permission)
        self.client.login(email=self.auth_email, password=self.auth_password)

        with patch('xds_api.views.get_request'), \
                patch('xds_api.views.'
                      'get_spotlight_courses_api_url'):

            response = self.client.get(url)

            self.assertEqual(response.status_code,
                             status.HTTP_200_OK)
            self.assertEqual(len(response.content), 0)


@tag('unit')
class ViewTests(TestSetUp):

    def test_get_experiences_server_error(self):
        """Test that calling the endpoint /api/experiences returns an
            http error if an exception a thrown while reaching out to XIS"""
        doc_id = '123456'
        url = reverse('xds_api:get_courses', args=(doc_id,))
        errorMsg = "error reaching out to configured XIS API; " + \
                   "please check the XIS logs"
        self.client.login(email=self.auth_email, password=self.auth_password)
        with patch('xds_api.views.get_request') as get_request:
            get_request.side_effect = RequestException

            response = self.client.get(url)
            responseDict = json.loads(response.content)

            self.assertEqual(response.status_code,
                             status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(responseDict['message'], errorMsg)

    def test_get_experiences_not_found(self):
        """
        Test that calling /api/experiences returns an http 404 error when
        a course is not found.
        """
        doc_id = '123456'
        url = reverse('xds_api:get_courses', args=(doc_id,))

        # login user and get token
        self.client.login(email=self.auth_email, password=self.auth_password)

        with patch('xds_api.views.get_request') as get_request:
            get_request.side_effect = ObjectDoesNotExist

            response = self.client.get(url)

            self.assertEqual(response.status_code,
                             status.HTTP_404_NOT_FOUND)


VALID_STATEMENT = {
    "actor": {
        "objectType": "Agent",
        "mbox": "mailto:test_auth@test.com"
    },
    "verb": {
        "id": "http://adlnet.gov/expapi/verbs/shared"
    },
    "object": {
        "id": "http://example.com/activity/1234"
    }
}

VALID_STATEMENT_NO_WHITELIST = {
    "actor": {
        "objectType": "Agent",
        "mbox": "mailto:test_auth@test.com"
    },
    "verb": {
        "id": "http://example.com/verbs/not-in-whitelist"
    },
    "object": {
        "id": "http://example.com/activity/1234"
    }
}

LRS_SUCCESS_RESPONSE_BODY = ["93f55eca-7c3c-4bb7-a4cc-6991ffd1d282"]

EXPECTED_REGISTRATION_UUID = "00000000-0000-4000-a000-000000000001"


@tag('unit')
class StatementForwardTests(TestSetUp):
    @patch('requests.post')
    @patch('xds_api.views.get_or_set_registration_uuid',
           return_value=EXPECTED_REGISTRATION_UUID)
    def test_forwards_whitelisted_verb(self, mock_registration, mock_post):
        """
        Ensure statements with a whitelisted verb get forwarded to the LRS.
        """
        # Mock the LRS response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = LRS_SUCCESS_RESPONSE_BODY

        # login user
        self.client.login(email=self.auth_email, password=self.auth_password)

        url = reverse('xds_api:forward_statements')

        # Send a statement with a whitelisted verb
        response = self.client.post(
            url,
            data=json.dumps([VALID_STATEMENT]),
            content_type='application/json'
        )

        # Check that requests.post was actually called once
        mock_post.assert_called_once()
        called_args, called_kwargs = mock_post.call_args
        # To the right URL
        self.assertIn('http://lrs.example.com/xapi/statements',
                      called_kwargs["url"])
        # correct JSON payload with reg added
        self.assertEqual(called_kwargs['json'], [{
            **VALID_STATEMENT,
            "context": {"registration": EXPECTED_REGISTRATION_UUID}
        }])

        # Check the response to the client
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), LRS_SUCCESS_RESPONSE_BODY)

    @patch('requests.post')
    @patch('xds_api.views.get_or_set_registration_uuid',
           return_value=EXPECTED_REGISTRATION_UUID)
    def test_overwrites_actor(self, mock_registration, mock_post):
        """
        Ensure statement actors are overwritten.
        """
        # Mock the LRS response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = LRS_SUCCESS_RESPONSE_BODY

        # login user
        self.client.login(email=self.auth_email, password=self.auth_password)

        url = reverse('xds_api:forward_statements')

        # Send a statement with a different actor
        unknown_actor_statement = {
            **VALID_STATEMENT,
            "actor": {
                "objectType": "Agent",
                "mbox": "mailto:test_auth_other@test.com"
            }
        }
        response = self.client.post(
            url,
            data=json.dumps([unknown_actor_statement]),
            content_type='application/json'
        )

        # Check that it is overwritten by the backend
        called_args, called_kwargs = mock_post.call_args
        self.assertEqual(called_kwargs['json'], [{
            **VALID_STATEMENT,
            "context": {"registration": EXPECTED_REGISTRATION_UUID}
        }])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('requests.post')
    def test_forwards_lrs_response(self, mock_post):
        """
        Ensure that the endpoint returns the LRS response without modification.
        """
        # Mock the LRS response
        mock_post.return_value.status_code = 418
        mock_post.return_value.json.return_value = {"I'm": "a teapot."}

        # login user
        self.client.login(email=self.auth_email, password=self.auth_password)

        url = reverse('xds_api:forward_statements')

        # Send a statement
        response = self.client.post(
            url,
            data=json.dumps([VALID_STATEMENT]),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 418)
        self.assertEqual(response.json(), {"I'm": "a teapot."})

    @patch('requests.post')
    def test_rejects_non_whitelisted_verb(self, mock_post):
        """
        Ensure statements with a non-whitelisted verb cause a 400 response.
        """
        # Not expecting a requests.post call at all in this scenario, since
        # no statement is whitelisted, but let's just ensure it never happens
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = LRS_SUCCESS_RESPONSE_BODY

        # login user
        self.client.login(email=self.auth_email, password=self.auth_password)

        url = reverse('xds_api:forward_statements')

        # Send a statement with verb not in the whitelist
        response = self.client.post(
            url,
            data=json.dumps([VALID_STATEMENT_NO_WHITELIST]),
            content_type='application/json'
        )

        # 400 if no match
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # LRS is not called
        mock_post.assert_not_called()

    @patch('requests.post')
    def test_accepts_no_auth(self, mock_post):
        """
        Ensure requests without authentication succeed.
        """

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = LRS_SUCCESS_RESPONSE_BODY

        url = reverse('xds_api:forward_statements')

        # Send a valid statement that will not be sent
        response = self.client.post(
            url,
            data=json.dumps([VALID_STATEMENT]),
            content_type='application/json'
        )

        # 200, it's fine
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Overwrites actor with anonymous
        called_args, called_kwargs = mock_post.call_args
        self.assertEqual(called_kwargs['json'][0]['actor']['mbox'],
                         'mailto:anonymous@example.com')

    @patch('requests.post',
           side_effect=requests.exceptions.ConnectionError("No dice"))
    def test_returns_502_when_connection_fails(self, mock_post_splode):
        # login user
        self.client.login(email=self.auth_email, password=self.auth_password)

        url = reverse('xds_api:forward_statements')

        # Attempt to send a valid statement when there is no LRS
        response = self.client.post(
            url,
            data=json.dumps([VALID_STATEMENT]),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        # Also verify that requests.post was indeed called
        mock_post_splode.assert_called_once()


@tag('unit')
class InterestListMostSubscribedTests(TestSetUp):

    def test_get_most_subscribed_interest_lists_authenticated(self):
        """
        Test that an authenticated user can fetch top 5
        most subscribed interest lists.
        Endpoint: /api/interest-lists/most-subscribed
        """
        url = reverse('xds_api:most-subscribed-lists')

        self.list_1.public = True
        self.list_2.public = True
        self.list_3.public = True
        self.list_1.save()
        self.list_2.save()
        self.list_3.save()

        self.client.login(email=self.auth_email, password=self.auth_password)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_most_subscribed_interest_lists_no_public_lists(self):
        """
        Test that an authenticated user gets an empty list,
        when there are no public interest lists.
        Endpoint: /api/interest-lists/most-subscribed
        """
        url = reverse('xds_api:most-subscribed-lists')

        self.list_1.public = False
        self.list_2.public = False
        self.list_3.public = False
        self.list_1.save()
        self.list_2.save()
        self.list_3.save()

        self.client.login(email=self.auth_email, password=self.auth_password)

        response = self.client.get(url)

        response_dict = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_dict), 0)


@tag('unit')
class CourseMostSavedTests(TestSetUp):

    def test_get_most_saved_courses_authenticated(self):
        """
        Test that an authenticated user can fetch top 5 most saved courses
        Endpoint: /api/experiences/most-saved
        """
        url = reverse('xds_api:most-saved-courses-list')

        self.client.login(email=self.auth_email, password=self.auth_password)

        mock_mapping = Mock()
        mock_mapping.course_title = 'test-core.Title'

        with (
            patch('xds_api.views.metadata_to_target') as metadata_to_target,
            patch('xds_api.views.interest_list_check') as interest_list_check,
            patch(
                'xds_api.views.CourseInformationMapping.objects.first',
                return_value=mock_mapping,
            ),
            patch(
                'xds_api.views.interest_list_get_search_str'
            ) as interest_list_get_search_str,
        ):

            # Mock interest_list_check
            interest_list_check.return_value = (
                ['1234'],  # list of hashes
                '?metadata_key_hash_list=1234',
            )

            # Mock the response
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_json_data = {
                'results': [
                    {
                        'test': 'value',
                    }
                ]
            }

            # Mock interest_list_get_search_str
            interest_list_get_search_str.return_value = (
                mock_resp,
                mock_json_data
            )

            # Mock the metadata formatting
            metadata_to_target.return_value = [
                {
                    'test-core': {'Title': 'Test Course 998'},
                    'meta': {'metadata_key_hash': '1234'}
                }
            ]

            response = self.client.get(url)
            responseDict = json.loads(response.content)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIsInstance(responseDict, list)
            self.assertEqual(responseDict[0]['title'], 'Test Course 998')
            self.assertEqual(responseDict[0]['metadata_key_hash'], '1234')
            self.assertIn('num_saved', responseDict[0])
