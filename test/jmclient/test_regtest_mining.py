"""Exercise the installed regtest interface with mocked Core RPC responses."""

import unittest
from unittest.mock import Mock, call, patch

from jmclient import blockchaininterface as backend
from jmclient.jsonrpc import JsonRpcError


class RegtestMiningTests(unittest.TestCase):
    def setUp(self):
        self.rpc = Mock()
        self.rpc.call.side_effect = [
            {"chain": "regtest"},
            ["jm_wallet"],
            {"descriptors": True, "private_keys_enabled": False},
        ]
        self.client = backend.RegtestBitcoinCoreInterface(self.rpc, "jm_wallet")

    def test_startup_needs_no_mining_address_or_funding_descriptor(self):
        self.rpc.setURL.assert_called_once_with("/wallet/jm_wallet")
        self.assertEqual(self.rpc.call.call_args_list, [
            call("getblockchaininfo", []),
            call("listwallets", []),
            call("getwalletinfo", []),
        ])
        self.assertTrue(self.client.descriptors)

    def test_broadcast_does_not_schedule_mining_by_default(self):
        self.rpc.call.reset_mock()
        self.rpc.call.side_effect = ["txid"]
        with patch.object(backend.reactor, "callLater") as schedule:
            self.assertTrue(self.client.pushtx(b"transaction"))
        self.rpc.call.assert_called_once_with("sendrawtransaction", [b"transaction".hex()])
        schedule.assert_not_called()

    def test_public_address_import_still_uses_the_monitoring_wallet(self):
        self.rpc.call.reset_mock()
        self.rpc.call.side_effect = [[{"success": True}]]
        with patch.object(backend.btc, "get_address_descriptor", return_value="addr(test)#checksum"):
            self.client.import_addresses(["test"], "client-label")
        self.rpc.call.assert_called_once_with("importdescriptors", [[{
            "desc": "addr(test)#checksum", "timestamp": "now", "label": "client-label",
        }]])

    def test_explicit_mining_creates_one_address_and_reuses_it(self):
        self.rpc.call.reset_mock()
        self.rpc.call.side_effect = ["bcrt1-mining", ["block1"], ["block2", "block3"]]
        self.client.tick_forward_chain(1)
        self.client.tick_forward_chain(2)
        self.assertEqual(self.rpc.call.call_args_list, [
            call("getnewaddress", []),
            call("generatetoaddress", [1, "bcrt1-mining"]),
            call("generatetoaddress", [2, "bcrt1-mining"]),
        ])

    def test_address_error_propagates_without_mining_and_can_be_retried(self):
        self.rpc.call.reset_mock()
        error = JsonRpcError({"code": -4, "message": "This wallet has no available keys"})
        self.rpc.call.side_effect = error
        with self.assertRaises(JsonRpcError) as caught:
            self.client.tick_forward_chain(1)
        self.assertIs(caught.exception, error)
        self.rpc.call.assert_called_once_with("getnewaddress", [])

        self.rpc.call.reset_mock()
        self.rpc.call.side_effect = ["bcrt1-mining", ["block1"]]
        self.client.tick_forward_chain(1)
        self.assertEqual(self.rpc.call.call_args_list, [
            call("getnewaddress", []), call("generatetoaddress", [1, "bcrt1-mining"]),
        ])


if __name__ == "__main__":
    unittest.main()
