"""Ensure process-local configuration overrides reach the blockchain interface."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from jmclient import configure


class ConfigOverridesTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temporary_directory.name)
        (self.config_path / "joinmarket.cfg").write_text(
            configure.defaultconfig, encoding="utf-8"
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def load_with(self, **kwargs):
        received_config = Mock(return_value=None)
        with patch.object(configure, "get_blockchain_interface_instance", received_config), \
             patch.object(configure.global_singleton, "config_location", "joinmarket.cfg"):
            configure.load_program_config(config_path=str(self.config_path), **kwargs)
        return received_config.call_args.args[0]

    def test_rpc_wallet_file_override_is_applied_before_interface_creation(self):
        interface_config = self.load_with(rpc_wallet_file="jm_wallet_jcs_001")
        self.assertEqual(
            interface_config.get("BLOCKCHAIN", "rpc_wallet_file"), "jm_wallet_jcs_001"
        )

    def test_blockchain_source_override_is_applied_before_interface_creation(self):
        interface_config = self.load_with(bs="no-blockchain")
        self.assertEqual(
            interface_config.get("BLOCKCHAIN", "blockchain_source"), "no-blockchain"
        )


if __name__ == "__main__":
    unittest.main()
