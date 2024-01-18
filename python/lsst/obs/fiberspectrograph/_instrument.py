# This file is part of obs_fiberSpectrograph
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__all__ = ("FiberSpectrograph", )

import os.path

import lsst.obs.base.yamlCamera as yamlCamera
from lsst.utils import getPackageDir
from lsst.obs.base import VisitSystem
from lsst.obs.lsst import LsstCam
from .filters import FIBER_SPECTROGRAPH_FILTER_DEFINITIONS
from .translator import FiberSpectrographTranslator

PACKAGE_DIR = getPackageDir("obs_fiberSpectrograph")


class FiberSpectrograph(LsstCam):
    """Gen3 instrument for the Rubin fiber spectrographs

    Parameters
    ----------
    camera : `lsst.cameraGeom.Camera`
        Camera object from which to extract detector information.
    filters : `list` of `FilterDefinition`
        An ordered list of filters to define the set of PhysicalFilters
        associated with this instrument in the registry.
    """
    filterDefinitions = FIBER_SPECTROGRAPH_FILTER_DEFINITIONS
    instrument = "FiberSpec"
    policyName = "fiberSpectrograph"
    translatorClass = FiberSpectrographTranslator
    visitSystem = VisitSystem.BY_SEQ_START_END
    raw_definition = ("rawSpectrum",
                      ("instrument", "physical_filter", "exposure", "detector"),
                      "FiberSpectrum")

    @classmethod
    def getCamera(cls):
        # Constructing a YAML camera takes a long time but we rely on
        # yamlCamera to cache for us.
        # N.b. can't inherit as PACKAGE_DIR isn't in the class
        cameraYamlFile = os.path.join(PACKAGE_DIR, "policy", f"{cls.policyName}.yaml")
        return yamlCamera.makeCamera(cameraYamlFile)

    def getRawFormatter(self, dataId):
        # Docstring inherited from Instrument.getRawFormatter
        # local import to prevent circular dependency
        from .rawFormatter import FiberSpectrographRawFormatter
        return FiberSpectrographRawFormatter

    def extractDetectorRecord(self, camGeomDetector):
        """Create a Gen3 Detector entry dict from a cameraGeom.Detector.
        """
        return dict(
            instrument=self.getName(),
            id=camGeomDetector.getId(),
            full_name=camGeomDetector.getName(),
        )
