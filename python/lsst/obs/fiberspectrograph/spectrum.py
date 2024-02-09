# This file is part of obs_fiberspectrograph
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

__all__ = ("FiberSpectrum",)

import numpy as np
import astropy.io.fits
import astropy.units as u
from ._instrument import FiberSpectrograph
from .data_manager import DataManager
import lsst.afw.image as afwImage


class VisitInfo:
    def __init__(self, md):
        self.exposureTime = md["EXPTIME"]

    def getExposureTime(self):
        return self.exposureTime


class Info:
    def __init__(self, md):
        self.visitInfo = VisitInfo(md)

    def getVisitInfo(self):
        return self.visitInfo


class FiberSpectrum:
    """Define a spectrum from a fiber spectrograph

    Parameters
    ----------
    wavelength : `numpy.ndarray`
        Spectrum wavelength in units provided by the spectrum file.
    flux: `numpy.ndarray`
        Spectrum flux.
    md: `dict`
        Dictionary of the spectrum headers.
    detectorId : `int`
        Optional Detector ID for this data.
    """

    def __init__(self, wavelength, flux, md=None, detectorId=0):
        self.wavelength = wavelength
        self.flux = flux
        self.md = md

        self.detector = FiberSpectrograph().getCamera()[detectorId]

        self.__Mask = afwImage.MaskX(1, 1)
        self.getPlaneBitMask = self.__Mask.getPlaneBitMask  # ughh, awful Mask API
        self.mask = np.zeros(flux.shape, dtype=self.__Mask.array.dtype)
        self.variance = np.zeros_like(flux)

    def getDetector(self):
        return self.detector

    def getInfo(self):
        return self.info

    def getMetadata(self):
        return self.md

    def getFilter(self):
        return FiberSpectrograph.filterDefinitions[0].makeFilterLabel()

    def getBBox(self):
        return self.detector.getBBox()

    @classmethod
    def readFits(cls, path):
        """Read a Spectrum from disk"

        Parameters
        ----------
        path : `str`
            The file to read

        Returns
        -------
        spectrum : `~lsst.obs.fiberspectrograph.FiberSpectrum`
            In-memory spectrum.
        """

        fitsfile = astropy.io.fits.open(path)
        md = dict(fitsfile[0].header)

        if md["FORMAT_V"] >= 1:
            flux = fitsfile[0].data
            wavelength = fitsfile[md["PS1_0"]].data[md["PS1_1"]].flatten()

            wavelength = u.Quantity(wavelength, u.Unit(md["CUNIT1"]), copy=False)

        return cls(wavelength, flux, md)

    def writeFits(self, path):
        """Write a Spectrum to disk

        Parameters
        ----------
        path : `str`
            The file to write
        """
        hdl = DataManager(self).make_hdulist()

        hdl.writeto(path)
