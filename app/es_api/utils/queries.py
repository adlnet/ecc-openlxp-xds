import functools
import json
import logging

from django.core.exceptions import ObjectDoesNotExist
from elasticsearch.dsl import A, Document, Q
from elasticsearch.dsl.query import MoreLikeThis

from configurations.models import CourseInformationMapping, XDSConfiguration
from core.models import (CourseSpotlight, SearchField, SearchFilter,
                         SearchSortOption)
from users.models import Organization

from .queries_base import BaseQueries

logger = logging.getLogger('dict_config_logger')


class XSEQueries(BaseQueries):

    def get_page_start(self, page_number, page_size):
        """
        This helper method returns the starting index of a page given the page
        number, the size, and a start point of 0
        """
        if (page_number <= 1):
            return 0
        else:
            start_index = (page_number - 1) * page_size

            return start_index

    def add_search_aggregations(self, filter_set):
        """This helper method takes in a queryset of filters
            then creates an aggregation for each filter"""
        for curr_filter in filter_set:

            # this is needed because elastic search only filters on keyword
            # fields
            full_field_name = curr_filter.field_name + '.keyword'
            curr_agg = A(curr_filter.filter_type, field=full_field_name)
            self.search.aggs.bucket(curr_filter.display_name, curr_agg)

        return

    def add_search_filters(self, filters):
        """This helper method iterates through the filters and adds them
            to the search query"""
        result_search = self.search

        for filter_name in filters:
            if filter_name != 'page' and filter_name != 'sort':
                # .keyword is necessary for elastic search filtering
                field_name = filter_name + '.keyword'
                result_search = result_search\
                    .filter('terms', **{field_name: filters[filter_name]})

        self.search = result_search

    def add_search_sort(self, filters):
        """This helper method checks if one of the configured sort options was
            sent with the request then adds it to the search query
            filters = object containing all the request parameters
            returns -> modified Elasticsearch search object"""
        # add sort if it was sent in the request
        result_search = self.search

        if 'sort' in filters:
            key = filters['sort']
            sort_option = SearchSortOption.objects.filter(field_name=key,
                                                          active=True)

            # checking that the passed field name is allowed
            if sort_option:
                # need to add .keyword for Elasticsearch
                result_search = result_search.sort(key + '.keyword')

        self.search = result_search

    def search_by_keyword(self, keyword="", filters={}):
        """This method takes in a keyword string + a page number and queries
            ElasticSearch for the term then returns the Response Object"""

        course_mapping = CourseInformationMapping.objects.first()
        fields = [
            course_mapping.course_title, course_mapping.course_description,
            course_mapping.course_code, course_mapping.course_provider,
            course_mapping.course_instructor,
            course_mapping.course_deliveryMode,
            course_mapping.course_competency,
            *SearchField.objects.filter(
                active=True).values_list('field_name', flat=True)
        ]

        q = Q("multi_match",
              query=keyword,
              fields=fields)

        # setting up the search object
        self.search = self.search.query(q)

        self.user_organization_filtering()

        # add sort if it's part of the request
        self.add_search_sort(filters=filters)

        # getting the page size for result pagination
        configuration = XDSConfiguration.objects.first()
        uiConfig = configuration.xdsuiconfiguration
        search_filters = SearchFilter.objects.filter(
            xds_ui_configuration=uiConfig, active=True)

        # create aggregations for each filter
        self.add_search_aggregations(filter_set=search_filters)

        # add filters to the search query
        self.add_search_filters(filters=filters)

        page_size = uiConfig.search_results_per_page
        start_index = self.get_page_start(int(filters['page']), page_size)
        end_index = start_index + page_size
        self.search = self.search[start_index:end_index]

        # call to elasticsearch to execute the query
        response = self.search.execute()
        logger.info(self.search.to_dict())

        return response

    def search_by_competency(self, comp_uuid="", filters={}):
        """This method takes in a competency ID string + a page number and
        queries ElasticSearch for the term then returns the Response Object"""
        course_mapping = CourseInformationMapping.objects.first()

        q = Q("match",
              **{course_mapping.course_competency: comp_uuid})

        # setting up the search object
        self.search = self.search.query(q)

        self.user_organization_filtering()

        # getting the page size for result pagination
        configuration = XDSConfiguration.objects.first()
        uiConfig = configuration.xdsuiconfiguration

        page_size = uiConfig.search_results_per_page
        start_index = self.get_page_start(int(filters['page']), page_size)
        end_index = start_index + page_size
        self.search = self.search[start_index:end_index]

        # call to elasticsearch to execute the query
        response = self.search.execute()
        logger.info(self.search.to_dict())

        return response

    def search_for_derived(self, reference="", filters={}):
        """This method takes in a reference string and queries
            ElasticSearch for the items derived from it then returns the
            Response Object"""

        course_mapping = CourseInformationMapping.objects.first()

        q = Q("match",
              **{course_mapping.course_derived_from: reference})

        # setting up the search object
        self.search = self.search.query(q)

        self.user_organization_filtering()

        # getting the page size for result pagination
        configuration = XDSConfiguration.objects.first()
        uiConfig = configuration.xdsuiconfiguration

        page_size = uiConfig.search_results_per_page
        start_index = self.get_page_start(int(filters['page']), page_size)
        end_index = start_index + page_size
        self.search = self.search[start_index:end_index]

        # call to elasticsearch to execute the query
        response = self.search.execute()
        logger.info(self.search.to_dict())

        return response

    def more_like_this(self, doc_id):
        """This method takes in a doc ID and queries the elasticsearch index
            for courses with similar title or description"""
        likeObj = [
            {
                "_index": self.index,
                "_id": doc_id
            }
        ]

        course_mapping = CourseInformationMapping.objects.first()
        fields = [
            course_mapping.course_title, course_mapping.course_description,
            course_mapping.course_provider
        ]

        # We're going to match based only on two fields
        self.search = self.search.query(
            MoreLikeThis(like=likeObj, fields=fields))
        self.user_organization_filtering()

        # only fetch the first 6 results
        # TODO: make the size configurable
        self.search = self.search[0:6]
        response = self.search.execute()
        logger.info(response)

        return response

    def similar_courses(self, keyword=""):
        """This method takes in a keyword and queries the elasticsearch index
           for 4 courses with similar competencies or subjects"""

        course_mapping = CourseInformationMapping.objects.first()
        fields = [
            course_mapping.course_competency,
            course_mapping.course_subject
        ]

        # We're going to match based only on two fields
        q = Q("multi_match",
              query=keyword,
              fields=fields)

        # setting up the search object
        self.search = self.search.query(q)

        self.user_organization_filtering()

        # sending back 4 responses
        self.search = self.search[0:4]

        # call to elasticsearch to execute the query
        response = self.search.execute()
        logger.info(self.search.to_dict())

        return response

    def spotlight_courses(self):
        """This method queries elasticsearch for courses with ids matching the
            ids of stored CourseSpotlight objects that are active"""
        course_spotlights = CourseSpotlight.objects.filter(active=True)
        id_list = []
        result = []

        for spotlight in course_spotlights:
            id_list.append(spotlight.course_id)

        docs = Document.mget(id_list,
                             using='default',
                             index=self.index,
                             raise_on_error=True,
                             missing='none',)

        for doc in docs:
            curr_dict = doc.to_dict(include_meta=True, skip_empty=True)
            obj_data = curr_dict["_source"]
            meta = {}

            meta["id"] = curr_dict["_id"]
            meta["index"] = curr_dict["_index"]
            obj_data["meta"] = meta
            result.append(obj_data)

        return result

    def search_by_filters(self, page_num, filters={}):
        """This method takes in a page number + a dict of field names and
        values and queries ElasticSearch for the term then returns the
            Response Object"""

        # setting up the search object
        self.user_organization_filtering()
        # getting the page size for result pagination
        configuration = XDSConfiguration.objects.first()
        uiConfig = configuration.xdsuiconfiguration

        for field_name in filters:
            self.search = self.search.query(
                Q("match", **{field_name: filters[field_name]}))

        page_size = uiConfig.search_results_per_page
        start_index = self.get_page_start(page_num, page_size)
        end_index = start_index + page_size
        self.search = self.search[start_index:end_index]

        # call to elasticsearch to execute the query
        response = self.search.execute()
        logger.info(self.search.to_dict())

        return response

    def get_results(self, response):
        """
        This helper method consumes the response of an ElasticSearch Query and
        adds the hits to an array then returns a dictionary representing the
        results
        """
        hit_arr = []
        agg_dict = response.aggregations.to_dict()

        for hit in response:
            hit_dict = hit.to_dict()

            # adding the meta data to the dictionary
            hit_dict['meta'] = hit.meta.to_dict()
            hit_arr.append(hit_dict)

        for key in agg_dict:
            search_filter = SearchFilter.objects.filter(display_name=key,
                                                        active=True).first()
            filter_obj = agg_dict[key]
            filter_obj['field_name'] = search_filter.field_name

        resultObj = {
            "hits": hit_arr,
            "total": response.hits.total.value,
            "aggregations": agg_dict
        }

        return json.dumps(resultObj)

    def suggest(self, partial):
        """
        This method receives a partial to make a completion suggestion
        request to Elastic
        """
        # common settings for suggest query
        query_dict = {'field': 'autocomplete', 'fuzzy': {
            'fuzziness': 'AUTO'
        }}

        # check if user is logged in and in an organization
        if self.user.is_authenticated and self.user.organizations.count() > 0:
            # gets context from orgs user is a member of
            query_dict['contexts'] = {
                'filter': [org.filter for org in
                           self.user.organizations.all()]}
        # check if there are any organizations
        elif Organization.objects.count() > 0:
            # add all organizations to filter so nothing is excluded
            query_dict['contexts'] = {
                'filter': [org.filter for org in Organization.objects.all()]}
        # if no organizations
        else:
            # throw error, a filter is required for context suggestions
            raise ObjectDoesNotExist("No Organizations configured")

        # adds completion type suggestion to search query
        self.search = self.search.suggest('autocomplete_suggestion', partial,
                                          completion=query_dict)

        response = self.search.execute()

        return response

    def user_organization_filtering(self):
        """
        This helper method returns an updated search with the organizations
        the user belongs to filtering the query
        """
        # if user logged in and assigned organizations
        if self.user.is_authenticated and self.user.organizations.count() > 0:
            # generate queries for CourseProviderName from orgs
            orgs = [Q("match", filter=org.filter)
                    for org in self.user.organizations.all()]
            # combine queries into a chained OR query
            filtered_search = self.search.query(
                functools.reduce(lambda a, b: a | b, orgs))
            setattr(filtered_search, "minimum_should_match", 1)
            self.search = filtered_search
            return
        # if user not logged in but organizations exist
        if not self.user.is_authenticated and\
                Organization.objects.all().count() > 0:
            # generate queries for CourseProviderName from orgs
            orgs = [Q("match", filter=org.filter)
                    for org in Organization.objects.all()]
            # combine queries into a chained OR query
            filtered_search = self.search.query(
                functools.reduce(lambda a, b: a | b, orgs))
            setattr(filtered_search, "minimum_should_match", 1)
            self.search = filtered_search
            return
