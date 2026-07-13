import wifi
import ujson
import requests

class MapsAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "User-Agent": "Tildagon GPSUMap 0.0.1"
        }

    def _request(self, method, path, data=None):
        url = self.base_url + path

        try:

            # Prepare request
            if data is not None:
                resp = requests.request(
                    method,
                    url,
                    headers=self.headers,
                    data=ujson.dumps(data)
                )
            else:
                resp = requests.request(
                    method,
                    url,
                    headers=self.headers
                )
        except Exception:
            print("Request error")

        # Parse response
        try:
            result = resp.json()
        except Exception:
            result = resp.text
            print("Parse error")

        status = resp.status_code
        resp.close()

        return status, result

    # -------------------------
    # Locations
    # -------------------------

    def list_locations(self, page=0, size=20):
        return self._request(
            "GET",
            "/api/locations?page={}&size={}".format(page, size)
        )

    def get_location(self, osm_id):
        return self._request(
            "GET",
            "/api/locations/{}".format(osm_id)
        )

    def create_location(self, name, latitude, longitude, description=None):
        body = {
            "name": name,
            "latitude": latitude,
            "longitude": longitude
        }

        if description is not None:
            body["description"] = description

        return self._request(
            "POST",
            "/api/locations",
            body
        )

    def update_location(self, edit_token, name, latitude, longitude, description=None):
        body = {
            "name": name,
            "latitude": latitude,
            "longitude": longitude
        }

        if description is not None:
            body["description"] = description

        return self._request(
            "PUT",
            "/api/locations/{}".format(edit_token),
            body
        )

    def delete_location(self, edit_token):
        return self._request(
            "DELETE",
            "/api/locations/{}".format(edit_token)
        )

    # -------------------------
    # Badge Locations
    # -------------------------

    def list_badge_locations(self, page=0, size=20):
        return self._request(
            "GET",
            "/api/badgeLocations?page={}&size={}".format(page, size)
        )

    def get_badge_location(self, osm_id):
        return self._request(
            "GET",
            "/api/badgeLocations/{}".format(osm_id)
        )

    def create_badge_location(self, name, latitude, longitude, description=None):
        body = {
            "name": name,
            "latitude": latitude,
            "longitude": longitude
        }

        if description is not None:
            body["description"] = description

        print(body)

        return self._request(
            "POST",
            "/api/badgeLocations",
            body
        )

    def update_badge_location(self, edit_token, name, latitude, longitude, description=None):
        body = {
            "name": name,
            "latitude": latitude,
            "longitude": longitude
        }

        if description is not None:
            body["description"] = description

        return self._request(
            "PUT",
            "/api/badgeLocations/{}".format(edit_token),
            body
        )

    def delete_badge_location(self, edit_token):
        return self._request(
            "DELETE",
            "/api/badgeLocations/{}".format(edit_token)
        )
