from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms.utils import ErrorList
from utils.forms import is_valid_for_publication

import re


def check_url_or_page(form, formset_attachment):
    """
    Check for electronic_address field or attachment or pages
    """
    url_or_page = True

    pages = form.cleaned_data.get('pages')
    electronic_address = form.cleaned_data.get('electronic_address')

    # if not electronic_address field check for attachment files
    if not electronic_address:
        for form_attach in formset_attachment:
            try:
                if form_attach.cleaned_data and form_attach.cleaned_data.get('DELETE') == False:
                    electronic_address = True
            except AttributeError:
                pass

    # run LILACS validation check
    if not pages and not electronic_address:
        form.add_error('pages', _('Eletronic address, fulltext file OR pages are required'))
        url_or_page = False

    return url_or_page


def check_url_or_attachment(form, formset_attachment):
    """
    Check if is present the electronic_address field or attachment
    """
    url_or_attachment = True
    electronic_address = form.cleaned_data.get('electronic_address')

    # if not electronic_address field check for attachment files
    if not electronic_address:
        for form_attach in formset_attachment:
            try:
                if form_attach.cleaned_data and form_attach.cleaned_data.get('DELETE') == False:
                    electronic_address = True
            except AttributeError:
                pass

    if not electronic_address:
        formset_attachment.non_form_errors = ErrorList([_('Eletronic address or fulltext file required')])
        formset_attachment.is_valid = False
        url_or_attachment = False

    return url_or_attachment


def check_descriptor(form, formset_descriptor):
    """
    Check for at least one primary descriptors
    """
    valid = True
    descriptor_primary = False
    data = None

    # access forms from formsets:
    for formset in formset_descriptor.forms:
        if hasattr(formset, 'cleaned_data'):
            data = formset.cleaned_data

            # check for status and not marked for DELETE
            if data.get('DELETE') == False:
                if data.get('text') and data.get('code'):
                    if data.get('primary') == True:
                        descriptor_primary = True

    if not descriptor_primary:
        # For publication must have at least one descriptor admitted
        formset_descriptor.non_form_errors = ErrorList([_('For status "Published" you must have at least one primary descriptor')])
        formset_descriptor.is_valid = False
        valid = False

    return valid

def check_for_publication(form, formsets, user_data):
    """
    Run additional validation across forms fields for status LILACS-Express and LILACS
    """
    valid = True
    # regex match starts with S (Serial) and ends with (as) analytic
    regex_sas = r"^S.*as$"
    Sas_record = re.search(regex_sas, form.document_type)

    status = form.cleaned_data['status']
    user_role = user_data['service_role'].get('LILDBI')

    # for LILACS status and not Serie Source is required at least one primary descriptor
    if status == 1 and form.document_type != 'S':
        valid = check_descriptor(form, formsets['descriptor'])

    # for LILACS indexed check url/fulltext/page
    if valid and form.is_LILACS and status != -1:
        # for journal article (Sas record) check for electronic_address OR fulltext file #159
        if Sas_record:
            valid = check_url_or_attachment(form, formsets['attachment'])
        elif 'a' in form.document_type:
            # for other types of analytic records check for page or electronic_address #160
            valid = check_url_or_page(form, formsets['attachment'])

    return valid
