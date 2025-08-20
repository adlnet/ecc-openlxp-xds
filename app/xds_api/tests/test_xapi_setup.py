from django.test import TestCase
from xds_api.utils.xapi_utils import (
    COURSE_ACTIVITY_TYPES,
    COURSE_PROGRESS_VERBS
)


class XAPITestSetup(TestCase):
    def setUp(self):
        """Set up test data for XAPI related tests"""
        self.test_course_id = {
            "course-100": "https://testmytest.com/course/view.php?id=100",
            "course-101": "https://testmytest.com/course/view.php?id=101"
        }

        self.test_platform = {
            "test_platform": "test_platform",
            "another_platform": "another_platform"
        }

        self.test_courses = {
            "course-100": "Test Course 1",
            "course-101": "Test Course 2"
        }

        self.type_enrolled = "enrolled"

        self.type_completed = "completed"

        self.type_in_progress = "in-progress"

        self.enrolled_statement = {
            "object": {
                "id": self.test_course_id["course-100"],
                "definition": {
                    "type": COURSE_ACTIVITY_TYPES["course"],
                    "name": {
                        "en": self.test_courses["course-100"]
                    }
                },
            },
            "verb": {
                "id": COURSE_PROGRESS_VERBS["enrolled"][0]
            },
            "timestamp": "2025-08-15T21:20:00.000Z",
            "context": {
                "platform": self.test_platform["test_platform"]
            },
        }

        self.completed_statement = {
            "object": {
                "id": self.test_course_id["course-101"],
                "definition": {
                    "type": COURSE_ACTIVITY_TYPES["course"],
                    "name": {
                        "en": self.test_courses["course-101"]
                    }
                },
            },
            "verb": {
                "id": COURSE_PROGRESS_VERBS["completed"][0]
            },
            "timestamp": "2025-08-16T21:20:00.000Z",
            "context": {
                "platform": self.test_platform["another_platform"]
            },
        }

        self.in_progress_statement = {
            "object": {
                "id": "https://testmytest.com/attempt=17&cmid=50",
                "definition": {
                    "type": "http://adlnet.gov/expapi/activities/assessment",
                    "name": {
                        "en": "Quiz 1"
                    }
                },
            },
            "verb": {
                "id": COURSE_PROGRESS_VERBS["in-progress"][0]
            },
            "timestamp": "2025-08-15T19:37:21.000Z",
            "context": {
                "platform": self.test_platform["test_platform"],
                "contextActivities": {
                    "parent": [
                        {
                            "id": self.test_course_id["course-100"],
                            "definition": {
                                "type": COURSE_ACTIVITY_TYPES["course"],
                                "name": {
                                    "en": self.test_courses["course-100"]
                                },
                            },
                        }
                    ]
                },
            },
        }

        self.courses_with_duplicates = [
            {
                "course_id": self.test_course_id["course-100"],
                "course_name": self.test_courses["course-100"],
                "platform": self.test_platform["test_platform"],
                "type": self.type_enrolled,
                "timestamp": "2025-08-15T21:10:00.000Z"
            },
            {
                "course_id": self.test_course_id["course-101"],
                "course_name": self.test_courses["course-101"],
                "platform": self.test_platform["test_platform"],
                "type": self.type_completed,
                "timestamp": "2025-08-16T21:50:10.000Z"
            },
            {
                "course_id": self.test_course_id["course-100"],
                "course_name": self.test_courses["course-100"],
                "platform": self.test_platform["test_platform"],
                "type": self.type_enrolled,
                "timestamp": "2025-08-18T21:25:00.000Z"
            },
        ]

        self.courses_to_exclude = [
            {
                "course_id": self.test_course_id["course-100"],
                "course_name": self.test_courses["course-100"],
                "platform": self.test_platform["test_platform"],
                "type": self.type_completed,
                "timestamp": "2025-08-18T21:22:00.000Z",
            }
        ]
