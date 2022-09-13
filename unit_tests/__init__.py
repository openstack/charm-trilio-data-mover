import sys

sys.path.append("src")
sys.path.append("src/lib")

# Mock out charmhelpers so that we can test without it.
import charms_openstack.test_mocks  # noqa

charms_openstack.test_mocks.mock_charmhelpers()
sys.modules['charmhelpers.core.kernel'] = (
    charms_openstack.test_mocks.charmhelpers.core.kernel)
