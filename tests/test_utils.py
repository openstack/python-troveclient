import os
import unittest2
from reddwarfclient import utils
from reddwarfclient import versions


class UtilsTest(unittest2.TestCase):
    
    def test_add_hookable_mixin(self):
        def func():
            pass
        
        hook_type = "hook_type"
        mixin = utils.HookableMixin()
        mixin.add_hook(hook_type, func)
        self.assertTrue(hook_type in mixin._hooks_map)
        self.assertTrue(func in mixin._hooks_map[hook_type])
        
    def test_run_hookable_mixin(self):
        def func():
            pass
        
        hook_type = "hook_type"
        mixin = utils.HookableMixin()
        mixin.add_hook(hook_type, func)
        mixin.run_hooks(hook_type)
        
    def test_environment(self):
        self.assertEqual('', utils.env())
        self.assertEqual('passing', utils.env(default='passing'))
                
        os.environ['test_abc'] = 'passing'
        self.assertEqual('passing', utils.env('test_abc'))
        self.assertEqual('', utils.env('test_abcd'))
        
    def test_slugify(self):
        import unicodedata
        
        self.assertEqual('not_unicode', utils.slugify('not_unicode'))
        self.assertEqual('unicode', utils.slugify(unicode('unicode')))
        self.assertEqual('slugify-test', utils.slugify('SLUGIFY% test!'))
        
