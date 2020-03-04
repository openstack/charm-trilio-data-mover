import mock
import unittest
import trilio_data_mover as datamover

_when_args = {}
_when_not_args = {}


def mock_hook_factory(d):

    def mock_hook(*args, **kwargs):

        def inner(f):
            # remember what we were passed.  Note that we can't actually
            # determine the class we're attached to, as the decorator only gets
            # the function.
            try:
                d[f.__name__].append(dict(args=args, kwargs=kwargs))
            except KeyError:
                d[f.__name__] = [dict(args=args, kwargs=kwargs)]
            return f
        return inner
    return mock_hook


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._patched_when = mock.patch('charms.reactive.when',
                                       mock_hook_factory(_when_args))
        cls._patched_when_started = cls._patched_when.start()
        cls._patched_when_not = mock.patch('charms.reactive.when_not',
                                           mock_hook_factory(_when_not_args))
        cls._patched_when_not_started = cls._patched_when_not.start()
        # force requires to rerun the mock_hook decorator:
        # try except is Python2/Python3 compatibility as Python3 has moved
        # reload to importlib.
        try:
            reload(datamover)
        except NameError:
            import importlib
            importlib.reload(datamover)

    @classmethod
    def tearDownClass(cls):
        cls._patched_when.stop()
        cls._patched_when_started = None
        cls._patched_when = None
        cls._patched_when_not.stop()
        cls._patched_when_not_started = None
        cls._patched_when_not = None
        # and fix any breakage we did to the module
        try:
            reload(datamover)
        except NameError:
            import importlib
            importlib.reload(datamover)

    def setUp(self):
        self._patches = {}
        self._patches_start = {}

    def tearDown(self):
        for k, v in self._patches.items():
            v.stop()
            setattr(self, k, None)
        self._patches = None
        self._patches_start = None

    def patch(self, obj, attr, return_value=None, side_effect=None):
        mocked = mock.patch.object(obj, attr)
        self._patches[attr] = mocked
        started = mocked.start()
        started.return_value = return_value
        started.side_effect = side_effect
        self._patches_start[attr] = started
        setattr(self, attr, started)

    def test_registered_hooks(self):
        # test that the hooks actually registered the relation expressions that
        # are meaningful for this interface: this is to handle regressions.
        # The keys are the function names that the hook attaches to.
        when_patterns = {
            'stop_tvault_contego_plugin': ('tvault-contego.stopping', ),
        }
        when_not_patterns = {
            'install_tvault_contego_plugin': (
                'tvault-contego.installed', ), }
        # check the when hooks are attached to the expected functions
        for t, p in [(_when_args, when_patterns),
                     (_when_not_args, when_not_patterns)]:
            for f, args in t.items():
                # check that function is in patterns
                self.assertTrue(f in p.keys(),
                                "{} not found".format(f))
                # check that the lists are equal
                lists = []
                for a in args:
                    lists += a['args'][:]
                self.assertEqual(sorted(lists), sorted(p[f]),
                                 "{}: incorrect state registration".format(f))

    def test_install_plugin(self):
         self.patch(datamover, 'install_plugin')
         datamover.install_plugin('pkg_name')
         self.install_plugin.assert_called_once_with('pkg_name')

    def test_uninstall_plugin(self):
         self.patch(datamover, 'uninstall_plugin')
         datamover.uninstall_plugin()
         self.uninstall_plugin.assert_called_once_with()

    def test_install_tvault_contego_plugin(self):
         self.patch(datamover, 'install_tvault_contego_plugin')
         datamover.install_tvault_contego_plugin()
         self.install_tvault_contego_plugin.assert_called_once_with()

    def test_stop_tvault_contego_plugin(self):
         self.patch(datamover, 'config')
         self.patch(datamover, 'status_set')
         self.patch(datamover, 'remove_state')
         self.patch(datamover, 'uninstall_plugin')
         self.uninstall_plugin.return_value = True
         datamover.stop_tvault_contego_plugin()
         self.status_set.assert_called_with(
             'maintenance', 'Stopping...')
         self.remove_state.assert_called_with('tvault-contego.stopping')

    def test_s3_object_storage_fail(self):
         self.patch(datamover, 'config')
         self.config.return_value = 's3'
         self.patch(datamover, 'apt_update')
         self.patch(datamover, 'status_set')
         self.patch(datamover, 'validate_backup')
         self.validate_backup.return_value = True
         self.patch(datamover, 'add_users')
         self.add_users.return_value = True
         self.patch(datamover, 'create_virt_env')
         self.create_virt_env.return_value = True
         self.patch(datamover, 'ensure_files')
         self.ensure_files.return_value = True
         self.patch(datamover, 'create_conf')
         self.create_conf.return_value = True
         self.patch(datamover, 'ensure_data_dir')
         self.ensure_data_dir.return_value = True
         self.patch(datamover, 'create_service_file')
         self.create_service_file.return_value = True
         self.patch(datamover, 'create_object_storage_service')
         self.create_object_storage_service.return_value = False
         self.patch(datamover.os, 'system')
         self.patch(datamover, 'log')
         datamover.install_tvault_contego_plugin()
         self.status_set.assert_called_with(
             'blocked',
             'Failed while creating ObjectStore service file')

    def test_s3_object_storage_pass(self):
         self.patch(datamover, 'config')
         self.patch(datamover, 'apt_update')
         self.patch(datamover, 'status_set')
         self.patch(datamover, 'validate_backup')
         self.validate_backup.return_value = True
         self.patch(datamover, 'add_users')
         self.add_users.return_value = True
         self.patch(datamover, 'create_virt_env')
         self.create_virt_env.return_value = True
         self.patch(datamover, 'ensure_files')
         self.ensure_files.return_value = True
         self.patch(datamover, 'create_conf')
         self.create_conf.return_value = True
         self.patch(datamover, 'ensure_data_dir')
         self.ensure_data_dir.return_value = True
         self.patch(datamover, 'create_service_file')
         self.create_service_file.return_value = True
         self.patch(datamover, 'create_object_storage_service')
         self.create_object_storage_service.return_value = True
         self.patch(datamover, 'service_restart')
         self.patch(datamover, 'set_flag')
         self.patch(datamover, 'application_version_set')
         self.patch(datamover, 'get_new_version')
         self.patch(datamover.os, 'system')
         datamover.install_tvault_contego_plugin()
         self.service_restart.assert_called_with(
             'tvault-contego')
         self.status_set.assert_called_with(
             'active', 'Ready...')
         self.application_version_set.assert_called_once()
         self.set_flag.assert_called_with(
             'tvault-contego.installed')
