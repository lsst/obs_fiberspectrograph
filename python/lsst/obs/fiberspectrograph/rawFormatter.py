__all__ = []

from lsst.obs.base import FitsRawFormatterBase
from .filters import FIBER_SPECTROGRAPH_FILTER_DEFINITIONS
from ._instrument import FiberSpectrograph
from .translator import FiberSpectrographTranslator
import fitsio
import astropy.units as u
from lsst.daf.base import PropertyList


class FiberSpectrographRawFormatter(FitsRawFormatterBase):
    cameraClass = FiberSpectrograph
    translatorClass = FiberSpectrographTranslator
    filterDefinitions = FIBER_SPECTROGRAPH_FILTER_DEFINITIONS

    def getDetector(self, id):
        return self.cameraClass().getCamera()[id]

    def read(self, component=None):
        """Read just the image component of the Exposure.

        Returns
        -------
        image : `~lsst.afw.image.Image`
            In-memory image component.
        """
        pytype = self.fileDescriptor.storageClass.pytype
        path = self.fileDescriptor.location.path

        sourceMd = dict(fitsio.read_header(path))
        md = PropertyList()
        md.update(sourceMd)
        if component is not None:
            if component == 'metadata':
                return md

        flux = fitsio.read(path)
        wavelength = fitsio.read(path, ext=md["PS1_0"], columns=md["PS1_1"]).flatten()

        wavelength = u.Quantity(wavelength, u.Unit(md["CUNIT1"]), copy=False)

        return pytype(wavelength, flux, md)
