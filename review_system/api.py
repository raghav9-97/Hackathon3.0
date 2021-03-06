from tastypie.resources import ModelResource
from models import Reviews
from tastypie.utils.urls import trailing_slash
from django.conf.urls import url
from utils import near_by_places
from utils import find_route
from tastypie.utils.timezone import now
from models import Map
from django.contrib.auth.models import User
import json

API_BASE_URL = 'api/map/'
USER_REVEWS_API = 'api/user/'


# location = '22.7304794,75.8708128'
destination = '22.7304794,75.8708128'


class MapResource(ModelResource):
    class Meta:
        queryset = Map.objects.all()
        # review_query_set = Reviews.objects.all()
        resource_name = 'map'
        resource_name_user = 'user'

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/find%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('find_route'), name="api_find_route"),
            url(r"^(?P<resource_name>%s)/route%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('find_near_by_location'), name="api_find_near_by_location"),
            url(r"^(?P<resource_name>%s)/review%s$" %
                (self._meta.resource_name_user, trailing_slash()),
                self.wrap_view('store_user_reviews'), name="api_store_user_reviews"),
            url(r"^(?P<resource_name>%s)/get_review%s$" %
                (self._meta.resource_name_user, trailing_slash()),
                self.wrap_view('get_user_review'), name="api_get_user_review")
        ]

    def get_user_review(self, request, *args, **kwargs):
        if request:
            body = json.loads(request.body)
            place_id = body['place_id']
            try:
                review_query = Reviews.objects.get(place_id__place_id__exact=place_id)
                review = review_query.review
                rating = review_query.rating
            except Reviews.DoesNotExist:
                review = "This kind of nice"
                rating = 4.0
            data = {'rating': rating, 'review': review}
            return self.create_response(request, {
                'data': data
            })

    def store_user_reviews(self, request, *args, **kwargs):
        if request:
            body = json.loads(request.body)
            rating = body['rating']
            review = body['review']
            # print rating, review
            review_object = Reviews.objects.create(review=review, rating=rating, time=now())
            review_object.save()
            return self.create_response(request, {
                'status': "success"
            })

    def find_near_by_location(self, request, *args, **kwargs):
        if request:
            body = json.loads(request.body)
            # print body
            location = str(body['lat']) + ',' + str(body['lng'])
            resp = near_by_places(location)
            # print resp
            if resp['status'] == u'OK':
                result = resp['results']
                # print result
                locations = []
                place_ids = []
                custom_reviews = ["Clean and Tidy", "Dirty and Unhygienic", "Water supply is irregular",
                                  "Noisy Environment", "Incomplete Construction", "Entire place smells bad",
                                  "Ideal for everyone", "Not suitable for women", "Excessive Charge",
                                  "Remotely located"]
                custom_ratings = [5, 1, 2.5, 3, 2.5, 3, 4, 3, 3.5, 3]
                for i in range(10):
                    # print result[i]
                    place_id = result[i]['place_id']
                    address = result[i]['vicinity']
                    location = result[i]['geometry']['location']
                    try:
                        map_query = Map.objects.get(place_id=place_id)
                    except Map.DoesNotExist:
                        map_query = Map.objects.create(place_id=place_id, address=address, location=location)
                        map_query.save()
                        review_query = Reviews.objects.create(place_id=map_query,
                                                              rating=custom_ratings[i],
                                                              review=custom_reviews[i],
                                                              user_locations=location,
                                                              time=now())
                        review_query.save()
                    locations.append(location)
                    place_ids.append(place_id)
                    # print location
                # print locations
                return self.create_response(request, {
                    'status': "success",
                    'location': locations,
                    'place_id': place_ids
                })

    def find_route(self, request, *args, **kwargs):
        if request:
            body = json.loads(request.body)
            # print body
            location = str(body['lat']) + ',' + str(body['lng'])
            resp = find_route(location, destination)
            if resp:
                print resp
                return self.create_response(request, {
                    'status': "success"
                })

    def _post_resp(self, rel_url, data, res_type):
        url = API_BASE_URL + rel_url
        resp = self.api_client.post(
            url,
            # authentication=self.get_credentials(self.user),
            data=data
        )
        res_type(resp)
        return self.deserialize(resp)
