from django.conf import settings

from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.authentication import ApiKeyAuthentication, Authentication
from tastypie.resources import Resource, ModelResource
from tastypie.validation import Validation

from artbase.models import ArtworkStub
from support.models import CommunityCampaign, NewDonation
from blocks.models import Block
from utils.payments import call_authorizedotnet


class CampaignResource(ModelResource):
    amount_raised = fields.DecimalField(attribute='amount_raised', null=True)
    formatted_amount_raised = fields.CharField(attribute='formatted_amount_raised', null=True)
    formatted_amount_goal = fields.CharField(attribute='formatted_amount_goal', null=True)
    percent_raised = fields.IntegerField(attribute='percent_raised', null=True)
    days_left = fields.IntegerField(attribute='days_left', null=True)

    class Meta:
        queryset = CommunityCampaign.objects.all()
        resource_name = 'campaign'
        allowed_methods = ['get']
        authorization= Authorization()
        authentication = Authentication()
        filtering = {
            'year': ('exact'),
        }

class BlockResource(ModelResource):
    class Meta:
        queryset = Block.objects.all()
        resource_name = 'block'
        allowed_methods = ['get']
        authorization = Authorization()
        authentication = Authentication()
        filtering = {
            'ident': ('exact'),
        }

class QuickStatsResource(Resource):
    class Meta:
        resource_name = 'quickstats'
        authentication = ApiKeyAuthentication()

    def dehydrate(self, bundle):
        bundle.data['online_now_ids'] = len(bundle.request.online_now_ids)
        bundle.data['online_now'] = [u.get_profile() for u in bundle.request.online_now]

        stub = ArtworkStub.objects.filter(status='approved').exclude(image_large='artbase/images/rhizome_art_default.png').order_by('?')[0]

        bundle.data['random_image'] = {
            'abs_path': '%s%s' % (settings.MEDIA_URL, stub.image_large),
            'title': stub.title,
            'byline': stub.byline,
        }
        return bundle

    def detail_uri_kwargs(self, bundle_or_obj):
        return {'pk': 0}

    def get_object_list(self, request):
        return [None]

    def obj_get_list(self, request=None, **kwargs):
        return self.get_object_list(request)

    def obj_get(self, request=None, **kwargs):
        return None

class CreateDonationResource(ModelResource):
    class Meta:
        queryset = NewDonation.objects.all()
        resource_name = 'donation'
        allowed_methods = ['post']
        authorization= Authorization()
        authentication = Authentication()

    def hydrate(self, bundle):
        return self.process_payment(bundle)

    def obj_create(self, bundle, **kwargs):
        if bundle.request.user.is_authenticated():
            kwargs['user'] = bundle.request.user
        return super(CreateDonationResource, self).obj_create(bundle, **kwargs)

    def process_payment(self, bundle):
        verify_call = call_authorizedotnet(
            bundle.data.get('amount'), 
            bundle.data.get('card_number'), 
            '%s-%s' % (bundle.data.get('exp_date_0'), bundle.data.get('exp_date_1')),
            bundle.data.get('cvv'),
            '',
            '',
            '',
            '', 
            '',
            bundle.data.get('first_name'),
            bundle.data.get('last_name'),
            '',
            bundle.data.get('email'),
            'Donation', 
        )

        if verify_call.split('|')[0] == '1':
            bundle.data['authorize_transaction_id'] = verify_call.split('|')[6]
            bundle.data['authorize_transaction_raw_response'] = verify_call
        else:   
            bundle.errors[self._meta.resource_name] = verify_call.split('|')[3]
        return bundle
