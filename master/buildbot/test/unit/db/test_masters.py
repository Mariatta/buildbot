# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members

from twisted.internet import defer
from twisted.trial import unittest

from buildbot.db import masters
from buildbot.test import fakedb
from buildbot.test.util import connector_component
from buildbot.test.util import interfaces
from buildbot.test.util import validation
from buildbot.util import epoch2datetime

SOMETIME = 1348971992
SOMETIME_DT = epoch2datetime(SOMETIME)
OTHERTIME = 1008971992
OTHERTIME_DT = epoch2datetime(OTHERTIME)


class Tests(interfaces.InterfaceTests):

    # common sample data

    master_row = [
        fakedb.Master(id=7, name="some:master",
                      active=1, last_active=SOMETIME),
    ]

    # tests

    def test_signature_findMasterId(self):
        @self.assertArgSpecMatches(self.db.masters.findMasterId)
        def findMasterId(self, name):
            pass

    def test_signature_setMasterState(self):
        @self.assertArgSpecMatches(self.db.masters.setMasterState)
        def setMasterState(self, masterid, active):
            pass

    def test_signature_getMaster(self):
        @self.assertArgSpecMatches(self.db.masters.getMaster)
        def getMaster(self, masterid):
            pass

    def test_signature_getMasters(self):
        @self.assertArgSpecMatches(self.db.masters.getMasters)
        def getMasters(self):
            pass

    @defer.inlineCallbacks
    def test_findMasterId_new(self):
        id = yield self.db.masters.findMasterId('some:master')
        masterdict = yield self.db.masters.getMaster(id)
        self.assertEqual(masterdict,
                         dict(id=id, name='some:master', active=False,
                              last_active=SOMETIME_DT))

    @defer.inlineCallbacks
    def test_findMasterId_new_name_differs_only_by_case(self):
        yield self.insert_test_data([
            fakedb.Master(id=7, name='some:master'),
        ])
        id = yield self.db.masters.findMasterId('some:Master')
        masterdict = yield self.db.masters.getMaster(id)
        self.assertEqual(masterdict, {'id': id, 'name': 'some:Master', 'active': False,
                                      'last_active': SOMETIME_DT})

    @defer.inlineCallbacks
    def test_findMasterId_exists(self):
        yield self.insert_test_data([
            fakedb.Master(id=7, name='some:master'),
        ])
        id = yield self.db.masters.findMasterId('some:master')
        self.assertEqual(id, 7)

    @defer.inlineCallbacks
    def test_setMasterState_when_missing(self):
        activated = \
            yield self.db.masters.setMasterState(masterid=7, active=True)
        self.assertFalse(activated)

    @defer.inlineCallbacks
    def test_setMasterState_true_when_active(self):
        yield self.insert_test_data([
            fakedb.Master(id=7, name='some:master',
                          active=1, last_active=OTHERTIME),
        ])
        activated = yield self.db.masters.setMasterState(
            masterid=7, active=True)
        self.assertFalse(activated)  # it was already active
        masterdict = yield self.db.masters.getMaster(7)
        self.assertEqual(masterdict,
                         dict(id=7, name='some:master', active=True,
                              last_active=SOMETIME_DT))  # timestamp updated

    @defer.inlineCallbacks
    def test_setMasterState_true_when_inactive(self):
        yield self.insert_test_data([
            fakedb.Master(id=7, name='some:master',
                          active=0, last_active=OTHERTIME),
        ])
        activated = yield self.db.masters.setMasterState(
            masterid=7, active=True)
        self.assertTrue(activated)
        masterdict = yield self.db.masters.getMaster(7)
        self.assertEqual(masterdict,
                         dict(id=7, name='some:master', active=True,
                              last_active=SOMETIME_DT))

    @defer.inlineCallbacks
    def test_setMasterState_false_when_active(self):
        yield self.insert_test_data([
            fakedb.Master(id=7, name='some:master',
                          active=1, last_active=OTHERTIME),
        ])
        deactivated = yield self.db.masters.setMasterState(
            masterid=7, active=False)
        self.assertTrue(deactivated)
        masterdict = yield self.db.masters.getMaster(7)
        self.assertEqual(masterdict,
                         dict(id=7, name='some:master', active=False,
                              last_active=OTHERTIME_DT))

    @defer.inlineCallbacks
    def test_setMasterState_false_when_inactive(self):
        yield self.insert_test_data([
            fakedb.Master(id=7, name='some:master',
                          active=0, last_active=OTHERTIME),
        ])
        deactivated = yield self.db.masters.setMasterState(
            masterid=7, active=False)
        self.assertFalse(deactivated)
        masterdict = yield self.db.masters.getMaster(7)
        self.assertEqual(masterdict,
                         dict(id=7, name='some:master', active=False,
                              last_active=OTHERTIME_DT))

    @defer.inlineCallbacks
    def test_getMaster(self):
        yield self.insert_test_data([
            fakedb.Master(id=7, name='some:master',
                          active=0, last_active=SOMETIME),
        ])
        masterdict = yield self.db.masters.getMaster(7)
        validation.verifyDbDict(self, 'masterdict', masterdict)
        self.assertEqual(masterdict, dict(id=7, name='some:master',
                                          active=False, last_active=SOMETIME_DT))

    @defer.inlineCallbacks
    def test_getMaster_missing(self):
        masterdict = yield self.db.masters.getMaster(7)
        self.assertEqual(masterdict, None)

    @defer.inlineCallbacks
    def test_getMasters(self):
        yield self.insert_test_data([
            fakedb.Master(id=7, name='some:master',
                          active=0, last_active=SOMETIME),
            fakedb.Master(id=8, name='other:master',
                          active=1, last_active=OTHERTIME),
        ])
        masterlist = yield self.db.masters.getMasters()
        for masterdict in masterlist:
            validation.verifyDbDict(self, 'masterdict', masterdict)

        def masterKey(master):
            return master['id']

        expected = sorted([
            dict(id=7, name='some:master',
                 active=0, last_active=SOMETIME_DT),
            dict(id=8, name='other:master',
                 active=1, last_active=OTHERTIME_DT),
        ], key=masterKey)
        self.assertEqual(sorted(masterlist, key=masterKey), expected)


class RealTests(Tests):

    # tests that only "real" implementations will pass

    @defer.inlineCallbacks
    def test_setMasterState_false_deletes_links(self):
        yield self.insert_test_data([
            fakedb.Master(id=7, name='some:master',
                          active=1, last_active=OTHERTIME),
            fakedb.Scheduler(id=21),
            fakedb.SchedulerMaster(schedulerid=21, masterid=7),
        ])
        deactivated = yield self.db.masters.setMasterState(
            masterid=7, active=False)
        self.assertTrue(deactivated)

        # check that the scheduler_masters row was deleted
        def thd(conn):
            tbl = self.db.model.scheduler_masters
            self.assertEqual(conn.execute(tbl.select()).fetchall(), [])
        yield self.db.pool.do(thd)


class TestFakeDB(unittest.TestCase, connector_component.FakeConnectorComponentMixin, Tests):

    @defer.inlineCallbacks
    def setUp(self):
        yield self.setUpConnectorComponent()
        self.reactor.advance(SOMETIME)


class TestRealDB(unittest.TestCase,
                 connector_component.ConnectorComponentMixin,
                 RealTests):

    @defer.inlineCallbacks
    def setUp(self):
        yield self.setUpConnectorComponent(
            table_names=['masters', 'schedulers', 'scheduler_masters'])

        self.reactor.advance(SOMETIME)

        self.db.masters = masters.MastersConnectorComponent(self.db)

    def tearDown(self):
        return self.tearDownConnectorComponent()
