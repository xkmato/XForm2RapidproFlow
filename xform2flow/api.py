from pyxform.xform2json import XFormToDict

from converter.xform2flow.models import Flow


def from_xls(xml_file):
    pass


def from_xform(xml_file):
    _dict = XFormToDict(xml_file)
    flow = Flow.create_from_dict(_dict)
    return flow.as_json()