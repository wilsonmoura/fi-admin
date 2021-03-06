# coding: utf-8

from django.utils.translation import ugettext_lazy as _

LANGUAGES_CHOICES = (
    ('en', _('English')), # default language
    ('pt-br', _('Portuguese')),
    ('es', _('Spanish')),
)

SOURCE_CHOICES = [
    ('resources', _('Resources')),
    ('events', _('Events')),
    ('biblioref', _('Bibliographic Reference')),
]

USER_PROFILES = [
    ('edi', _('Editor')),
    ('doc', _('Documentalist')),
    ('editor_llxp', _('Editor LILACS-Express')),
]

SLOTS = [
    ('dashboard', _('Dashboard')),
]


############################## Descriptor choices ##############################

DESCRIPTOR_LEVEL = [
    ('general', _('General')),
    ('geographic', _('Geographic')),
]

DESCRIPTOR_VOCABULARY = [
    ('DeCS', _('DeCS: Health Sciences Descriptors')),
    ('Kewords', _('Keywords')),
]
