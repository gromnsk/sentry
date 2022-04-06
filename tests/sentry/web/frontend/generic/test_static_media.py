import os

from django.test.utils import override_settings

from sentry.testutils import TestCase
from sentry.utils.assets import get_frontend_app_asset_url
from sentry.web.frontend.generic import FOREVER_CACHE, NEVER_CACHE, NO_CACHE


class StaticMediaTest(TestCase):
    @override_settings(DEBUG=False)
    def test_basic(self):
        url = "/_static/sentry/js/ads.js"
        response = self.client.get(url)
        assert response.status_code == 200, response
        assert response["Cache-Control"] == NEVER_CACHE
        assert response["Vary"] == "Accept-Encoding"
        assert response["Access-Control-Allow-Origin"] == "*"
        assert "Content-Encoding" not in response
        assert b"".join(response.streaming_content)

    @override_settings(DEBUG=False)
    def test_versioned(self):
        url = "/_static/1234567890/sentry/js/ads.js"
        response = self.client.get(url)
        assert response.status_code == 200, response
        assert response["Cache-Control"] == FOREVER_CACHE
        assert response["Vary"] == "Accept-Encoding"
        assert response["Access-Control-Allow-Origin"] == "*"
        assert "Content-Encoding" not in response
        assert b"".join(response.streaming_content)

        url = "/_static/a43db3b08ddd4918972f80739f15344b/sentry/js/ads.js"
        response = self.client.get(url)
        assert response.status_code == 200, response
        assert response["Cache-Control"] == FOREVER_CACHE
        assert response["Vary"] == "Accept-Encoding"
        assert response["Access-Control-Allow-Origin"] == "*"
        assert "Content-Encoding" not in response
        assert b"".join(response.streaming_content)

        with override_settings(DEBUG=True):
            response = self.client.get(url)
            assert response.status_code == 200, response
            assert response["Cache-Control"] == NEVER_CACHE
            assert response["Vary"] == "Accept-Encoding"
            assert response["Access-Control-Allow-Origin"] == "*"
            assert b"".join(response.streaming_content)

    @override_settings(DEBUG=False)
    def test_frontend_app_assets(self):
        """
        static assets that do not have versioned filenames/paths
        """

        # non-existant dist file
        response = self.client.get("/_static/dist/sentry/invalid.js")
        assert response.status_code == 404, response

        dist_path = os.path.join("src", "sentry", "static", "sentry", "dist")
        os.makedirs(dist_path, exist_ok=True)

        try:
            with open(os.path.join(dist_path, "test.js"), "a"):
                url = get_frontend_app_asset_url("sentry", "test.js", cache_bust=True)
                assert "?v=" in url

                response = self.client.get(url)
                assert response.status_code == 200, response
                assert response["Cache-Control"] == NO_CACHE
                assert response["Vary"] == "Accept-Encoding"
                assert response["Access-Control-Allow-Origin"] == "*"
                assert "Content-Encoding" not in response
                assert not b"".join(response.streaming_content)

            with override_settings(DEBUG=True):
                response = self.client.get(url)
                assert response.status_code == 200, response
                assert response["Cache-Control"] == NEVER_CACHE
                assert response["Vary"] == "Accept-Encoding"
                assert response["Access-Control-Allow-Origin"] == "*"
                assert not b"".join(response.streaming_content)
        finally:
            try:
                os.unlink(os.path.join(dist_path, "test.js"))
            except Exception:
                pass

    @override_settings(DEBUG=False)
    def test_no_cors(self):
        url = "/_static/sentry/images/favicon.ico"
        response = self.client.get(url)
        assert response.status_code == 200, response
        assert response["Cache-Control"] == NEVER_CACHE
        assert response["Vary"] == "Accept-Encoding"
        assert "Access-Control-Allow-Origin" not in response
        assert "Content-Encoding" not in response
        assert b"".join(response.streaming_content)

    def test_404(self):
        url = "/_static/sentry/app/thisfiledoesnotexistlol.js"
        response = self.client.get(url)
        assert response.status_code == 404, response

    def test_gzip(self):
        url = "/_static/sentry/js/ads.js"
        response = self.client.get(url, HTTP_ACCEPT_ENCODING="gzip,deflate")
        assert response.status_code == 200, response
        assert response["Vary"] == "Accept-Encoding"
        assert "Content-Encoding" not in response
        assert b"".join(response.streaming_content)

        try:
            open("src/sentry/static/sentry/js/ads.js.gz", "a").close()

            # Not a gzip Accept-Encoding, so shouldn't serve gzipped file
            response = self.client.get(url, HTTP_ACCEPT_ENCODING="lol")
            assert response.status_code == 200, response
            assert response["Vary"] == "Accept-Encoding"
            assert "Content-Encoding" not in response
            assert b"".join(response.streaming_content)

            response = self.client.get(url, HTTP_ACCEPT_ENCODING="gzip,deflate")
            assert response.status_code == 200, response
            assert response["Vary"] == "Accept-Encoding"
            assert response["Content-Encoding"] == "gzip"
            assert not b"".join(response.streaming_content)
        finally:
            try:
                os.unlink("src/sentry/static/sentry/js/ads.js.gz")
            except Exception:
                pass

    def test_file_not_found(self):
        url = "/_static/sentry/app/xxxxxxxxxxxxxxxxxxxxxxxx.js"
        response = self.client.get(url)
        assert response.status_code == 404, response

    def test_bad_access(self):
        url = "/_static/sentry/images/../../../../../etc/passwd"
        response = self.client.get(url)
        assert response.status_code == 404, response

    def test_directory(self):
        url = "/_static/sentry/images/"
        response = self.client.get(url)
        assert response.status_code == 404, response

        url = "/_static/sentry/images"
        response = self.client.get(url)
        assert response.status_code == 404, response
