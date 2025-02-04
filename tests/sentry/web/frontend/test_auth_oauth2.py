from collections import namedtuple
from unittest import mock
from urllib.parse import parse_qs, urlencode, urlparse

from django.urls import reverse
from exam import fixture

from sentry.auth.providers.oauth2 import OAuth2Callback, OAuth2Login, OAuth2Provider
from sentry.models import AuthProvider
from sentry.testutils import AuthProviderTestCase
from sentry.testutils.silo import control_silo_test
from sentry.utils import json


class DummyOAuth2Login(OAuth2Login):
    authorize_url = "http://example.com/authorize_url"
    client_id = "my_client_id"
    scope = "test_scope"


class DummyOAuth2Callback(OAuth2Callback):
    access_token_url = "http://example.com/token_url"
    client_id = "my_client_id"
    client_secret = "my_client_secret"


class DummyOAuth2Provider(OAuth2Provider):
    name = "dummy"

    def get_refresh_token_url(self) -> str:
        pass

    def build_config(self, state):
        pass

    def get_auth_pipeline(self):
        return [DummyOAuth2Login(), DummyOAuth2Callback()]

    def build_identity(self, state):
        return state["data"]


MockResponse = namedtuple("MockResponse", ["headers", "content"])


@control_silo_test
class AuthOAuth2Test(AuthProviderTestCase):
    provider = DummyOAuth2Provider
    provider_name = "oauth2_dummy"

    def setUp(self):
        super().setUp()
        self.auth_provider = AuthProvider.objects.create(
            provider=self.provider_name, organization=self.organization
        )

    @fixture
    def login_path(self):
        return reverse("sentry-auth-organization", args=[self.organization.slug])

    @fixture
    def sso_path(self):
        return reverse("sentry-auth-sso")

    def initiate_oauth_flow(self, http_host=None):
        kwargs = {}
        if http_host is not None:
            kwargs["HTTP_HOST"] = http_host
        else:
            http_host = "testserver"

        resp = self.client.post(self.login_path, {"init": True}, **kwargs)

        assert resp.status_code == 302
        redirect = urlparse(resp.get("Location", ""))
        query = parse_qs(redirect.query)

        assert redirect.path == "/authorize_url"
        assert query["redirect_uri"][0] == f"http://{http_host}/auth/sso/"
        assert query["client_id"][0] == "my_client_id"
        assert "state" in query

        return query["state"][0]

    @mock.patch("sentry.auth.providers.oauth2.safe_urlopen")
    def initiate_callback(self, state, auth_data, urlopen, expect_success=True, **kwargs):
        headers = {"Content-Type": "application/json"}
        urlopen.return_value = MockResponse(headers, json.dumps(auth_data))

        query = urlencode({"code": "1234", "state": state})
        resp = self.client.get(f"{self.sso_path}?{query}", **kwargs)

        if expect_success:
            assert resp.status_code == 200
            assert urlopen.called
            data = urlopen.call_args[1]["data"]

            http_host = "testserver"
            if "HTTP_HOST" in kwargs:
                http_host = kwargs["HTTP_HOST"]

            assert data == {
                "grant_type": "authorization_code",
                "code": "1234",
                "redirect_uri": f"http://{http_host}/auth/sso/",
                "client_id": "my_client_id",
                "client_secret": "my_client_secret",
            }

        return resp

    def test_oauth2_flow(self):
        auth_data = {"id": "oauth_external_id_1234", "email": self.user.email}

        state = self.initiate_oauth_flow()
        auth_resp = self.initiate_callback(state, auth_data)

        assert auth_resp.context["existing_user"] == self.user

    def test_oauth2_flow_customer_domain(self):
        HTTP_HOST = "albertos-apples.testserver"
        auth_data = {"id": "oauth_external_id_1234", "email": self.user.email}

        state = self.initiate_oauth_flow(http_host=HTTP_HOST)
        auth_resp = self.initiate_callback(state, auth_data, HTTP_HOST=HTTP_HOST)

        assert auth_resp.context["existing_user"] == self.user

    def test_state_mismatch(self):
        auth_data = {"id": "oauth_external_id_1234", "email": self.user.email}

        self.initiate_oauth_flow()
        auth_resp = self.initiate_callback("bad", auth_data, expect_success=False, follow=True)

        messages = list(auth_resp.context["messages"])
        assert len(messages) == 1
        assert str(messages[0]).startswith("Authentication error")

    def test_response_errors(self):
        auth_data = {"error_description": "Mock failure"}

        state = self.initiate_oauth_flow()
        auth_resp = self.initiate_callback(state, auth_data, expect_success=False, follow=True)

        messages = list(auth_resp.context["messages"])
        assert len(messages) == 1
        assert str(messages[0]) == "Authentication error: Mock failure"

        auth_data = {"error": "its broke yo"}

        state = self.initiate_oauth_flow()
        auth_resp = self.initiate_callback(state, auth_data, expect_success=False, follow=True)

        messages = list(auth_resp.context["messages"])
        assert len(messages) == 1
        assert str(messages[0]).startswith("Authentication error")
