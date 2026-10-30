from importlib.util import find_spec
from unittest import TestCase, skipUnless

from support import load_module


@skipUnless(find_spec("pydantic"), "Install the Python 3.14 requirements to validate Pydantic models")
class PayloadModelTests(TestCase):
    def test_registration_alias_and_field_name_remain_valid(self) -> None:
        payload = load_module("payload/user.py").UserRegisterPayload
        values = dict(user_id="user", user_password="password", email_address="user@example.test", company_name="company")
        self.assertEqual(payload(**values, invitationKey="key").invitation_key, "key")
        self.assertEqual(payload(**values, invitation_key="key").invitation_key, "key")
        self.assertIsNone(payload(**values).invitation_key)
