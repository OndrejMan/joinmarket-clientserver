"""Check the installed display endpoint without starting a wallet or node."""
import json
import unittest
from unittest.mock import Mock, patch

from jmclient import wallet_rpc


class WalletDisplayTests(unittest.TestCase):
    def test_endpoint_forwards_displayall_and_keeps_private_keys_hidden(self):
        daemon = object.__new__(wallet_rpc.JMWalletDaemon)
        wallet = object()
        daemon.services = {"wallet": wallet}
        daemon.wallet_name = "client.jmdat"
        daemon.check_cookie = Mock()
        for args, expected in [({}, False), ({b"displayall": [b"false"]}, False),
                               ({b"displayall": [b"true"]}, True)]:
            with self.subTest(args=args):
                request = Mock(args=args)
                with patch.object(wallet_rpc, "print_req"), patch.object(
                    wallet_rpc, "wallet_display", return_value={"accounts": []}
                ) as display:
                    result = daemon.displaywallet(request, "client.jmdat")
                display.assert_called_once_with(wallet, False, displayall=expected, jsonified=True)
                self.assertEqual(json.loads(result)["walletinfo"], {"accounts": []})
                request.setResponseCode.assert_called_once_with(200)


if __name__ == "__main__":
    unittest.main()
