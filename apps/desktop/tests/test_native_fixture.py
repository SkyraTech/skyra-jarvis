"""Preflight native fake-provider contracts without opening a Windows application."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
from native_fixture import FixtureProvider
from jarvis_core import Core
from jarvis_runtime.conversation import ConversationRuntime


class NativeFixtureContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.core=Core(Path(self.temp.name)/'core.sqlite3');self.addCleanup(self.core.close)
        self.project=self.core.create_project('owner','Native fixture preflight')
        self.conversation=self.core.create_conversation('owner',self.project)
        self.runtime=ConversationRuntime({'fixture':FixtureProvider()})

    def plan(self,request):
        turn=self.runtime.create(self.core,'owner',self.conversation,'fixture','plan',request,'preflight')
        return self.runtime.generate(self.core,'owner',turn)['response']['plan']

    def test_typescript_plan_uses_actual_current_request_context(self):
        plan=self.plan('Plan a TypeScript library that returns 42.')
        self.assertEqual('Native TypeScript library',plan['title'])
        self.assertEqual(['handle(null) returns 42'],plan['requirements'])

    def test_prior_typescript_history_does_not_change_a_new_website_request(self):
        self.core.append_message('owner',self.conversation,'user','Earlier TypeScript library work','old')
        self.assertEqual('Native client website plan',self.plan('Plan the fixture client website.')['title'])


if __name__=='__main__':unittest.main()
