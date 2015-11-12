import json
import uuid as _uuid
from django.db import models
from django.utils.datetime_safe import strftime


class ModelBase(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Flow(ModelBase):
    name = models.CharField(max_length=100)
    saved_on = models.DateTimeField(auto_now=True)
    revision = models.IntegerField(default=13)
    version = models.IntegerField(default=8)

    flow_type = models.CharField(default='F', max_length=1)
    base_language = models.CharField(default='eng', max_length=100)

    def as_json(self, make_string=True):
        _json = {'version': 8, 'flows': [{'version': self.version, 'flow_type': self.flow_type,
                                          'entry': unicode(self.action_sets.order_by('created_on').first().uuid),
                                          'rule_sets': [rule_set.as_json(False) for rule_set in self.rule_sets.all()],
                                          'action_sets': [_set.as_json(False) for _set in self.action_sets.all()],
                                          'base_language': 'eng'}],
                 'metadata': {'expires': 0, 'revision': self.revision, 'id': self.pk,
                              'name': self.name, 'saved_on': strftime(self.saved_on, '%Y-%m-%dT%H:%M:%S.%fZ')},
                 'triggers': []}
        return json.dumps(_json) if make_string else _json

    @classmethod
    def create(cls, name):
        return cls.objects.create(name=name)

    @classmethod
    def create_from_dict(cls, _dict):
        flow = Flow.create(_dict['html']['head']['title'])
        action_sets = _dict['html']['body']['input']
        rule_sets = _dict['html']['head']['model']['bind']
        ay = 0
        ry = 150
        rule_set = None
        for a in action_sets:
            action_set = ActionSet.create_from_input(a, ay, flow)
            if rule_set:
                rule = rule_set.rules.exclude(category='Other').first()
                rule.destination = unicode(action_set.uuid)
                rule.destination_type = 'A'
                rule.save()
            r = [x for x in rule_sets if x['nodeset'] == a['ref']][0]
            rule_set = RuleSet.create_from_input(r, ry, flow)
            action_set.destination = unicode(rule_set.uuid)
            action_set.save()
            ay = ry + 150
            ry = ay + 150
        return flow


class RuleSet(ModelBase):
    uuid = models.UUIDField(primary_key=True, editable=False, default=_uuid.uuid4)
    ruleset_type = models.CharField(default='wait_message', max_length=100)
    response_type = models.CharField(max_length=100, blank=True)
    label = models.CharField(max_length=100)
    x = models.IntegerField(default=100)
    y = models.IntegerField()
    finished_key = models.CharField(null=True, max_length=100)
    operand = models.CharField(default='@step.value', max_length=100)
    flow = models.ForeignKey(Flow, related_name='rule_sets')

    def as_json(self, make_string=True):
        _json = {'uuid': unicode(self.uuid), 'webhook_action': None, 'webhook': None, 'ruleset_type': self.ruleset_type,
                 'label': self.label, 'operand': self.operand, 'finished_key': None,
                 'response_type': self.response_type,
                 'config': {}, 'x': self.x, 'y': self.y, 'rules': [rule.as_json(False) for rule in self.rules.all()]}
        return json.dumps(_json) if make_string else _json

    @classmethod
    def create_from_input(cls, _input, y, flow, destination=None):
        rule_set = cls.objects.create(flow=flow, y=y, label=_input['nodeset'].split('/')[-1])
        if _input['type'] != 'string':
            other = Rule.create_other_rule(rule_set)
        rule = Rule.create(_input, rule_set)
        rule.destination = destination
        if not destination:
            rule.destination_type = None
        rule.save()
        return rule_set


class Rule(ModelBase):
    category = models.CharField(max_length=100, default="All Responses")
    uuid = models.UUIDField(primary_key=True, editable=False, default=_uuid.uuid4)
    rule_set = models.ForeignKey(RuleSet, related_name='rules')
    destination = models.UUIDField(null=True)
    destination_type = models.CharField(max_length=100, default='A', null=True)

    MAPPING = {'integer': 'number'}

    def as_json(self, make_string=True):
        _json = {'test': self.test.as_json(False), 'category': {'eng': self.category}, 'uuid': unicode(self.uuid)}
        if self.destination:
            _json['destination'] = unicode(self.destination)
        if self.destination_type:
            _json['destination_type'] = self.destination_type
        return json.dumps(_json) if make_string else _json

    @classmethod
    def create(cls, _input, _set):
        if _input['type'].lower() != 'string':
            rule = cls.objects.create(rule_set=_set, category=_input['nodeset'].split('/')[-1])
            RuleTest.objects.create(type=cls.MAPPING[_input['type']], rule=rule)
        else:
            rule = cls.objects.create(rule_set=_set)
            RuleTest.objects.create(rule=rule)
        return rule

    @classmethod
    def create_other_rule(cls, _set):
        rule = cls.objects.create(rule_set=_set, category='Other')
        RuleTest.objects.create(rule=rule)
        return rule


class RuleTest(ModelBase):
    type = models.CharField(max_length=100, default='true')
    test = models.CharField(max_length=100, default='true')
    rule = models.OneToOneField(Rule, related_name='test')

    def as_json(self, make_string=True):
        if self.type == 'true':
            _json = {'type': self.type, 'test': self.test}
        else:
            _json = {'type': self.type}
        return json.dumps(_json) if make_string else _json


class ActionSet(ModelBase):
    y = models.IntegerField()
    x = models.IntegerField(default=100)
    destination = models.UUIDField(null=True)
    uuid = models.UUIDField(primary_key=True, editable=False, default=_uuid.uuid4)
    flow = models.ForeignKey(Flow, related_name='action_sets')

    def as_json(self, make_string=True):
        _json = {'y': self.y, 'x': self.x, 'destination': unicode(self.destination), 'uuid': unicode(self.uuid),
                 'actions': [action.as_json(False) for action in self.actions.all()]}
        return json.dumps(_json) if make_string else _json

    @classmethod
    def create_from_input(cls, _input, y, flow):
        act_set = cls.objects.create(y=y, flow=flow)
        Action.objects.create(action_set=act_set, msg=_input['label'])
        return act_set


class Action(ModelBase):
    action_set = models.ForeignKey(ActionSet, related_name='actions')
    msg = models.TextField()
    type = models.CharField(max_length=100, default='reply')

    def as_json(self, make_string=True):
        _json = {'msg': {'eng': self.msg}, 'type': self.type}
        return json.dumps(_json) if make_string else _json
