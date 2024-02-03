__all__ = []

from lsst.daf.butler import Formatter
from .filters import FIBER_SPECTROGRAPH_FILTER_DEFINITIONS
from ._instrument import FiberSpectrograph
from .translator import FiberSpectrographTranslator
from .spectrum import FiberSpectrum


class FiberSpectrographRawFormatter(Formatter):
    cameraClass = FiberSpectrograph
    translatorClass = FiberSpectrographTranslator
    fiberSpectrumClass = FiberSpectrum
    filterDefinitions = FIBER_SPECTROGRAPH_FILTER_DEFINITIONS
    extension = ".fits"

    def getDetector(self, id):
        return self.cameraClass().getCamera()[id]

    def read(self, component=None):
        """Read fiberspectrograph data.

        Returns
        -------
        FiberSpectrum: `~lsst.obs.fiberspectrograph.FiberSpectrum`
            In-memory spectrum.
        """
        path = self.fileDescriptor.location.path

        return self.fiberSpectrumClass.readFits(path)

    def write(self):
        path = self.fileDescriptor.location.path

        return self.fiberSpectrumClass.writeFits(path)
