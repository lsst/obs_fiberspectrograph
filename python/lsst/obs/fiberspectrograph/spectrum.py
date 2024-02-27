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
from astro_metadata_translator import ObservationInfo


class FiberSpectrum:
    """Define a spectrum from a fiber spectrograph.

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

    def __init__(self, wavelength, flux, md=None, detectorId=0, mask=None, variance=None):
        self.wavelength = wavelength
        self.flux = flux
        self.metadata = md

        self.info = ObservationInfo(md)
        self.detector = FiberSpectrograph().getCamera()[detectorId]

        mask_temp = afwImage.MaskX(1, 1)
        self.getPlaneBitMask = mask_temp.getPlaneBitMask  # ughh, awful Mask API
        self.mask = mask
        self.variance = variance

    def getDetector(self):
        """Get fiber spectrograph detector."
        """
        return self.detector

    def getInfo(self):
        """Get observation information."
        """
        return self.info

    def getMetadata(self):
        """Get the spectrum metadata."
        """
        return self.md

    def getFilter(self):
        """Get filter label."
        """
        return FiberSpectrograph.filterDefinitions[0].makeFilterLabel()

    def getBBox(self):
        """Get bounding box."
        """
        return self.detector.getBBox()

    @classmethod
    def readFits(cls, path):
        """Read a Spectrum from disk."

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
        format_v = md["FORMAT_V"]

        if format_v == 1:
            flux = fitsfile[0].data
            wavelength = fitsfile[md["PS1_0"]].data[md["PS1_1"]].flatten()

            wavelength = u.Quantity(wavelength, u.Unit(md["CUNIT1"]), copy=False)

            mask_temp = afwImage.MaskX(1, 1)
            mask = np.zeros(flux.shape, dtype=mask_temp.array.dtype)
            variance = np.zeros_like(flux)
            if len(fitsfile) == 4:
                mask = fitsfile[2].data
                variance = fitsfile[3].data
        else:
            raise ValueError(f"FORMAT_V has changed from 1 to {format_v}")

        return cls(wavelength, flux, md=md, mask=mask, variance=variance)

    def writeFits(self, path):
        """Write a Spectrum to disk.

        Parameters
        ----------
        path : `str`
            The file to write
        """
        hdl = DataManager(self).make_hdulist()

        hdl.writeto(path)
