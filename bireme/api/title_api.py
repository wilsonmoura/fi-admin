# coding: utf-8
from django.conf import settings
from django.conf.urls import patterns, url, include

from django.contrib.contenttypes.models import ContentType

from tastypie.serializers import Serializer
from tastypie.utils import trailing_slash
from tastypie import fields

from title.models import *
from isis_serializer import ISISSerializer

from tastypie_custom import CustomResource

from main.models import Descriptor
from title.field_definitions import field_tag_map

import requests
import urllib
import json

TITLE_VARIANCE_LABELS = (
    ('230', 'parallel_titles'),
    ('235', 'shortened_parallel_titles'),
    ('240', 'other_titles'),
)

AUDIT_LABELS = (
    ('510', 'has_edition'),
    ('520', 'is_edition'),
    ('530', 'has_subseries'),
    ('540', 'is_subseries'),
    ('550', 'has_supplement'),
    ('560', 'is_supplement'),
    ('610', 'continuation'),
    ('620', 'partial_continuation'),
    ('650', 'absorbed'),
    ('660', 'absorbed_in_part'),
    ('670', 'subdivision'),
    ('680', 'fusion'),
    ('710', 'continued_by'),
    ('720', 'continued_in_part_by'),
    ('750', 'absorbed_by'),
    ('760', 'absorbed_in_part_by'),
    ('770', 'subdivided'),
    ('780', 'merged'),
    ('790', 'to_form'),
)

class TitleResource(CustomResource):

    class Meta:
        queryset = Title.objects.all()
        allowed_methods = ['get']
        serializer = ISISSerializer(formats=['json', 'xml', 'isis_id'], field_tag=field_tag_map)
        resource_name = 'title'
        filtering = {
            'update_date': ('gte', 'lte'),
            'status': 'exact',
        }
        include_resource_uri = True

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_search'), name="api_get_search"),
        ]

    def get_search(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        q = request.GET.get('q', '')
        fq = request.GET.get('fq', '')
        start = request.GET.get('start', '')
        count = request.GET.get('count', '')
        lang = request.GET.get('lang', 'pt')
        op = request.GET.get('op', 'search')
        id = request.GET.get('id', '')
        sort = request.GET.get('sort', 'created_date desc')

        # filter result by approved resources (status=1)
        if fq != '':
            fq = '(status:1 AND django_ct:title.title*) AND %s' % fq
        else:
            fq = '(status:1 AND django_ct:title.title*)'

        # url
        search_url = "%siahx-controller/" % settings.SEARCH_SERVICE_URL

        search_params = {'site': 'fi', 'col': 'main', 'op': op, 'output': 'site', 'lang': lang,
                         'q': q, 'fq': fq, 'start': start, 'count': count, 'id': id, 'sort': sort}

        r = requests.post(search_url, data=search_params)

        self.log_throttled_access(request)
        return self.create_response(request, r.json())

    def dehydrate(self, bundle):
        c_type = ContentType.objects.get_for_model(bundle.obj)

        descriptors = Descriptor.objects.filter(object_id=bundle.obj.id, content_type=c_type)
        title_variance = TitleVariance.objects.filter(title=bundle.obj.id)
        bvs_specialties = BVSSpecialty.objects.filter(title=bundle.obj.id)
        index_range = IndexRange.objects.filter(title=bundle.obj.id)
        audits = Audit.objects.filter(title=bundle.obj.id)
        new_url = OnlineResources.objects.filter(title=bundle.obj.id)

        # add fields to output
        bundle.data['MFN'] = bundle.obj.id
        bundle.data['descriptors'] = [{'text': descriptor.text} for descriptor in descriptors] # field tag 440

        # field tags 230 and 240
        if title_variance:
            for label in TITLE_VARIANCE_LABELS:
                bundle.data[label[1]] = []

            for title in title_variance:
                text = title.label if title.label else ''
                text += '^a'+title.initial_year if title.initial_year else ''
                text += '^v'+title.initial_volume if title.initial_volume else ''
                text += '^n'+title.initial_number if title.initial_number else ''
                text += '^i'+title.issn if title.issn else ''
                bundle.data[dict(TITLE_VARIANCE_LABELS)[title.type]] += [{'text': text}]

        # field tag 436
        if bvs_specialties:
            bundle.data['bvs_specialties'] = []
            for bvs_specialty in bvs_specialties:
                text = '^a'+bvs_specialty.bvs if bvs_specialty.bvs else ''
                text += '^b'+bvs_specialty.thematic_area if bvs_specialty.thematic_area else ''
                bundle.data['bvs_specialties'] += [{'text': text}]

        # field tag 450
        if index_range:
            bundle.data['index_range'] = []
            for index in index_range:
                text = index.index_code if index.index_code else ''
                text += '^a'+index.initial_volume if index.initial_volume else ''
                text += '^b'+index.initial_number if index.initial_number else ''
                text += '^c'+index.initial_date if index.initial_date else ''
                text += '^d'+index.final_volume if index.final_volume else ''
                text += '^e'+index.final_number if index.final_number else ''
                text += '^f'+index.final_date if index.final_date else ''
                bundle.data['index_range'] += [{'text': text}]

        # field tags 510, 520, 530, 540, 550, 560, 610, 620, 650,
        # 660, 670, 680, 710, 720, 750, 760, 770, 780 and 790
        if audits:
            for label in AUDIT_LABELS:
                bundle.data[label[1]] = []

            for audit in audits:
                text = audit.label if audit.label else ''
                text += '^i'+audit.issn if audit.issn else ''
                bundle.data[dict(AUDIT_LABELS)[audit.type]] += [{'text': text}]

        # field tag 999
        if new_url:
            bundle.data['online'] = []

            for data in new_url:
                text = data.issn_online if data.issn_online else ''
                text += '^a'+data.access_type if data.access_type else ''
                text += '^b'+data.url if data.url else ''
                text += '^c'+data.owner.owner if data.owner else ''
                text += '^d'+data.access_control if data.access_control else ''
                text += '^e'+data.initial_period if data.initial_period else ''
                text += '^f'+data.final_period if data.final_period else ''

                if data.notes:
                    if isinstance(data.notes, basestring) and "\r\n" in data.notes:
                        lines = ''
                        for line in data.notes.split('\r\n'):
                            if line:
                                lines += line + ' ' if line[-1] == '.' else line + '. '
                        if lines:
                            text += '^g'+lines
                    else:
                        text += '^g'+data.notes

                bundle.data['online'] += [{'text': text}]

        return bundle
