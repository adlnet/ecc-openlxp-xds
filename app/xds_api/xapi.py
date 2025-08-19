import jwt
import uuid


VERB_WHITELIST = {
    "https://w3id.org/xapi/tla/verbs/explored",
    "https://w3id.org/xapi/acrossx/verbs/searched",
    "http://activitystrea.ms/save",
    "https://xapi.edlm/profiles/edlm-ecc/concepts/verbs/curated",
    "http://adlnet.gov/expapi/verbs/shared",
    "http://id.tincanapi.com/verb/viewed",
    "https://xapi.edlm/profiles/edlm-lms/concepts/verbs/enrolled",
    "http://activitystrea.ms/schema/1.0/start",
    "http://adlnet.gov/expapi/verbs/completed"
}


def filter_allowed_statements(statements):
    allowed_statements = []
    for st in statements:
        verb_iri = st.get("verb", {}).get("id")
        if verb_iri in VERB_WHITELIST:
            allowed_statements.append(st)
    return allowed_statements


def actor_with_mbox(email):
    return {
        "objectType": "Agent",
        "mbox": f"mailto:{email}"
    }


def actor_with_account(home_page, name):
    return {
        "objectType": "Agent",
        "account": {
            "homePage": home_page,
            "name": name
        }
    }


def jwt_account_name(request, fields):
    encoded_auth_header = request.headers["Authorization"]
    jwt_payload = jwt.decode(encoded_auth_header.split("Bearer ")[1],
                             options={"verify_signature": False})
    return next(
        (jwt_payload.get(f) for f in fields if jwt_payload.get(f)),
        None
    )


def get_or_set_registration_uuid(request):
    if 'registration_uuid' not in request.session:
        # Generate a new UUID and store it in the session
        request.session['registration_uuid'] = str(uuid.uuid4())
    return request.session['registration_uuid']
