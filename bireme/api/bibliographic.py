# coding: utf-8
from django.conf import settings
from django.conf.urls import patterns, url, include
from django.conf import settings
from copy import copy

from django.contrib.contenttypes.models import ContentType

from tastypie.serializers import Serializer
from tastypie.utils import trailing_slash
from tastypie import fields

from biblioref.models import Reference, ReferenceSource, ReferenceAnalytic
from attachments.models import Attachment
from isis_serializer import ISISSerializer

from tastypie_custom import CustomResource

from main.models import Descriptor, ResourceThematic
from biblioref.field_definitions import field_tag_map

import os
import requests
import urllib
import json


class ReferenceResource(CustomResource):
    class Meta:
        queryset = Reference.objects.all()
        allowed_methods = ['get']
        serializer = ISISSerializer(formats=['json', 'xml', 'isis_id'], field_tag=field_tag_map)
        resource_name = 'bibliographic'
        filtering = {
            'update_date': ('gte', 'lte'),
            'status': 'exact',
        }
        include_resource_uri = True

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_search'), name="api_get_search"),
            url(r"^(?P<resource_name>%s)/get_last_id%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_last_id'), name="api_get_last_id"),
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
            fq = '(status:1 AND django_ct:biblioref.reference*) AND %s' % fq
        else:
            fq = '(status:1 AND django_ct:biblioref.reference*)'

        # url
        search_url = "%siahx-controller/" % settings.SEARCH_SERVICE_URL

        search_params = {'site': 'fi', 'col': 'main', 'op': op, 'output': 'site', 'lang': lang,
                         'q': q, 'fq': fq, 'start': start, 'count': count, 'id': id, 'sort': sort}

        r = requests.post(search_url, data=search_params)

        self.log_throttled_access(request)
        return self.create_response(request, r.json())

    def full_dehydrate(self, bundle, for_list=False):
        # complete bundle fields with child fields. Ex. Analytic and Source fields to Reference

        # first populate bundle with Reference fields
        bundle = super(ReferenceResource, self).full_dehydrate(bundle)

        # Check type of Reference to add additional fields to bundle
        reference_id = bundle.obj.id
        if 'a' in bundle.data['treatment_level']:
            obj = ReferenceAnalytic.objects.get(pk=reference_id)
        else:
            obj = ReferenceSource.objects.get(pk=reference_id)

        # Add additional fields to bundle
        bundle = self.add_fields_to_bundle(bundle, obj)

        # Add Source fields to bundle
        if 'source' in bundle.data:
            source_id = bundle.data['source']
            obj_source = ReferenceSource.objects.get(pk=source_id)
            bundle = self.add_fields_to_bundle(bundle, obj_source)
            bundle.data['source_control'] = 'FONTE'

        # Add system version control number
        version_file = open(os.path.join(settings.PROJECT_ROOT_PATH, 'templates/version.txt'))
        version_number = version_file.readlines()[0]
        bundle.data['system_version'] = version_number.rstrip()

        # Add LILACS Database
        if obj.LILACS_indexed:
            bundle.data['database'] = 'LILACS'

        return bundle

    def add_fields_to_bundle(self, bundle, obj):
        for field in obj._meta.get_fields():
            # check if field is not already in bundle or has no value in bundle.data
            if field.name not in bundle.data or not bundle.data.get(field.name):
                field_value = getattr(obj, field.name, {})
                if field_value:
                    # copy value to mantain list (jsonfieds)
                    bundle.data[field.name] = copy(field_value)

        return bundle

    def dehydrate(self, bundle):
        # retrive child class of reference (analytic or source) for use in ContentType query
        child_class = bundle.obj.child_class()
        c_type = ContentType.objects.get_for_model(child_class)

        descriptors = Descriptor.objects.filter(object_id=bundle.obj.id, content_type=c_type, status=1)
        thematic_areas = ResourceThematic.objects.filter(object_id=bundle.obj.id, content_type=c_type, status=1)
        attachments = Attachment.objects.filter(object_id=bundle.obj.id, content_type=c_type)

        # add fields to output
        bundle.data['MFN'] = bundle.obj.id
        bundle.data['descriptors'] = [{'text': descriptor.code} for descriptor in descriptors]
        bundle.data['thematic_areas'] = [{'text': thematic.thematic_area.name} for thematic in thematic_areas]

        electronic_address = []
        for attach in attachments:
            file_name = attach.attachment_file.name
            file_extension = file_name.split(".")[-1].lower()

            if file_extension == 'pdf':
                file_type = 'PDF'
            else:
                file_type = 'TEXTO'

            view_url = "%sdocument/view/%s" % (settings.SITE_URL,  attach.short_url)

            electronic_address.append({'_u': view_url, '_i': attach.language[:2],
                                       '_y': file_type, '_q': file_extension})

        if electronic_address:
            if bundle.data['electronic_address'] and type(bundle.data['electronic_address']) is list:
                bundle.data['electronic_address'].extend(electronic_address)
            else:
                bundle.data['electronic_address'] = electronic_address

        return bundle

    def get_last_id(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        response = Reference.objects.latest('pk').pk

        return self.create_response(request, response)
