"""Governance prompts & constant policy messages shared across modules."""

SECURITY_BLOCKED_MESSAGE = (
    "This request violates the security policy and has been blocked."
)

CUBE_ONLY_POLICY_MESSAGE = (
    "MetricMind only supports analytics through the Cube.dev Semantic API. "
    "Direct SQL access is disabled by governance policy."
)

EXPENSIVE_QUERY_SUGGESTION_MESSAGE = (
    "This request may return too much data and was blocked for performance reasons. "
    "Please add filters such as a date range (e.g. 'last month'), region, category, "
    "or product to narrow the scope."
)

UNSUPPORTED_OPERATION_MESSAGE = (
    "This operation is not supported. MetricMind only answers business analytics "
    "questions through the governed Cube.dev API."
)

ALLOWED_ROUTES_THROUGH_GOVERNANCE = {"/ask", "/semantic-search", "/explain", "/governance/validate"}

CUBE_API_ENDPOINT = "/cubejs-api/v1/load"
