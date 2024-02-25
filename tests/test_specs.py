
# Testing against the official mustache specs. From:
# https://github.com/mustache/spec
# import os
# SPECS_PATH = os.path.join('specs')
# print(SPECS_PATH)
# if os.path.exists(SPECS_PATH):
#     SPECS = [path for path in os.listdir(SPECS_PATH) if path.endswith('.json')]
# else:
#     SPECS = []

# print(SPECS)

# #STACHE = chevron2.render


# def _test_case_from_path(json_path):
#     json_path = '%s.json' % json_path

#     class MustacheTestCase(unittest.TestCase):
#         """A simple yaml based test case"""

#         def _test_from_object(obj):
#             """Generate a unit test from a test object"""

#             def test_case(self):
#                 result = STACHE(obj['template'], obj['data'],
#                                 partials_dict=obj.get('partials', {}))

#                 self.assertEqual(result, obj['expected'])

#             test_case.__doc__ = 'suite: {0}    desc: {1}'.format(spec,
#                                                                  obj['desc'])
#             return test_case

#         with io.open(json_path, 'r', encoding='utf-8') as f:
#             yaml = json.load(f)

#         # Generates a unit test for each test object
#         for i, test in enumerate(yaml['tests']):
#             vars()['test_' + str(i)] = _test_from_object(test)

#     # Return the built class
#     return MustacheTestCase


# # Create TestCase for each json file
# for spec in SPECS:
#     # Ignore optional tests
#     if spec[0] != '~':
#         spec = spec.split('.')[0]
#         globals()[spec] = _test_case_from_path(os.path.join(SPECS_PATH, spec))




def test_spec_from_folder(datadir) -> None:
    print(datadir)
    assert False
