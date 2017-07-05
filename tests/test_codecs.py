# Copyright (C) 2016-present the asyncpg authors and contributors
# <see AUTHORS file>
#
# This module is part of asyncpg and is released under
# the Apache 2.0 License: http://www.apache.org/licenses/LICENSE-2.0


import datetime
import decimal
import ipaddress
import math
import random
import struct
import unittest
import uuid

import asyncpg
from asyncpg import _testbase as tb


def _timezone(offset):
    minutes = offset // 60
    return datetime.timezone(datetime.timedelta(minutes=minutes))


infinity_datetime = datetime.datetime(
    datetime.MAXYEAR, 12, 31, 23, 59, 59, 999999)
negative_infinity_datetime = datetime.datetime(
    datetime.MINYEAR, 1, 1, 0, 0, 0, 0)

infinity_date = datetime.date(datetime.MAXYEAR, 12, 31)
negative_infinity_date = datetime.date(datetime.MINYEAR, 1, 1)


type_samples = [
    ('bool', 'bool', (
        True, False,
    )),
    ('smallint', 'int2', (
        -2 ** 15, 2 ** 15 - 1,
        -1, 0, 1,
    )),
    ('int', 'int4', (
        -2 ** 31, 2 ** 31 - 1,
        -1, 0, 1,
    )),
    ('bigint', 'int8', (
        -2 ** 63, 2 ** 63 - 1,
        -1, 0, 1,
    )),
    ('numeric', 'numeric', (
        -(2 ** 64),
        2 ** 64,
        -(2 ** 128),
        2 ** 128,
        -1, 0, 1,
        decimal.Decimal("0.00000000000000"),
        decimal.Decimal("1.00000000000000"),
        decimal.Decimal("-1.00000000000000"),
        decimal.Decimal("-2.00000000000000"),
        decimal.Decimal("1000000000000000.00000000000000"),
        decimal.Decimal("-0.00000000000000"),
        decimal.Decimal(1234),
        decimal.Decimal(-1234),
        decimal.Decimal("1234000000.00088883231"),
        decimal.Decimal(str(1234.00088883231)),
        decimal.Decimal("3123.23111"),
        decimal.Decimal("-3123000000.23111"),
        decimal.Decimal("3123.2311100000"),
        decimal.Decimal("-03123.0023111"),
        decimal.Decimal("3123.23111"),
        decimal.Decimal("3123.23111"),
        decimal.Decimal("10000.23111"),
        decimal.Decimal("100000.23111"),
        decimal.Decimal("1000000.23111"),
        decimal.Decimal("10000000.23111"),
        decimal.Decimal("100000000.23111"),
        decimal.Decimal("1000000000.23111"),
        decimal.Decimal("1000000000.3111"),
        decimal.Decimal("1000000000.111"),
        decimal.Decimal("1000000000.11"),
        decimal.Decimal("100000000.0"),
        decimal.Decimal("10000000.0"),
        decimal.Decimal("1000000.0"),
        decimal.Decimal("100000.0"),
        decimal.Decimal("10000.0"),
        decimal.Decimal("1000.0"),
        decimal.Decimal("100.0"),
        decimal.Decimal("100"),
        decimal.Decimal("100.1"),
        decimal.Decimal("100.12"),
        decimal.Decimal("100.123"),
        decimal.Decimal("100.1234"),
        decimal.Decimal("100.12345"),
        decimal.Decimal("100.123456"),
        decimal.Decimal("100.1234567"),
        decimal.Decimal("100.12345679"),
        decimal.Decimal("100.123456790"),
        decimal.Decimal("100.123456790000000000000000"),
        decimal.Decimal("1.0"),
        decimal.Decimal("0.0"),
        decimal.Decimal("-1.0"),
        decimal.Decimal("1.0E-1000"),
        decimal.Decimal("1.0E1000"),
        decimal.Decimal("0.000000000000000000000000001"),
        decimal.Decimal("0.000000000000010000000000001"),
        decimal.Decimal("0.00000000000000000000000001"),
        decimal.Decimal("0.00000000100000000000000001"),
        decimal.Decimal("0.0000000000000000000000001"),
        decimal.Decimal("0.000000000000000000000001"),
        decimal.Decimal("0.00000000000000000000001"),
        decimal.Decimal("0.0000000000000000000001"),
        decimal.Decimal("0.000000000000000000001"),
        decimal.Decimal("0.00000000000000000001"),
        decimal.Decimal("0.0000000000000000001"),
        decimal.Decimal("0.000000000000000001"),
        decimal.Decimal("0.00000000000000001"),
        decimal.Decimal("0.0000000000000001"),
        decimal.Decimal("0.000000000000001"),
        decimal.Decimal("0.00000000000001"),
        decimal.Decimal("0.0000000000001"),
        decimal.Decimal("0.000000000001"),
        decimal.Decimal("0.00000000001"),
        decimal.Decimal("0.0000000001"),
        decimal.Decimal("0.000000001"),
        decimal.Decimal("0.00000001"),
        decimal.Decimal("0.0000001"),
        decimal.Decimal("0.000001"),
        decimal.Decimal("0.00001"),
        decimal.Decimal("0.0001"),
        decimal.Decimal("0.001"),
        decimal.Decimal("0.01"),
        decimal.Decimal("0.1"),
    )),
    ('bytea', 'bytea', (
        bytes(range(256)),
        bytes(range(255, -1, -1)),
        b'\x00\x00',
        b'foo',
        b'f' * 1024 * 1024,
        dict(input=bytearray(b'\x02\x01'), output=b'\x02\x01'),
    )),
    ('text', 'text', (
        '',
        'A' * (1024 * 1024 + 11)
    )),
    ('"char"', 'char', (
        b'a',
        b'b',
        b'\x00'
    )),
    ('timestamp', 'timestamp', [
        datetime.datetime(3000, 5, 20, 5, 30, 10),
        datetime.datetime(2000, 1, 1, 5, 25, 10),
        datetime.datetime(500, 1, 1, 5, 25, 10),
        datetime.datetime(250, 1, 1, 5, 25, 10),
        infinity_datetime,
        negative_infinity_datetime,
        {'textinput': 'infinity', 'output': infinity_datetime},
        {'textinput': '-infinity', 'output': negative_infinity_datetime},
    ]),
    ('date', 'date', [
        datetime.date(3000, 5, 20),
        datetime.date(2000, 1, 1),
        datetime.date(500, 1, 1),
        infinity_date,
        negative_infinity_date,
        {'textinput': 'infinity', 'output': infinity_date},
        {'textinput': '-infinity', 'output': negative_infinity_date},
    ]),
    ('time', 'time', [
        datetime.time(12, 15, 20),
        datetime.time(0, 1, 1),
        datetime.time(23, 59, 59),
    ]),
    ('timestamptz', 'timestamptz', [
        # It's converted to UTC. When it comes back out, it will be in UTC
        # again. The datetime comparison will take the tzinfo into account.
        datetime.datetime(1990, 5, 12, 10, 10, 0, tzinfo=_timezone(4000)),
        datetime.datetime(1982, 5, 18, 10, 10, 0, tzinfo=_timezone(6000)),
        datetime.datetime(1950, 1, 1, 10, 10, 0, tzinfo=_timezone(7000)),
        datetime.datetime(1800, 1, 1, 10, 10, 0, tzinfo=_timezone(2000)),
        datetime.datetime(2400, 1, 1, 10, 10, 0, tzinfo=_timezone(2000)),
        infinity_datetime,
        negative_infinity_datetime,
    ]),
    ('timetz', 'timetz', [
        # timetz retains the offset
        datetime.time(10, 10, 0, tzinfo=_timezone(4000)),
        datetime.time(10, 10, 0, tzinfo=_timezone(6000)),
        datetime.time(10, 10, 0, tzinfo=_timezone(7000)),
        datetime.time(10, 10, 0, tzinfo=_timezone(2000)),
        datetime.time(22, 30, 0, tzinfo=_timezone(0)),
    ]),
    ('interval', 'interval', [
        # no months :(
        datetime.timedelta(40, 10, 1234),
        datetime.timedelta(0, 0, 4321),
        datetime.timedelta(0, 0),
        datetime.timedelta(-100, 0),
        datetime.timedelta(-100, -400),
    ]),
    ('uuid', 'uuid', [
        uuid.UUID('38a4ff5a-3a56-11e6-a6c2-c8f73323c6d4'),
        uuid.UUID('00000000-0000-0000-0000-000000000000'),
        {'input': '00000000-0000-0000-0000-000000000000',
         'output': uuid.UUID('00000000-0000-0000-0000-000000000000')}
    ]),
    ('uuid[]', 'uuid[]', [
        [uuid.UUID('38a4ff5a-3a56-11e6-a6c2-c8f73323c6d4'),
         uuid.UUID('00000000-0000-0000-0000-000000000000')],
        []
    ]),
    ('json', 'json', [
        '[1, 2, 3, 4]',
        '{"a": [1, 2], "b": 0}'
    ], (9, 2)),
    ('jsonb', 'jsonb', [
        '[1, 2, 3, 4]',
        '{"a": [1, 2], "b": 0}'
    ], (9, 4)),
    ('oid[]', 'oid[]', [
        [1, 2, 3, 4],
        []
    ]),
    ('smallint[]', 'int2[]', [
        [1, 2, 3, 4],
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 0],
        []
    ]),
    ('bigint[]', 'int8[]', [
        [2 ** 42, -2 ** 54, 0],
        []
    ]),
    ('int[]', 'int4[]', [
        [2 ** 22, -2 ** 24, 0],
        []
    ]),
    ('time[]', 'time[]', [
        [datetime.time(12, 15, 20), datetime.time(0, 1, 1)],
        []
    ]),
    ('text[]', 'text[]', [
        ['ABCDE', 'EDCBA'],
        [],
        ['A' * 1024 * 1024] * 10
    ]),
    ('float8', 'float8', [
        1.1,
        -1.1,
        0,
        2,
        1e-4,
        -1e-20,
        122.2e-100,
        2e5,
        math.pi,
        math.e,
        math.inf,
        -math.inf,
        math.nan,
        {'textinput': 'infinity', 'output': math.inf},
        {'textinput': '-infinity', 'output': -math.inf},
        {'textinput': 'NaN', 'output': math.nan},
    ]),
    ('float4', 'float4', [
        1.1,
        -1.1,
        0,
        2,
        1e-4,
        -1e-20,
        2e5,
        math.pi,
        math.e,
        math.inf,
        -math.inf,
        math.nan,
        {'textinput': 'infinity', 'output': math.inf},
        {'textinput': '-infinity', 'output': -math.inf},
        {'textinput': 'NaN', 'output': math.nan},
    ]),
    ('cidr', 'cidr', [
        ipaddress.IPv4Network('255.255.255.255/32'),
        ipaddress.IPv4Network('127.0.0.0/8'),
        ipaddress.IPv4Network('127.1.0.0/16'),
        ipaddress.IPv4Network('127.1.0.0/18'),
        ipaddress.IPv4Network('10.0.0.0/32'),
        ipaddress.IPv4Network('0.0.0.0/0'),
        ipaddress.IPv6Network('ffff' + ':ffff' * 7 + '/128'),
        ipaddress.IPv6Network('::1/128'),
        ipaddress.IPv6Network('::/0'),
    ]),
    ('inet', 'inet', [
        ipaddress.IPv4Address('255.255.255.255'),
        ipaddress.IPv4Address('127.0.0.1'),
        ipaddress.IPv4Address('0.0.0.0'),
        ipaddress.IPv6Address('ffff' + ':ffff' * 7),
        ipaddress.IPv6Address('::1'),
        ipaddress.IPv6Address('::'),
        dict(
            input='127.0.0.0/8',
            output=ipaddress.IPv4Network('127.0.0.0/8')),
        dict(
            input='127.0.0.1/32',
            output=ipaddress.IPv4Network('127.0.0.1/32')),
    ]),
    ('macaddr', 'macaddr', [
        '00:00:00:00:00:00',
        'ff:ff:ff:ff:ff:ff'
    ]),
    ('txid_snapshot', 'txid_snapshot', [
        (100, 1000, (100, 200, 300, 400))
    ]),
    ('varbit', 'varbit', [
        asyncpg.BitString('0000 0001'),
        asyncpg.BitString('00010001'),
        asyncpg.BitString(''),
        asyncpg.BitString(),
        asyncpg.BitString.frombytes(b'\x00', bitlength=3),
        asyncpg.BitString('0000 0000 1'),
        dict(input=b'\x01', output=asyncpg.BitString('0000 0001')),
        dict(input=bytearray(b'\x02'), output=asyncpg.BitString('0000 0010')),
    ]),
    ('path', 'path', [
        asyncpg.Path(asyncpg.Point(0.0, 0.0), asyncpg.Point(1.0, 1.0)),
        asyncpg.Path(asyncpg.Point(0.0, 0.0), asyncpg.Point(1.0, 1.0),
                     is_closed=True),
        dict(input=((0.0, 0.0), (1.0, 1.0)),
             output=asyncpg.Path(asyncpg.Point(0.0, 0.0),
                                 asyncpg.Point(1.0, 1.0),
                                 is_closed=True)),
        dict(input=[(0.0, 0.0), (1.0, 1.0)],
             output=asyncpg.Path(asyncpg.Point(0.0, 0.0),
                                 asyncpg.Point(1.0, 1.0),
                                 is_closed=False)),
    ]),
    ('point', 'point', [
        asyncpg.Point(0.0, 0.0),
        asyncpg.Point(1.0, 2.0),
    ]),
    ('box', 'box', [
        asyncpg.Box((1.0, 2.0), (0.0, 0.0)),
    ]),
    ('line', 'line', [
        asyncpg.Line(1, 2, 3),
    ], (9, 4)),
    ('lseg', 'lseg', [
        asyncpg.LineSegment((1, 2), (2, 2)),
    ]),
    ('polygon', 'polygon', [
        asyncpg.Polygon(asyncpg.Point(0.0, 0.0), asyncpg.Point(1.0, 0.0),
                        asyncpg.Point(1.0, 1.0), asyncpg.Point(0.0, 1.0)),
    ]),
    ('circle', 'circle', [
        asyncpg.Circle((0.0, 0.0), 100),
    ]),
]


class TestCodecs(tb.ConnectedTestCase):

    async def test_standard_codecs(self):
        """Test encoding/decoding of standard data types and arrays thereof."""
        for (typname, intname, sample_data, *metadata) in type_samples:
            if metadata and self.server_version < metadata[0]:
                continue

            st = await self.con.prepare(
                "SELECT $1::" + typname
            )

            textst = await self.con.prepare(
                "SELECT $1::text::" + typname
            )

            for sample in sample_data:
                with self.subTest(sample=sample, typname=typname):
                    stmt = st
                    if isinstance(sample, dict):
                        if 'textinput' in sample:
                            inputval = sample['textinput']
                            stmt = textst
                        else:
                            inputval = sample['input']
                        outputval = sample['output']
                    else:
                        inputval = outputval = sample

                    result = await stmt.fetchval(inputval)
                    err_msg = (
                        "unexpected result for {} when passing {!r}: "
                        "received {!r}, expected {!r}".format(
                            typname, inputval, result, outputval))

                    if typname.startswith('float'):
                        if math.isnan(outputval):
                            if not math.isnan(result):
                                self.fail(err_msg)
                        else:
                            self.assertTrue(
                                math.isclose(result, outputval, rel_tol=1e-6),
                                err_msg)
                    else:
                        self.assertEqual(result, outputval, err_msg)

            with self.subTest(sample=None, typname=typname):
                # Test that None is handled for all types.
                rsample = await st.fetchval(None)
                self.assertIsNone(rsample)

            at = st.get_attributes()
            self.assertEqual(at[0].type.name, intname)

    async def test_all_builtin_types_handled(self):
        from asyncpg.protocol.protocol import TYPEMAP

        for oid, typename in TYPEMAP.items():
            codec = self.con.get_settings().get_data_codec(oid)
            self.assertIsNotNone(
                codec,
                'core type {} ({}) is unhandled'.format(typename, oid))

    async def test_void(self):
        res = await self.con.fetchval('select pg_sleep(0)')
        self.assertIsNone(res)
        await self.con.fetchval('select now($1::void)', '')

    def test_bitstring(self):
        bitlen = random.randint(0, 1000)
        bs = ''.join(random.choice(('1', '0', ' ')) for _ in range(bitlen))
        bits = asyncpg.BitString(bs)
        sanitized_bs = bs.replace(' ', '')
        self.assertEqual(sanitized_bs,
                         bits.as_string().replace(' ', ''))

        expected_bytelen = \
            len(sanitized_bs) // 8 + (1 if len(sanitized_bs) % 8 else 0)

        self.assertEqual(len(bits.bytes), expected_bytelen)

    async def test_interval(self):
        res = await self.con.fetchval("SELECT '5 years'::interval")
        self.assertEqual(res, datetime.timedelta(days=1825))

        res = await self.con.fetchval("SELECT '5 years 1 month'::interval")
        self.assertEqual(res, datetime.timedelta(days=1855))

        res = await self.con.fetchval("SELECT '-5 years'::interval")
        self.assertEqual(res, datetime.timedelta(days=-1825))

        res = await self.con.fetchval("SELECT '-5 years -1 month'::interval")
        self.assertEqual(res, datetime.timedelta(days=-1855))

    async def test_unhandled_type_fallback(self):
        await self.con.execute('''
            CREATE EXTENSION IF NOT EXISTS isn
        ''')

        try:
            input_val = '1436-4522'

            res = await self.con.fetchrow('''
                SELECT $1::issn AS issn, 42 AS int
            ''', input_val)

            self.assertEqual(res['issn'], input_val)
            self.assertEqual(res['int'], 42)

        finally:
            await self.con.execute('''
                DROP EXTENSION isn
            ''')

    async def test_invalid_input(self):
        cases = [
            ('bytea', TypeError, 'a bytes-like object is required', [
                1,
                'aaa'
            ]),
            ('bool', TypeError, 'a boolean is required', [
                1,
            ]),
            ('int2', TypeError, 'an integer is required', [
                '2',
                'aa',
            ]),
            ('smallint', OverflowError, 'int too big to be encoded as INT2', [
                2**256,  # check for the same exception for any big numbers
                decimal.Decimal("2000000000000000000000000000000"),
                0xffff,
                0xffffffff,
                32768,
                -32769
            ]),
            ('float4', ValueError, 'float value too large', [
                4.1 * 10 ** 40,
                -4.1 * 10 ** 40,
            ]),
            ('int4', TypeError, 'an integer is required', [
                '2',
                'aa',
            ]),
            ('int', OverflowError, 'int too big to be encoded as INT4', [
                2**256,  # check for the same exception for any big numbers
                decimal.Decimal("2000000000000000000000000000000"),
                0xffffffff,
                2**31,
                -2**31 - 1,
            ]),
            ('int8', TypeError, 'an integer is required', [
                '2',
                'aa',
            ]),
            ('bigint', OverflowError, 'int too big to be encoded as INT8', [
                2**256,  # check for the same exception for any big numbers
                decimal.Decimal("2000000000000000000000000000000"),
                0xffffffffffffffff,
                2**63,
                -2**63 - 1,
            ]),
            ('text', TypeError, 'expected str, got bytes', [
                b'foo'
            ]),
            ('text', TypeError, 'expected str, got list', [
                [1]
            ])
        ]

        for typname, errcls, errmsg, data in cases:
            stmt = await self.con.prepare("SELECT $1::" + typname)

            for sample in data:
                with self.subTest(sample=sample, typname=typname):
                    with self.assertRaisesRegex(errcls, errmsg):
                        await stmt.fetchval(sample)

    async def test_arrays(self):
        """Test encoding/decoding of arrays (particularly multidimensional)."""
        cases = [
            (
                r"SELECT '[1:3][-1:0]={{1,2},{4,5},{6,7}}'::int[]",
                [[1, 2], [4, 5], [6, 7]]
            ),
            (
                r"SELECT '{{{{{{1}}}}}}'::int[]",
                [[[[[[1]]]]]]
            ),
            (
                r"SELECT '{1, 2, NULL}'::int[]::anyarray",
                [1, 2, None]
            ),
            (
                r"SELECT '{}'::int[]",
                []
            ),
        ]

        for sql, expected in cases:
            with self.subTest(sql=sql):
                res = await self.con.fetchval(sql)
                self.assertEqual(res, expected)

        with self.assertRaises(asyncpg.ProgramLimitExceededError):
            await self.con.fetchval("SELECT '{{{{{{{1}}}}}}}'::int[]")

        cases = [
            [None],
            [1, 2, 3, 4, 5, 6],
            [[1, 2], [4, 5], [6, 7]],
            [[[1], [2]], [[4], [5]], [[None], [7]]],
            [[[[[[1]]]]]],
            [[[[[[None]]]]]]
        ]

        st = await self.con.prepare(
            "SELECT $1::int[]"
        )

        for case in cases:
            with self.subTest(case=case):
                result = await st.fetchval(case)
                err_msg = (
                    "failed to return array data as-is; "
                    "gave {!r}, received {!r}".format(
                        case, result))

                self.assertEqual(result, case, err_msg)

        with self.assertRaisesRegex(ValueError, 'dimensions'):
            await self.con.fetchval(
                "SELECT $1::int[]",
                [[[[[[[1]]]]]]])

        with self.assertRaisesRegex(ValueError, 'non-homogeneous'):
            await self.con.fetchval(
                "SELECT $1::int[]",
                [1, [1]])

        with self.assertRaisesRegex(ValueError, 'non-homogeneous'):
            await self.con.fetchval(
                "SELECT $1::int[]",
                [[1], 1, [2]])

        with self.assertRaisesRegex(ValueError, 'invalid array element'):
            await self.con.fetchval(
                "SELECT $1::int[]",
                [1, 't', 2])

        with self.assertRaisesRegex(ValueError, 'invalid array element'):
            await self.con.fetchval(
                "SELECT $1::int[]",
                [[1], ['t'], [2]])

        with self.assertRaisesRegex(TypeError,
                                    'non-trivial iterable expected'):
            await self.con.fetchval(
                "SELECT $1::int[]",
                1)

    async def test_composites(self):
        """Test encoding/decoding of composite types."""
        await self.con.execute('''
            CREATE TYPE test_composite AS (
                a int,
                b text,
                c int[]
            )
        ''')

        st = await self.con.prepare('''
            SELECT ROW(NULL, 1234, '5678', ROW(42, '42'))
        ''')

        res = await st.fetchval()

        self.assertEqual(res, (None, 1234, '5678', (42, '42')))

        try:
            st = await self.con.prepare('''
                SELECT ROW(
                    NULL,
                    '5678',
                    ARRAY[9, NULL, 11]::int[]
                )::test_composite AS test
            ''')

            res = await st.fetch()
            res = res[0]['test']

            self.assertIsNone(res['a'])
            self.assertEqual(res['b'], '5678')
            self.assertEqual(res['c'], [9, None, 11])

            self.assertIsNone(res[0])
            self.assertEqual(res[1], '5678')
            self.assertEqual(res[2], [9, None, 11])

            at = st.get_attributes()
            self.assertEqual(len(at), 1)
            self.assertEqual(at[0].name, 'test')
            self.assertEqual(at[0].type.name, 'test_composite')
            self.assertEqual(at[0].type.kind, 'composite')

            res = await self.con.fetchval('''
                SELECT $1::test_composite
            ''', res)

        finally:
            await self.con.execute('DROP TYPE test_composite')

    async def test_domains(self):
        """Test encoding/decoding of composite types."""
        await self.con.execute('''
            CREATE DOMAIN my_dom AS int
        ''')

        await self.con.execute('''
            CREATE DOMAIN my_dom2 AS my_dom
        ''')

        try:
            st = await self.con.prepare('''
                SELECT 3::my_dom2
            ''')
            res = await st.fetchval()

            self.assertEqual(res, 3)

            st = await self.con.prepare('''
                SELECT NULL::my_dom2
            ''')
            res = await st.fetchval()

            self.assertIsNone(res)

            at = st.get_attributes()
            self.assertEqual(len(at), 1)
            self.assertEqual(at[0].name, 'my_dom2')
            self.assertEqual(at[0].type.name, 'int4')
            self.assertEqual(at[0].type.kind, 'scalar')

        finally:
            await self.con.execute('DROP DOMAIN my_dom2')
            await self.con.execute('DROP DOMAIN my_dom')

    async def test_range_types(self):
        """Test encoding/decoding of range types."""

        if self.server_version < (9, 2):
            raise unittest.SkipTest(
                'PostgreSQL servers < 9.2 do not support range types.')

        cases = [
            ('int4range', [
                [(1, 9), asyncpg.Range(1, 10)],
                [asyncpg.Range(0, 9, lower_inc=False, upper_inc=True),
                 asyncpg.Range(1, 10)],
                [(), asyncpg.Range(empty=True)],
                [asyncpg.Range(empty=True), asyncpg.Range(empty=True)],
                [(None, 2), asyncpg.Range(None, 3)],
                [asyncpg.Range(None, 2, upper_inc=True),
                 asyncpg.Range(None, 3)],
                [(2,), asyncpg.Range(2, None)],
                [(2, None), asyncpg.Range(2, None)],
                [asyncpg.Range(2, None), asyncpg.Range(2, None)],
                [(None, None), asyncpg.Range(None, None)],
                [asyncpg.Range(None, None), asyncpg.Range(None, None)]
            ])
        ]

        for (typname, sample_data) in cases:
            st = await self.con.prepare(
                "SELECT $1::" + typname
            )

            for sample, expected in sample_data:
                with self.subTest(sample=sample, typname=typname):
                    result = await st.fetchval(sample)
                    self.assertEqual(result, expected)

        with self.assertRaisesRegex(
                TypeError, 'list, tuple or Range object expected'):
            await self.con.fetch("SELECT $1::int4range", 'aa')

        with self.assertRaisesRegex(
                ValueError, 'expected 0, 1 or 2 elements'):
            await self.con.fetch("SELECT $1::int4range", (0, 2, 3))

    async def test_extra_codec_alias(self):
        """Test encoding/decoding of a builtin non-pg_catalog codec."""
        await self.con.execute('''
            CREATE EXTENSION IF NOT EXISTS hstore
        ''')

        try:
            await self.con.set_builtin_type_codec(
                'hstore', codec_name='pg_contrib.hstore')

            cases = [
                {'ham': 'spam', 'nada': None},
                {}
            ]

            st = await self.con.prepare('''
                SELECT $1::hstore AS result
            ''')

            for case in cases:
                res = await st.fetchval(case)
                self.assertEqual(res, case)

            res = await self.con.fetchval('''
                SELECT $1::hstore AS result
            ''', (('foo', '2'), ('bar', '3')))

            self.assertEqual(res, {'foo': '2', 'bar': '3'})

            with self.assertRaisesRegex(ValueError, 'null value not allowed'):
                await self.con.fetchval('''
                    SELECT $1::hstore AS result
                ''', {None: '1'})

        finally:
            await self.con.execute('''
                DROP EXTENSION hstore
            ''')

    async def test_custom_codec_text(self):
        """Test encoding/decoding using a custom codec in text mode."""
        await self.con.execute('''
            CREATE EXTENSION IF NOT EXISTS hstore
        ''')

        def hstore_decoder(data):
            result = {}
            items = data.split(',')
            for item in items:
                k, _, v = item.partition('=>')
                result[k.strip('"')] = v.strip('"')

            return result

        def hstore_encoder(obj):
            return ','.join('{}=>{}'.format(k, v) for k, v in obj.items())

        try:
            await self.con.set_type_codec('hstore', encoder=hstore_encoder,
                                          decoder=hstore_decoder)

            st = await self.con.prepare('''
                SELECT $1::hstore AS result
            ''')

            res = await st.fetchrow({'ham': 'spam'})
            res = res['result']

            self.assertEqual(res, {'ham': 'spam'})

            pt = st.get_parameters()
            self.assertTrue(isinstance(pt, tuple))
            self.assertEqual(len(pt), 1)
            self.assertEqual(pt[0].name, 'hstore')
            self.assertEqual(pt[0].kind, 'scalar')
            self.assertEqual(pt[0].schema, 'public')

            at = st.get_attributes()
            self.assertTrue(isinstance(at, tuple))
            self.assertEqual(len(at), 1)
            self.assertEqual(at[0].name, 'result')
            self.assertEqual(at[0].type, pt[0])

            err = 'cannot use custom codec on non-scalar type public._hstore'
            with self.assertRaisesRegex(ValueError, err):
                await self.con.set_type_codec('_hstore',
                                              encoder=hstore_encoder,
                                              decoder=hstore_decoder)

            await self.con.execute('''
                CREATE TYPE mytype AS (a int);
            ''')

            try:
                err = 'cannot use custom codec on non-scalar type ' + \
                      'public.mytype'
                with self.assertRaisesRegex(ValueError, err):
                    await self.con.set_type_codec(
                        'mytype', encoder=hstore_encoder,
                        decoder=hstore_decoder)
            finally:
                await self.con.execute('''
                    DROP TYPE mytype;
                ''')

        finally:
            await self.con.execute('''
                DROP EXTENSION hstore
            ''')

    async def test_custom_codec_binary(self):
        """Test encoding/decoding using a custom codec in binary mode."""
        await self.con.execute('''
            CREATE EXTENSION IF NOT EXISTS hstore
        ''')

        longstruct = struct.Struct('!L')
        ulong_unpack = lambda b: longstruct.unpack_from(b)[0]
        ulong_pack = longstruct.pack

        def hstore_decoder(data):
            result = {}
            n = ulong_unpack(data)
            view = memoryview(data)
            ptr = 4

            for i in range(n):
                klen = ulong_unpack(view[ptr:ptr + 4])
                ptr += 4
                k = bytes(view[ptr:ptr + klen]).decode()
                ptr += klen
                vlen = ulong_unpack(view[ptr:ptr + 4])
                ptr += 4
                if vlen == -1:
                    v = None
                else:
                    v = bytes(view[ptr:ptr + vlen]).decode()
                    ptr += vlen

                result[k] = v

            return result

        def hstore_encoder(obj):
            buffer = bytearray(ulong_pack(len(obj)))

            for k, v in obj.items():
                kenc = k.encode()
                buffer += ulong_pack(len(kenc)) + kenc

                if v is None:
                    buffer += b'\xFF\xFF\xFF\xFF'  # -1
                else:
                    venc = v.encode()
                    buffer += ulong_pack(len(venc)) + venc

            return buffer

        try:
            await self.con.set_type_codec('hstore', encoder=hstore_encoder,
                                          decoder=hstore_decoder,
                                          format='binary')

            st = await self.con.prepare('''
                SELECT $1::hstore AS result
            ''')

            res = await st.fetchrow({'ham': 'spam'})
            res = res['result']

            self.assertEqual(res, {'ham': 'spam'})

            pt = st.get_parameters()
            self.assertTrue(isinstance(pt, tuple))
            self.assertEqual(len(pt), 1)
            self.assertEqual(pt[0].name, 'hstore')
            self.assertEqual(pt[0].kind, 'scalar')
            self.assertEqual(pt[0].schema, 'public')

            at = st.get_attributes()
            self.assertTrue(isinstance(at, tuple))
            self.assertEqual(len(at), 1)
            self.assertEqual(at[0].name, 'result')
            self.assertEqual(at[0].type, pt[0])

        finally:
            await self.con.execute('''
                DROP EXTENSION hstore
            ''')

    async def test_custom_codec_override_binary(self):
        """Test overriding core codecs."""
        import json

        conn = await self.cluster.connect(database='postgres', loop=self.loop)
        try:
            def _encoder(value):
                return json.dumps(value).encode('utf-8')

            def _decoder(value):
                return json.loads(value.decode('utf-8'))

            await conn.set_type_codec(
                'json', encoder=_encoder, decoder=_decoder,
                schema='pg_catalog', format='binary'
            )

            data = {'foo': 'bar', 'spam': 1}
            res = await conn.fetchval('SELECT $1::json', data)
            self.assertEqual(data, res)

        finally:
            await conn.close()

    async def test_custom_codec_override_text(self):
        """Test overriding core codecs."""
        import json

        conn = await self.cluster.connect(database='postgres', loop=self.loop)
        try:
            def _encoder(value):
                return json.dumps(value)

            def _decoder(value):
                return json.loads(value)

            await conn.set_type_codec(
                'json', encoder=_encoder, decoder=_decoder,
                schema='pg_catalog', format='text'
            )

            data = {'foo': 'bar', 'spam': 1}
            res = await conn.fetchval('SELECT $1::json', data)
            self.assertEqual(data, res)

            def _encoder(value):
                return value

            def _decoder(value):
                return value

            await conn.set_type_codec(
                'uuid', encoder=_encoder, decoder=_decoder,
                schema='pg_catalog', format='text'
            )

            data = '14058ad9-0118-4b7e-ac15-01bc13e2ccd1'
            res = await conn.fetchval('SELECT $1::uuid', data)
            self.assertEqual(res, data)
        finally:
            await conn.close()

    async def test_custom_codec_override_tuple(self):
        """Test overriding core codecs."""
        cases = [
            ('date', (3,), '2000-01-04'),
            ('date', (2**31 - 1,), 'infinity'),
            ('date', (-2**31,), '-infinity'),
            ('time', (60 * 10**6,), '00:01:00'),
            ('timetz', (60 * 10**6, 12600), '00:01:00-03:30'),
            ('timestamp', (60 * 10**6,), '2000-01-01 00:01:00'),
            ('timestamp', (2**63 - 1,), 'infinity'),
            ('timestamp', (-2**63,), '-infinity'),
            ('timestamptz', (60 * 10**6,), '1999-12-31 19:01:00',
                "tab.v AT TIME ZONE 'EST'"),
            ('timestamptz', (2**63 - 1,), 'infinity'),
            ('timestamptz', (-2**63,), '-infinity'),
            ('interval', (2, 3, 0, 0), '2 mons 3 days')
        ]

        conn = await self.cluster.connect(database='postgres', loop=self.loop)

        def _encoder(value):
            return tuple(value)

        def _decoder(value):
            return tuple(value)

        try:
            for (typename, data, expected_result, *extra) in cases:
                with self.subTest(type=typename):
                    await self.con.execute(
                        'CREATE TABLE tab (v {})'.format(typename))

                    try:
                        await conn.set_type_codec(
                            typename, encoder=_encoder, decoder=_decoder,
                            schema='pg_catalog', format='tuple'
                        )

                        await conn.execute(
                            'INSERT INTO tab VALUES ($1)', data)

                        res = await conn.fetchval('SELECT tab.v FROM tab')
                        self.assertEqual(res, data)

                        await conn.reset_type_codec(
                            typename, schema='pg_catalog')

                        if extra:
                            val = extra[0]
                        else:
                            val = 'tab.v'

                        res = await conn.fetchval(
                            'SELECT ({val})::text FROM tab'.format(val=val))
                        self.assertEqual(res, expected_result)
                    finally:
                        await self.con.execute('DROP TABLE tab')
        finally:
            await conn.close()

    async def test_custom_codec_override_deprecation(self):
        conn = await self.cluster.connect(database='postgres', loop=self.loop)
        try:
            def _encoder(value):
                return value

            def _decoder(value):
                return value

            with self.assertWarnsRegex(DeprecationWarning,
                                       r"The `binary` keyword argument to "
                                       r"set_type_codec\(\) is deprecated"):
                await conn.set_type_codec(
                    'uuid', encoder=_encoder, decoder=_decoder,
                    schema='pg_catalog', binary=False
                )

                data = '14058ad9-0118-4b7e-ac15-01bc13e2ccd1'
                res = await conn.fetchval('SELECT $1::uuid', data)
                self.assertEqual(res, data)

        finally:
            await conn.close()

    async def test_composites_in_arrays(self):
        await self.con.execute('''
            CREATE TYPE t AS (a text, b int);
            CREATE TABLE tab (d t[]);
        ''')

        try:
            await self.con.execute(
                'INSERT INTO tab (d) VALUES ($1)',
                [('a', 1)])

            r = await self.con.fetchval('''
                SELECT d FROM tab
            ''')

            self.assertEqual(r, [('a', 1)])
        finally:
            await self.con.execute('''
                DROP TABLE tab;
                DROP TYPE t;
            ''')

    async def test_table_as_composite(self):
        await self.con.execute('''
            CREATE TABLE tab (a text, b int);
            INSERT INTO tab VALUES ('1', 1);
        ''')

        try:
            r = await self.con.fetchrow('''
                SELECT tab FROM tab
            ''')

            self.assertEqual(r, (('1', 1),))

        finally:
            await self.con.execute('''
                DROP TABLE tab;
            ''')

    async def test_relacl_array_type(self):
        await self.con.execute(r'''
            CREATE USER """u1'";
            CREATE USER "{u2";
            CREATE USER ",u3";
            CREATE USER "u4}";
            CREATE USER "u5""";
            CREATE USER "u6\""";
            CREATE USER "u7\";
            CREATE USER norm1;
            CREATE USER norm2;
            CREATE TABLE t0 (); GRANT SELECT ON t0 TO norm1;
            CREATE TABLE t1 (); GRANT SELECT ON t1 TO """u1'";
            CREATE TABLE t2 (); GRANT SELECT ON t2 TO "{u2";
            CREATE TABLE t3 (); GRANT SELECT ON t3 TO ",u3";
            CREATE TABLE t4 (); GRANT SELECT ON t4 TO "u4}";
            CREATE TABLE t5 (); GRANT SELECT ON t5 TO "u5""";
            CREATE TABLE t6 (); GRANT SELECT ON t6 TO "u6\""";
            CREATE TABLE t7 (); GRANT SELECT ON t7 TO "u7\";

            CREATE TABLE a1 ();
                GRANT SELECT ON a1 TO """u1'";
                GRANT SELECT ON a1 TO "{u2";
                GRANT SELECT ON a1 TO ",u3";
                GRANT SELECT ON a1 TO "norm1";
                GRANT SELECT ON a1 TO "u4}";
                GRANT SELECT ON a1 TO "u5""";
                GRANT SELECT ON a1 TO "u6\""";
                GRANT SELECT ON a1 TO "u7\";
                GRANT SELECT ON a1 TO "norm2";

            CREATE TABLE a2 ();
                GRANT SELECT ON a2 TO """u1'" WITH GRANT OPTION;
                GRANT SELECT ON a2 TO "{u2"   WITH GRANT OPTION;
                GRANT SELECT ON a2 TO ",u3"   WITH GRANT OPTION;
                GRANT SELECT ON a2 TO "norm1" WITH GRANT OPTION;
                GRANT SELECT ON a2 TO "u4}"   WITH GRANT OPTION;
                GRANT SELECT ON a2 TO "u5"""  WITH GRANT OPTION;
                GRANT SELECT ON a2 TO "u6\""" WITH GRANT OPTION;
                GRANT SELECT ON a2 TO "u7\"   WITH GRANT OPTION;

            SET SESSION AUTHORIZATION """u1'"; GRANT SELECT ON a2 TO "norm2";
            SET SESSION AUTHORIZATION "{u2";   GRANT SELECT ON a2 TO "norm2";
            SET SESSION AUTHORIZATION ",u3";   GRANT SELECT ON a2 TO "norm2";
            SET SESSION AUTHORIZATION "u4}";   GRANT SELECT ON a2 TO "norm2";
            SET SESSION AUTHORIZATION "u5""";  GRANT SELECT ON a2 TO "norm2";
            SET SESSION AUTHORIZATION "u6\"""; GRANT SELECT ON a2 TO "norm2";
            SET SESSION AUTHORIZATION "u7\";   GRANT SELECT ON a2 TO "norm2";
            RESET SESSION AUTHORIZATION;
        ''')

        try:
            rows = await self.con.fetch('''
                SELECT
                    relacl,
                    relacl::text[] AS chk,
                    relacl::text[]::text AS text_
                FROM
                    pg_catalog.pg_class
                WHERE
                    relacl IS NOT NULL
            ''')

            for row in rows:
                self.assertEqual(row['relacl'], row['chk'],)

        finally:
            await self.con.execute(r'''
                DROP TABLE t0;
                DROP TABLE t1;
                DROP TABLE t2;
                DROP TABLE t3;
                DROP TABLE t4;
                DROP TABLE t5;
                DROP TABLE t6;
                DROP TABLE t7;
                DROP TABLE a1;
                DROP TABLE a2;
                DROP USER """u1'";
                DROP USER "{u2";
                DROP USER ",u3";
                DROP USER "u4}";
                DROP USER "u5""";
                DROP USER "u6\""";
                DROP USER "u7\";
                DROP USER norm1;
                DROP USER norm2;
            ''')

    async def test_enum(self):
        await self.con.execute('''
            CREATE TYPE enum_t AS ENUM ('abc', 'def', 'ghi');
            CREATE TABLE tab (
                a text,
                b enum_t
            );
            INSERT INTO tab (a, b) VALUES ('foo', 'abc');
            INSERT INTO tab (a, b) VALUES ('bar', 'def');
        ''')

        try:
            for i in range(10):
                r = await self.con.fetch('''
                    SELECT a, b FROM tab ORDER BY b
                ''')

                self.assertEqual(r, [('foo', 'abc'), ('bar', 'def')])

        finally:
            await self.con.execute('''
                DROP TABLE tab;
                DROP TYPE enum_t;
            ''')

    async def test_unknown_type_text_fallback(self):
        await self.con.execute(r'CREATE EXTENSION citext')
        await self.con.execute(r'''
            CREATE DOMAIN citext_dom AS citext
        ''')
        await self.con.execute(r'''
            CREATE TYPE citext_range AS RANGE (SUBTYPE = citext)
        ''')
        await self.con.execute(r'''
            CREATE TYPE citext_comp AS (t citext)
        ''')

        try:
            # Check that plain fallback works.
            result = await self.con.fetchval('''
                SELECT $1::citext
            ''', 'citext')

            self.assertEqual(result, 'citext')

            # Check that domain fallback works.
            result = await self.con.fetchval('''
                SELECT $1::citext_dom
            ''', 'citext')

            self.assertEqual(result, 'citext')

            # Check that array fallback works.
            cases = [
                ['a', 'b'],
                [None, 'b'],
                [],
                ['  a', '  b'],
                ['"a', r'\""'],
                [['"a', r'\""'], [',', '",']],
            ]

            for case in cases:
                result = await self.con.fetchval('''
                    SELECT
                        $1::citext[]
                ''', case)

                self.assertEqual(result, case)

            # Text encoding of ranges and composite types
            # is not supported yet.
            with self.assertRaisesRegex(
                    RuntimeError,
                    'text encoding of range types is not supported'):

                await self.con.fetchval('''
                    SELECT
                        $1::citext_range
                ''', ['a', 'z'])

            with self.assertRaisesRegex(
                    RuntimeError,
                    'text encoding of composite types is not supported'):

                await self.con.fetchval('''
                    SELECT
                        $1::citext_comp
                ''', ('a',))

            # Check that setting a custom codec clears the codec
            # cache properly and that subsequent queries work
            # as expected.
            await self.con.set_type_codec(
                'citext', encoder=lambda d: d, decoder=lambda d: 'CI: ' + d)

            result = await self.con.fetchval('''
                SELECT
                    $1::citext[]
            ''', ['a', 'b'])

            self.assertEqual(result, ['CI: a', 'CI: b'])

        finally:
            await self.con.execute(r'DROP TYPE citext_comp')
            await self.con.execute(r'DROP TYPE citext_range')
            await self.con.execute(r'DROP TYPE citext_dom')
            await self.con.execute(r'DROP EXTENSION citext')

    async def test_enum_in_array(self):
        await self.con.execute('''
            CREATE TYPE enum_t AS ENUM ('abc', 'def', 'ghi');
        ''')

        try:
            result = await self.con.fetchrow('''SELECT $1::enum_t[];''',
                                             ['abc'])
            self.assertEqual(result, (['abc'],))

            result = await self.con.fetchrow('''SELECT ARRAY[$1::enum_t];''',
                                             'abc')

            self.assertEqual(result, (['abc'],))

        finally:
            await self.con.execute('''
                DROP TYPE enum_t;
            ''')

    async def test_enum_and_range(self):
        await self.con.execute('''
            CREATE TYPE enum_t AS ENUM ('abc', 'def', 'ghi');
            CREATE TABLE testtab (
                a int4range,
                b enum_t
            );

            INSERT INTO testtab VALUES (
                '[10, 20)', 'abc'
            );
        ''')

        try:
            result = await self.con.fetchrow('''
                SELECT testtab.a FROM testtab WHERE testtab.b = $1
            ''', 'abc')

            self.assertEqual(result, (asyncpg.Range(10, 20),))
        finally:
            await self.con.execute('''
                DROP TABLE testtab;
                DROP TYPE enum_t;
            ''')
