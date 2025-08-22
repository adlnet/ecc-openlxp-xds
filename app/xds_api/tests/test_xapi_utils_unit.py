from unittest.mock import patch

from django.test import tag
from xds_api.tests.test_xapi_setup import XAPITestSetup
from xds_api.utils.xapi_utils import (
    COURSE_PROGRESS_VERBS,
    get_lrs_statements,
    process_course_statements,
    remove_duplicates,
    filter_statements_by_platform,
    filter_courses_by_exclusion
)


@tag("unit")
class XAPIUtilsTests(XAPITestSetup):
    def test_remove_duplicates(self):
        """Test the removal of duplicate courses"""
        # Course with duplicates includes course-100 (2x) and course-101 (1x)
        unique_courses = remove_duplicates(self.courses_with_duplicates)
        # Should return only unique courses,
        # which are course-100 and course-101
        self.assertEqual(len(unique_courses), 2)
        self.assertIn(self.courses_with_duplicates[0], unique_courses)
        self.assertIn(self.courses_with_duplicates[1], unique_courses)

    def test_filter_statements_by_platform(self):
        """Test the filtering of statements by platform"""
        # 3 statements should be filtered, with 2 from the test platform,
        # and 1 from a different platform
        filtered = filter_statements_by_platform(
            statements=[
                self.enrolled_statement,
                self.completed_statement,
                self.in_progress_statement,
            ],
            platform=self.test_platform["test_platform"]
        )
        # Should return only statements from the test platform,
        # which are the enrolled and in-progress statements
        self.assertEqual(len(filtered), 2)
        self.assertIn(self.enrolled_statement, filtered)
        self.assertIn(self.in_progress_statement, filtered)
        self.assertNotIn(self.completed_statement, filtered)

    def test_filter_courses_by_exclusion(self):
        """Test the filtering of courses by exclusion"""
        filtered = filter_courses_by_exclusion(
            # Has course-100 (2x) and course-101 (1x)
            self.courses_with_duplicates,
            # Has course-100 to exclude
            self.courses_to_exclude,
        )

        # Should exclude all course 100,
        # keep only 1 course which is the course 101
        self.assertEqual(len(filtered), 1)
        self.assertIn(self.courses_with_duplicates[1], filtered)
        self.assertNotIn(self.courses_with_duplicates[0], filtered)
        self.assertNotIn(self.courses_with_duplicates[2], filtered)

    def test_process_course_statements(self):
        """Test the processing of lrs statements"""
        statements_resp = {
            "statements": [
                self.enrolled_statement,
            ]
        }
        processed_courses = process_course_statements(
            statements_resp, "enrolled"
        )

        result_course = processed_courses[0]

        self.assertEqual(
            result_course["course_id"], self.test_course_id["course-100"]
        )
        self.assertEqual(
            result_course["course_name"], self.test_courses["course-100"]
        )
        self.assertEqual(
            result_course["platform"], self.test_platform["test_platform"]
        )
        self.assertEqual(
            result_course["type"], "enrolled"
        )
        self.assertNotEqual(
            result_course["type"], "in-progress"
        )
        self.assertNotEqual(
            result_course["type"], "completed"
        )

    def test_process_course_statements_in_progress(self):
        """Test the processing of in-progress course statements"""
        statements_resp = {
            "statements": [
                self.in_progress_statement,
            ]
        }
        processed_courses = process_course_statements(
            statements_resp, "in-progress"
        )

        result_course = processed_courses[0]

        self.assertEqual(
            result_course["course_id"], self.test_course_id["course-100"]
        )
        self.assertEqual(
            result_course["course_name"], self.test_courses["course-100"]
        )
        self.assertEqual(
            result_course["platform"], self.test_platform["test_platform"]
        )
        self.assertEqual(
            result_course["type"], "in-progress"
        )
        self.assertNotEqual(
            result_course["type"], "completed"
        )
        self.assertNotEqual(
            result_course["type"], "enrolled"
        )

    @patch("xds_api.utils.xapi_utils.requests.get")
    def test_get_lrs_statements(self, mock_get):
        """Test the retrieval of LRS statements"""

        mock_get.return_value.json.return_value = {
            "statements": [
                self.enrolled_statement
            ]
        }

        result = get_lrs_statements(
            lrs_endpoint="https://test.example.com",
            username="testuser",
            password="testpass",
            user_identifier="test@example.com",
            verbs=COURSE_PROGRESS_VERBS["enrolled"],
        )

        self.assertEqual(len(result["statements"]), 1)
        self.assertEqual(result["statements"][0], self.enrolled_statement)
