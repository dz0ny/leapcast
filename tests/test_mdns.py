from __future__ import unicode_literals

import unittest
import binascii
from dnslib import QTYPE

from leapcast.services.mdns import RRlist2bitmap


class MDNSTest(unittest.TestCase):

    def test_bitmap_one(self):
        lst = RRlist2bitmap([QTYPE.A])
        self.assertEqual(
            binascii.hexlify(lst), '000140')

    def test_bitmap_many(self):
        lst = RRlist2bitmap([QTYPE.TXT, QTYPE.SRV])
        self.assertEqual(
            binascii.hexlify(lst), '00050000800040')
