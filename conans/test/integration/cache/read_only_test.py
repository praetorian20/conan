import os
import textwrap
import unittest

import pytest

from conans.model.recipe_ref import RecipeReference
from conans.test.utils.tools import NO_SETTINGS_PACKAGE_ID, TestClient, TestServer
from conans.util.files import save


@pytest.mark.xfail(reason="Legacy conan.conf configuration deprecated")
class ReadOnlyTest(unittest.TestCase):
    # TODO: The Cache ReadOnly might be always true if the "install-folder" initiative moves forward

    def setUp(self):
        self.test_server = TestServer()
        self.client = TestClient(servers={"default": self.test_server}, inputs=["admin", "password"])
        self.client.run("--version")
        conan_conf = textwrap.dedent("""
                            [general]
                            read_only_cache=True
                        """)
        self.client.save({"conan.conf": conan_conf}, path=self.client.cache.cache_folder)
        conanfile = """from conan import ConanFile
from conan.tools.files import copy
class MyPkg(ConanFile):
    exports_sources = "*.h"
    def package(self):
        copy(self, "*", self.source_folder, self.package_folder)
"""
        self.client.save({"conanfile.py": conanfile,
                          "myheader.h": "my header"})
        self.client.run("create . --name=pkg --version=0.1 --user=lasote --channel=channel")

    def test_basic(self):
        pref = self.client.get_latest_package_reference(RecipeReference.loads("pkg/0.1@lasote/channel"),
                                                        NO_SETTINGS_PACKAGE_ID)
        path = os.path.join(self.client.get_latest_pkg_layout(pref).package(), "myheader.h")
        with self.assertRaises(IOError):
            save(path, "Bye World")
        os.chmod(path, 0o777)
        save(path, "Bye World")

    @pytest.mark.xfail(reason="Tests using the Search command are temporarely disabled")
    def test_remove(self):
        self.client.run("search")
        self.assertIn("pkg/0.1@lasote/channel", self.client.out)
        self.client.run("remove pkg* -c")
        self.assertNotIn("pkg/0.1@lasote/channel", self.client.out)

    def test_upload(self):
        self.client.run("upload * --confirm -r default")
        self.client.run("remove pkg* -c")
        self.client.run("install --requires=pkg/0.1@lasote/channel")
        self.test_basic()

    def test_upload_change(self):
        self.client.run("upload * --confirm -r default")
        client = TestClient(servers={"default": self.test_server}, inputs=["admin", "password"])

        client.run("install --requires=pkg/0.1@lasote/channel")
        pref = self.client.get_latest_package_reference(RecipeReference.loads("pkg/0.1@lasote/channel"),
                                                        NO_SETTINGS_PACKAGE_ID)
        path = os.path.join(client.get_latest_pkg_layout(pref).package(), "myheader.h")
        with self.assertRaises(IOError):
            save(path, "Bye World")
        os.chmod(path, 0o777)
        save(path, "Bye World")
