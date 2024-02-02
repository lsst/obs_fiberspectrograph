"""Unit tests for Gen3 fiberspectrograph raw data ingest.
"""

import unittest
import os
import lsst.utils.tests

from lsst.obs.base.ingest_tests import IngestTestBase
from lsst.obs.fiberspectrograph import FiberSpectrograph
from lsst.obs.fiberspectrograph.filters import FIBER_SPECTROGRAPH_FILTER_DEFINITIONS

# TODO DM 42620
# testDataPackage = "testdata_fiberSpectrograph"
# try:
#     testDataDirectory = lsst.utils.getPackageDir(testDataPackage)
# except (LookupError, lsst.pex.exceptions.NotFoundError):
#     testDataDirectory = None
testDataDirectory = os.path.join(os.path.dirname(__file__), "data")


class FiberSpectrographIngestTestCase(IngestTestBase, lsst.utils.tests.TestCase):
    instrumentClassName = "lsst.obs.fiberspectrograph.FiberSpectrograph"
    visits = None                       # we don't have a definition of visits
    ingestDatasetTypeName = "rawSpectrum"

    def setUp(self):
        self.ingestdir = os.path.dirname(__file__)
        self.instrument = FiberSpectrograph()
        self.file = os.path.join(testDataDirectory,
                                 "Broad_fiberSpecBroad_2024-01-09T17:41:34.996.fits")

        day_obs = 20240109
        seq_num = 4
        self.dataIds = [dict(instrument="FiberSpec", exposure=100000 * day_obs + seq_num, detector=0)]
        self.filterLabel = FIBER_SPECTROGRAPH_FILTER_DEFINITIONS[0].makeFilterLabel()

        super().setUp()


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
