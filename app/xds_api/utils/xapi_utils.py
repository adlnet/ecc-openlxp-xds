import json

import requests
from django.conf import settings

COURSE_PROGRESS_VERBS = {
    "completed": ["http://adlnet.gov/expapi/verbs/completed"],
    "enrolled": [
        "https://xapi.edlm/profiles/edlm-lms/concepts/verbs/enrolled"
    ],
    "in-progress": [
        "http://activitystrea.ms/schema/1.0/start",
        "http://id.tincanapi.com/verb/viewed",
    ],
}

COURSE_ACTIVITY_TYPES = {
    "course": "https://w3id.org/xapi/cmi5/activitytype/course",
    "lesson": "https://w3id.org/xapi/cmi5/activitytype/lesson",
}

PLATFORM = {
    "moodle": "moodle",
    "dote_portal": "dot&e portal"
}


def get_lrs_statements(
    lrs_endpoint, username, password, user_identifier, verbs, platform=None
):
    """This method handles a HTTP GET request to the LRS to fetch statements

    Args:
    lrs_endpoint: LRS endpoint
    username: The username for LRS authentication
    password: The password for LRS authentication
    user_identifier: User_identifier
    verbs: A list of verbs to filter the statements
    platform: The platform to filter the statements (optional)

    Returns:
    A dict containing all the fetched statements
    """

    # Construct the agent to get user's statements
    if settings.XAPI_USE_JWT:
        agent = {
            "account": {
                "homePage": settings.XAPI_ACTOR_ACCOUNT_HOMEPAGE,
                "name": user_identifier,
            }
        }
    else:
        agent = {"mbox": "mailto:" + user_identifier}

    headers = {
        "Content-Type": "application/json",
        "X-Experience-API-Version": "1.0.3",
    }

    all_statements = []

    # Fetch statements for each verb
    for verb in verbs:
        params = {
            "agent": json.dumps(agent),
            "verb": verb,
            "limit": "300",
        }

        resp = requests.get(
            f"{lrs_endpoint}/statements",
            params=params,
            headers=headers,
            auth=(username, password),
        )

        statements = resp.json().get("statements", [])
        # add the new statements to the all_statements list
        all_statements.extend(statements)

    # If there is platform filter, apply it
    if platform:
        all_statements = filter_statements_by_platform(
            all_statements, platform
        )

    return {"statements": all_statements}


def process_course_statements(statements_resp, statement_type):
    """This method processes course statements based on the statement_type

    Args:
        statements_resp: The response from the LRS containing statements
        statement_type: The type of statement to process
            (Such as:'completed', 'in-progress', 'enrolled')

    Returns:
        A list of processed course data
    """
    courses = []
    statements = statements_resp.get("statements", [])

    for statement in statements:
        context = statement.get("context", {})
        platform = context.get("platform", "Unknown Platform")
        timestamp = statement.get("timestamp", "")

        if statement_type == "in-progress":
            # For in-progress courses,
            # check contextActivities.parent to see the course
            context_activities = context.get("contextActivities", {})
            parent = context_activities.get("parent", [])
            for activity in parent:
                definition = activity.get("definition", {})
                activity_type = definition.get("type", "")

                if activity_type == COURSE_ACTIVITY_TYPES["course"]:
                    # Get course name from definition name
                    name_dic = definition.get("name", {})
                    course_name = name_dic.get("en", "Unknown Course")

                    course_data = {
                        "course_id": activity.get("id", ""),
                        "course_name": course_name,
                        "platform": platform,
                        "type": statement_type,
                        "timestamp": timestamp,
                    }
                    courses.append(course_data)
        else:
            # For other statement types, check main object
            activity = statement.get("object", {})
            definition = activity.get("definition", {})
            activity_type = definition.get("type", "")

            # Skip when the statement type is completed but not a course
            # (most likely, a lesson which we need to skip)
            if (
                statement_type == "completed"
                and activity_type != COURSE_ACTIVITY_TYPES["course"]
            ):
                continue

            # Get course name from definition name
            name_dic = definition.get("name", {})
            course_name = name_dic.get("en", "Unknown Course")

            course_data = {
                "course_id": activity.get("id", ""),
                "course_name": course_name,
                "platform": platform,
                "type": statement_type,
                "timestamp": timestamp,
            }
            courses.append(course_data)

    return courses


def remove_duplicates(courses):
    """This method removes duplicate courses"""
    ids = set()
    unique_courses = []

    for course in courses:
        if course["course_id"] not in ids:
            ids.add(course["course_id"])
            unique_courses.append(course)

    return unique_courses


def filter_statements_by_platform(statements, platform):
    """This method filters statements by platform"""

    if not platform:
        return statements

    filtered_statements = []

    for statement in statements:
        context = statement.get("context", {})
        statement_platform = context.get("platform", "")
        if statement_platform.lower() == platform.lower():
            filtered_statements.append(statement)

    return filtered_statements


def filter_courses_by_exclusion(courses_to_filter, courses_to_exclude):
    """This method removes courses from the first group
    if they exist in the second group

    This method can be used to filter out unwanted courses from a list,
    such as filter out completed courses from in-progress courses.

    Args:
        courses_to_filter: The list of courses to filter
        courses_to_exclude: The list of courses to exclude

    Returns:
        A list of courses from courses_to_filter that
        don't exist in courses_to_exclude
    """

    courses_to_exclude_ids = set()
    for course in courses_to_exclude:
        courses_to_exclude_ids.add(course["course_id"])

    filtered_courses = []
    for course in courses_to_filter:
        if course["course_id"] not in courses_to_exclude_ids:
            filtered_courses.append(course)

    return filtered_courses
