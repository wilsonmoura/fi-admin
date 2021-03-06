#! coding: utf-8
from django.utils.translation import ugettext_lazy as _, get_language
from django.db import models
from django.contrib.contenttypes.generic import GenericRelation
from django.contrib.admin.models import LogEntry
from utils.fields import JSONField, AuxiliaryChoiceField, MultipleAuxiliaryChoiceField
from utils.models import Generic, Country
from log.models import AuditLog

STATUS_CHOICES = (
    (-1, _('Draft')),
    (0, _('Inprocess')),
    (1, _('Published')),
    (2, _('Refused')),
    (3, _('Deleted')),
)

LITERATURETYPE_CHOICES = (
    ('S', _('Document published as a periodic series')),
    ('SC', _('Conference papers as a periodic series')),
    ('SCP', _('Paper of project and conference as a periodic series')),
    ('SP', _('Project paper as a periodic series')),
    ('M', _('Document published as a monograph')),
    ('MC', _('Conference paper as a monograph')),
    ('MCP', _('Paper of project and conference as a monograph')),
    ('MP', _('Project paper as a monograph ')),
    ('MS', _('Document published as a monographic series ')),
    ('MSC', _('Conference paper as a monographic series ')),
    ('MSP', _('Project paper as a monographic series')),
    ('T', _('Thesis, Dissertation (published or not) ')),
    ('TS', _('Thesis, Dissertation as a monographic series')),
    ('N', _('Non Conventional document')),
    ('NC', _('Conference paper in a non conventional format')),
    ('NP', _('Project paper in a non conventionally')),
)

TREATMENTLEVEL_CHOICES = (
    ('m', _('Monographic level')),
    ('mc', _('Monographic level of collection')),
    ('ms', _('Monographic level of serial')),
    ('am', _('Monographic analytical level')),
    ('amc', _('Monographic analytics level of collection')),
    ('ams', _('Monographic analytics level of serial')),
    ('as', _('Analytics level of serial')),
    ('c', _('Collection level')),
)


# Bibliographic Record
class Reference(Generic, AuditLog):
    class Meta:
        verbose_name = _("Bibliographic Record")
        verbose_name_plural = _("Bibliographic Records")

    status = models.SmallIntegerField(_('Status'), choices=STATUS_CHOICES, null=True, default=-1)
    LILACS_indexed = models.BooleanField(_('LILACS indexed?'), default=True)
    BIREME_reviewed = models.BooleanField(_('Reviewed by BIREME?'), default=False)

    # title used for display and search of Reference objects
    reference_title = models.TextField(_('Title'), blank=True)
    # field tag 01
    cooperative_center_code = models.CharField(_('Cooperative center'), max_length=55, blank=True)
    # field tag 05
    literature_type = models.CharField(_('Literature type'), max_length=10, blank=True)
    # field tag 06
    treatment_level = models.CharField(_('Treatment level'), max_length=10, blank=True)
    # field tag 08
    electronic_address = JSONField(_('Electronic address'), blank=True, null=True, dump_kwargs={'ensure_ascii': False})
    # field tag 09
    record_type = AuxiliaryChoiceField(_('Record type'), max_length=10, blank=True)

    # field tag 38
    descriptive_information = JSONField(_('Descriptive information'), blank=True, null=True, dump_kwargs={'ensure_ascii': False})
    # field tag 40
    text_language = MultipleAuxiliaryChoiceField(_('Text language'), blank=True)
    # field tag 61
    internal_note = models.TextField(_('Internal note'), blank=True)
    # field tag 64
    publication_date = models.CharField(_('Publication date'), max_length=250, blank=True)
    # field tag 65
    publication_date_normalized = models.CharField(_('Publication normalized date'), max_length=25, blank=True, help_text=_("Format: YYYYMMDD"))
    # field tag 71
    publication_type = MultipleAuxiliaryChoiceField(_('Publication type'), max_length=100, blank=True)
    # field tag 72
    total_number_of_references = models.CharField(_('Total number of references'), max_length=100, blank=True)
    # field tag 74
    time_limits_from = models.CharField(_('Time limits (from)'), max_length=50, blank=True)
    # field tag 75
    time_limits_to = models.CharField(_('Time limits (to)'), max_length=50, blank=True)
    # field tag 76
    check_tags = MultipleAuxiliaryChoiceField(_('Check tags'), max_length=100, blank=True)
    # field tag 78
    person_as_subject = models.TextField(_('Person as subject'), blank=True)
    # field tag 82
    non_decs_region = models.TextField(_('Non-DeCS Region'), blank=True)
    # field tag 83
    abstract = JSONField(_('Abstract'), blank=True, null=True, dump_kwargs={'ensure_ascii': False})
    # field tag 84
    transfer_date_to_database = models.CharField(_('Transfer date do database'), max_length=20, blank=True)
    # field tag 85
    author_keyword = JSONField(_('Author keyword'), blank=True, null=True, dump_kwargs={'ensure_ascii': False})
    # field tag 110
    item_form = AuxiliaryChoiceField(_('Item form'), max_length=10, blank=True)
    # field tag 111
    type_of_computer_file = AuxiliaryChoiceField(_('Type of computer file'), max_length=10, blank=True)
    # field tag 112
    type_of_cartographic_material = AuxiliaryChoiceField(_('Type of cartographic material'), max_length=10, blank=True)
    # field tag 113
    type_of_journal = AuxiliaryChoiceField(_('Type of journal'), max_length=10, blank=True)
    # field tag 114
    type_of_visual_material = AuxiliaryChoiceField(_('Type of visual material'), max_length=10, blank=True)
    # field tag 115
    specific_designation_of_the_material = AuxiliaryChoiceField(_('Specific designation of the material'), max_length=10, blank=True)
    # field tag 500
    general_note = models.TextField(_('General note'), blank=True)
    # field tag 505
    formatted_contents_note = models.TextField(_('Formatted contents note'), blank=True)
    # field tag 530
    additional_physical_form_available_note = models.TextField(_('Additional physical form available note'), blank=True)
    # field tag 533
    reproduction_note = models.TextField(_('Reproduction note'), blank=True)
    # field tag 534
    original_version_note = models.TextField(_('Original version note'), blank=True)
    # field tag 610
    institution_as_subject = models.TextField(_('Institution as subject'), blank=True)
    # field tag 653
    local_descriptors = models.TextField(_('Local descriptors'), blank=True)

    # field tag 899
    software_version = models.CharField(_('Software version'), max_length=50, blank=True)
    LILACS_original_id = models.CharField(_('LILACS id'), max_length=8, blank=True)

    # relations
    logs = GenericRelation(LogEntry)

    def __init__(self, *args, **kwargs):
        super(Reference, self).__init__(*args, **kwargs)
        self.__track_fields = ['status']
        for field in self.__track_fields:
            setattr(self, '__original_%s' % field, getattr(self, field))

    def previous_value(self, field):
        orig = '__original_%s' % field
        return getattr(self, orig)

    def __unicode__(self):
        if 'a' in self.treatment_level:
            ref_child = ReferenceAnalytic.objects.get(id=self.pk)
            if self.literature_type[0] == 'S':
                ref_title = u"{0}; {1} ({2}), {3} | {4}".format(ref_child.source.title_serial,
                                                                ref_child.source.volume_serial,
                                                                ref_child.source.issue_number,
                                                                ref_child.source.publication_date_normalized[:4],
                                                                ref_child.title[0]['text'])
            else:
                ref_title = u"{0} | {1}".format(ref_child.source.title_monographic,
                                                ref_child.title[0]['text'])
        else:
            ref_child = ReferenceSource.objects.get(id=self.pk)
            ref_title = ref_child.__unicode__()

        return ref_title

    def child_class(self):
        """
        Return the child class of the current instance (ex. for use in Content Type)
        """
        if 'a' in self.treatment_level:
            return ReferenceAnalytic
        else:
            return ReferenceSource


# Source
class ReferenceSource(Reference):

    class Meta:
        verbose_name = _("Bibliographic Record Source")
        verbose_name_plural = _("Bibliographic Records Source")

    # field tags 16
    individual_author_monographic = JSONField(_('Individual author'), blank=True, null=True, dump_kwargs={'ensure_ascii': False})
    # field tag 17
    corporate_author_monographic = JSONField(_('Corporate author'), blank=True, null=True, dump_kwargs={'ensure_ascii': False})
    # field tags 18
    title_monographic = models.CharField(_('Title'), max_length=250, blank=True)
    # field tags 19
    english_title_monographic = models.CharField(_('English translated title'), max_length=250, blank=True)
    # field tag 20
    pages_monographic = models.CharField(_('Pages'), max_length=80, blank=True)
    # field tags 21
    volume_monographic = models.CharField(_('Volume'), max_length=100, blank=True)
    # field tags 23
    individual_author_collection = JSONField(_('Individual author'), blank=True, null=True, dump_kwargs={'ensure_ascii': False})
    # field tag 24
    corporate_author_collection = JSONField(_('Corporate author'), blank=True, null=True, dump_kwargs={'ensure_ascii': False})
    # field tags 25
    title_collection = models.CharField(_('Title'), max_length=250, blank=True)
    # field tags 26
    english_title_collection = models.CharField(_('English translated title'), max_length=250, blank=True)
    # field tags 27
    total_number_of_volumes = models.CharField(_('Total number of volumes'), max_length=10, blank=True)
    # field tags 30
    title_serial = models.CharField(_('Journal title'), max_length=250, blank=True)
    # field tags 31
    volume_serial = models.CharField(_('Volume'), max_length=100, blank=True)
    # field tags 32
    issue_number = models.CharField(_('Issue number'), max_length=80, blank=True)
    # field tags 35
    issn = models.CharField(_('ISSN'), max_length=40, blank=True)
    # field tag 49
    thesis_dissertation_leader = JSONField(_('Thesis, Dissertation - Leader'), blank=True, null=True, dump_kwargs={'ensure_ascii': False})
    # field tag 50
    thesis_dissertation_institution = models.CharField(_('Thesis, Dissertation - Institution'), max_length=300, blank=True)
    # field tag 51
    thesis_dissertation_academic_title = models.CharField(_('Thesis, Dissertation - Academic title'), max_length=250, blank=True)
    # field tag 62
    publisher = models.TextField(_('Publisher'), blank=True)
    # field tag 63
    edition = models.CharField(_('Edition'), max_length=150, blank=True)
    # field tag 66
    publication_city = models.CharField(_('City of publication'), max_length=100, blank=True)
    # field tag 67
    publication_country = models.ForeignKey(Country, verbose_name=_('Publication country'), blank=True, null=True)
    # field tag 68
    symbol = models.TextField(_('Symbol'), blank=True)
    # field tag 69
    isbn = models.CharField(_('ISBN'), max_length=60, blank=True)
    # field tag 724
    doi_number = models.CharField(_('DOI number'), max_length=150, blank=True)

    def __unicode__(self):
        analytic_title = ''
        if self.literature_type[0] == 'S':
            analytic_title = u"{0}; {1} ({2}), {3}".format(self.title_serial,
                                                           self.volume_serial,
                                                           self.issue_number,
                                                           self.publication_date_normalized[:4])
        else:
            analytic_title = u"{0} {1}".format(self.title_monographic, self.volume_monographic)

        return analytic_title

    def has_analytic(self):
        exist_analytic = ReferenceAnalytic.objects.filter(source=self.pk).exists()

        return exist_analytic


# Bibliographic Records Analytic
class ReferenceAnalytic(Reference):

    class Meta:
        verbose_name = _("Bibliographic Record Analytic")
        verbose_name_plural = _("Bibliographic Records Analytic")

    source = models.ForeignKey(ReferenceSource, verbose_name=_("Source"), blank=False)
    # field tags 10
    individual_author = JSONField(_('Individual author'), blank=True, null=True, dump_kwargs={'ensure_ascii': False})
    # field tag 11
    corporate_author = JSONField(_('Corporate author'), blank=True, null=True, dump_kwargs={'ensure_ascii': False})
    # field tag 12
    title = JSONField(_('Title'), blank=False, null=True, dump_kwargs={'ensure_ascii': False}, help_text=_("Field mandatory"))
    # field tag 13
    english_translated_title = models.CharField(_('English translated title'), max_length=400, blank=True)
    # field tag 14
    pages = JSONField(_('Pages'), blank=True, null=True, dump_kwargs={'ensure_ascii': False})
    # field tag 700
    clinical_trial_registry_name = JSONField(_('Clinical trial registry name'), blank=True, null=True, dump_kwargs={'ensure_ascii': False})

    def __unicode__(self):
        if 'a' in self.treatment_level:
            if self.literature_type == 'S':
                ref_title = u"{0}; {1} ({2}), {3} | {4}".format(self.source.title_serial,
                                                                self.source.volume_serial,
                                                                self.source.issue_number,
                                                                self.source.publication_date_normalized[:4],
                                                                self.title[0]['text'])
            else:
                ref_title = u"{0} | {1}".format(self.source.title_monographic,
                                                self.title[0]['text'])
        else:
            ref_title = self.title[0]['text']

        return ref_title


# Bibliographic Record Complement
class ReferenceComplement(models.Model):

    class Meta:
        verbose_name = _("Bibliographic Record Complement")
        verbose_name_plural = _("Bibliographic Records Complement")

    source = models.ForeignKey(Reference, verbose_name=_("Source"), blank=False)

    # field tag 53
    conference_name = models.TextField(_('Conference name'), blank=True)
    # field tag 52
    conference_sponsoring_institution = models.TextField(_('Conference Sponsoring Institution'), blank=True)
    # field tag 54
    conference_date = models.CharField(_('Conference date'), max_length=100, blank=True)
    # field tag 55
    conference_normalized_date = models.CharField(_('Conference normalized date'), max_length=100, blank=True)
    # field tag 56
    conference_city = models.CharField(_('Conference city'), max_length=100, blank=True)
    # field tag 57
    conference_country = models.ForeignKey(Country, verbose_name=_('Conference country'), blank=True, null=True)
    # field tag 59
    project_name = models.CharField(_('Project name'), max_length=500, blank=True)
    # field tag 60
    project_number = models.CharField(_('Project number'), max_length=155, blank=True)
    # field tag 58
    project_sponsoring_institution = models.TextField(_('Project - Sponsoring Institution'), blank=True)


# Bibliographic Record Local information (library tab)
class ReferenceLocal(models.Model):

    class Meta:
        verbose_name = _("Bibliographic Record Local")
        verbose_name_plural = _("Bibliographic Records Local")

    source = models.ForeignKey(Reference, verbose_name=_("Source"), blank=False)
    # field tag 03
    call_number = JSONField(_('Call number'), blank=True, null=True, dump_kwargs={'ensure_ascii': False})
    # field tag 04
    database = models.TextField(_('Database'), blank=True)
    # field tag 07
    inventory_number = models.TextField(_('Inventory number'), blank=True)
    # field tag 61
    internal_note = models.TextField(_('Internal note'), blank=True)
    # field tag 653
    local_descriptors = models.TextField(_('Local descriptors'), blank=True)
    # responsible cooperative center
    cooperative_center_code = models.CharField(_('Cooperative center'), max_length=55, blank=True)

    def __unicode__(self):
        return u"[%s] | %s" % (self.cooperative_center_code, self.source)
