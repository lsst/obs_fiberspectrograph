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

__all__ = ("FiberSpectrum",)

import numpy as np
import astropy.io.fits
import fitsio
import astropy.units as u
from ._instrument import FiberSpectrograph
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
    def __init__(self, wavelength, flux, md=None):
        self.wavelength = wavelength
        self.flux = flux
        self.md = md

        self.info = Info(md)
        self.detector = FiberSpectrograph().getCamera()[0]

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

    @staticmethod
    def readFits(path):
        """Read a Spectrum from disk"

        Parameters
        ----------
        path : `str`
            The file to read

        Returns
        -------
        spectrum : `~lsst.obs.fiberSpectrograph.FiberSpectrum`
            In-memory spectrum.
        """
        md = dict(fitsio.read_header(path))
        flux = fitsio.read(path)
        wavelength = fitsio.read(path, ext=md["PS1_0"], columns=md["PS1_1"]).flatten()

        wavelength = u.Quantity(wavelength, u.Unit(md["CUNIT1"]), copy=False)

        return FiberSpectrum(wavelength, flux, md)

    def writeFits(self, path):
        """Write a Spectrum to disk

        Parameters
        ----------
        path : `str`
            The file to write
        """
        hdl = DataManager(self).make_hdulist()

        hdl.writeto(path)


class DataManager:
    """A data packager for `Spectrum` objects
    """

    wcs_table_name = "WCS-TAB"
    """Name of the table containing the wavelength WCS (EXTNAME)."""
    wcs_table_ver = 1
    """WCS table version (EXTVER)."""
    wcs_column_name = "wavelength"
    """Name of the table column containing the wavelength information."""

    # The version of the FITS file format produced by this class.
    FORMAT_VERSION = 1

    def __init__(self, spectrum):
        self.spectrum = spectrum

    def make_hdulist(self):
        """Generate a FITS hdulist built from SpectrographData.
        Parameters
        ----------
        spec : `SpectrographData`
            The data from which to build the FITS hdulist.
        Returns
        -------
        hdulist : `astropy.io.fits.HDUList`
            The FITS hdulist.
        """
        hdu1 = self.make_primary_hdu()
        hdu2 = self.make_wavelength_hdu()
        return astropy.io.fits.HDUList([hdu1, hdu2])

    def make_fits_header(self):
        """Return a FITS header built from a Spectrum"""
        hdr = astropy.io.fits.Header()

        hdr["FORMAT_V"] = self.FORMAT_VERSION
        for k, v in self.spectrum.md.items():
            hdr[k] = v

        # WCS headers - Use -TAB WCS definition
        wcs_cards = [
            "WCSAXES =                    1 / Number of WCS axes",
            "CRPIX1  =                  0.0 / Reference pixel on axis 1",
            "CRVAL1  =                  0.0 / Value at ref. pixel on axis 1",
            "CNAME1  = 'Wavelength'         / Axis name for labeling purposes",
            "CTYPE1  = 'WAVE-TAB'           / Wavelength axis by lookup table",
            "CDELT1  =                  1.0 / Pixel size on axis 1",
            f"CUNIT1  = '{self.spectrum.wavelength.unit.name:8s}'           / Units for axis 1",
            f"PV1_1   = {self.wcs_table_ver:20d} / EXTVER  of bintable extension for -TAB arrays",
            f"PS1_0   = '{self.wcs_table_name:8s}'           / EXTNAME of bintable extension for -TAB arrays",
            f"PS1_1   = '{self.wcs_column_name:8s}'         / Wavelength coordinate array",
        ]
        for c in wcs_cards:
            hdr.append(astropy.io.fits.Card.fromstring(c))

        return hdr

    def make_primary_hdu(self):
        """Return the primary HDU built from a Spectrum."""

        hdu = astropy.io.fits.PrimaryHDU(
            data=self.spectrum.flux, header=self.make_fits_header()
        )
        return hdu

    def make_wavelength_hdu(self):
        """Return the wavelength HDU built from a Spectrum."""

        # The wavelength array must be 2D (N, 1) in numpy but (1, N) in FITS
        wavelength = self.spectrum.wavelength.reshape([self.spectrum.wavelength.size, 1])

        # Create a Table. It will be a single element table
        table = astropy.table.Table()

        # Create the wavelength column
        # Create the column explicitly since it is easier to ensure the
        # shape this way.
        wavecol = astropy.table.Column([wavelength], unit=wavelength.unit.name)

        # The column name must match the PS1_1 entry from the primary HDU
        table[self.wcs_column_name] = wavecol

        # The name MUST match the value of PS1_0 and the version MUST
        # match the value of PV1_1
        hdu = astropy.io.fits.BinTableHDU(table, name=self.wcs_table_name, ver=1)
        return hdu
