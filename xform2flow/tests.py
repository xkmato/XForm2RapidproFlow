from django.test import TestCase

from converter.xform2flow.models import Flow, RuleSet, Rule, ActionSet

ODK_DICT = {u'html':
    {
        u'body':
            {u'input':
                [
                    {u'ref': u'/data/firstname', u'label': u'What is your first name?'},
                    {u'ref': u'/data/lastname', u'label': u'What is your last name?'},
                    {u'ref': u'/data/age', u'label': u'What is your age?'}
                ]
            },
        u'head':
            {
                u'model':
                    {
                        u'bind':
                            [
                                {u'nodeset': u'/data/firstname', u'type': u'string', u'required': u'true()'},
                                {u'nodeset': u'/data/lastname', u'type': u'string'},
                                {u'nodeset': u'/data/age', u'type': u'integer'}
                            ],
                        u'instance':
                            {u'data':
                                 {u'version': u'2014083101', u'firstname': u'', u'lastname': u'',u'age': u'', u'meta':
                                     {u'instanceID': u''}, u'id': u'mysurvey'
                                  }
                             }
                    },
                u'title': u'My Survey'
            }
    }
}


class FlowTests(TestCase):
    def setUp(self):
        self.odk_dict = ODK_DICT

    def test_create_flow_from_dict(self):
        n = Flow.objects.count()
        flow = Flow.create_from_dict(self.odk_dict)
        self.assertEqual(Flow.objects.count(), n+1)
        self.assertEqual(flow.name, self.odk_dict['html']['head']['title'])

    def test_as_json(self):
        flow = Flow.create_from_dict(self.odk_dict)
        _json = flow.as_json(False)
        _flow = _json['flows'][0]
        self.assertEqual(_flow['action_sets'], [_set.as_json(False) for _set in flow.action_sets.all()])
        self.assertEqual(_flow['rule_sets'], [rule_set.as_json(False) for rule_set in flow.rule_sets.all()])
        self.assertEqual(_flow['entry'], unicode(flow.action_sets.order_by('created_on').first().uuid))


class RuleSetTests(TestCase):
    def setUp(self):
        self.input = ODK_DICT['html']['head']['model']['bind'][0]
        self.flow = Flow.create_from_dict(ODK_DICT)

    def test_create_from_input(self):
        n = RuleSet.objects.count()
        rule_set = RuleSet.create_from_input(self.input, 0, self.flow)
        self.assertEqual(RuleSet.objects.count(), n+1)
        self.assertEqual(self.input['nodeset'].split('/')[-1], rule_set.label)

    def test_as_json(self):
        rule_set = RuleSet.create_from_input(self.input, 0, self.flow)
        _json = rule_set.as_json(False)
        self.assertEqual(_json['uuid'], unicode(rule_set.uuid))
        self.assertEqual(_json['rules'], [rule.as_json(False) for rule in rule_set.rules.all()])


class RuleTests(TestCase):
    def setUp(self):
        self.input = ODK_DICT['html']['head']['model']['bind'][0]
        self.rule_set = Flow.create_from_dict(ODK_DICT).rule_sets.all()[0]

    def test_create(self):
        n = Rule.objects.count()
        rule = Rule.create(self.input, self.rule_set)
        self.assertEqual(Rule.objects.count(), n+1)
        if self.input['type'].lower() != 'string':
            self.assertEqual(rule.category, self.input['nodeset'].split('/')[-1])
        else:
            self.assertEqual(rule.category, 'All Responses')

    def test_as_json(self):
        rule = Rule.create(self.input, self.rule_set)
        _json = rule.as_json(False)
        self.assertEqual(_json['test'], rule.test.as_json(False))
        self.assertEqual(_json['category'], {'eng': rule.category})
        self.assertEqual(_json['uuid'], unicode(rule.uuid))


class RuleTestTests(TestCase):
    def test_as_json(self):
        rule_test = Flow.create_from_dict(ODK_DICT).rule_sets.all()[0].rules.all()[0].test
        _json = rule_test.as_json(False)
        self.assertEqual(_json['type'], rule_test.type)
        self.assertEqual(_json['test'], rule_test.test)


class ActionSetTests(TestCase):
    def setUp(self):
        self.input = ODK_DICT['html']['body']['input'][0]
        self.flow = Flow.create_from_dict(ODK_DICT)

    def test_create_from_input(self):
        n = ActionSet.objects.count()
        ActionSet.create_from_input(self.input, 0, self.flow)
        self.assertEqual(ActionSet.objects.count(), n+1)

    def test_as_json(self):
        action_set = ActionSet.create_from_input(self.input, 0, self.flow)
        _json = action_set.as_json(False)
        self.assertEqual(_json['uuid'], unicode(action_set.uuid))


class ActionTests(TestCase):
    def test_as_json(self):
        action = Flow.create_from_dict(ODK_DICT).action_sets.all()[0].actions.all()[0]
        _json = action.as_json(False)
        self.assertEqual(_json['type'], action.type)
        self.assertEqual(_json['msg'], {'eng': action.msg})