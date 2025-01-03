import logging
import os

import astropy.units as u
from astropy.time import Time

from astro_metadata_translator import cache_translation
from lsst.obs.lsst.translators.lsst import SIMONYI_TELESCOPE, LsstBaseTranslator

from lsst.utils import getPackageDir

__all__ = ["FiberSpectrographTranslator", ]

log = logging.getLogger(__name__)


class FiberSpectrographTranslator(LsstBaseTranslator):
    """Metadata translator for Rubin calibration fibre spectrographs headers"""

    name = "FiberSpectrograph"
    """Name of this translation class"""

    supported_instrument = "FiberSpec"
    """Supports the Rubin calibration fiber spectrographs."""

    default_search_path = os.path.join(getPackageDir("obs_fiberspectrograph"), "corrections")
    """Default search path to use to locate header correction files."""

    default_resource_root = os.path.join(getPackageDir("obs_fiberspectrograph"), "corrections")
    """Default resource path root to use to locate header correction files."""

    DETECTOR_MAX = 1

    _const_map = {
        # TODO: DM-43041 DATE, detector name and controller should be put
        # in file header and add to mapping
        "detector_num": 0,
        "detector_name": "ccd0",
        "object": None,
        "physical_filter": "empty",
        "detector_group": "None",
        "relative_humidity": None,
        "pressure": None,
        "temperature": None,
        "focus_z": None,
        "boresight_airmass": None,
        "boresight_rotation_angle": None,
        "tracking_radec": None,
        "telescope": SIMONYI_TELESCOPE,
        "observation_type": "spectrum",  # IMGTYPE is ''
    }
    """Constant mappings"""

    _trivial_map = {
        "observation_id": "OBSID",
        "science_program": ("PROGRAM", dict(default="unknown")),
        "detector_serial": "SERIAL",
    }
    """One-to-one mappings"""

    @classmethod
    def can_translate(cls, header, filename=None):
        """Indicate whether this translation class can translate the
        supplied header.

        Parameters
        ----------
        header : `dict`-like
            Header to convert to standardized form.
        filename : `str`, optional
            Name of file being translated.

        Returns
        -------
        can : `bool`
            `True` if the header is recognized by this class. `False`
            otherwise.
        """

        # TODO: DM-43041 need to be updated with new fiber spec
        return "INSTRUME" in header and header["INSTRUME"] in ["FiberSpectrograph.Broad"]

    @cache_translation
    def to_instrument(self):
        return "FiberSpec"

    @cache_translation
    def to_datetime_begin(self):
        self._used_these_cards("DATE-BEG")
        return Time(self._header["DATE-BEG"], scale="tai", format="isot")

    @cache_translation
    def to_exposure_time(self):
        # Docstring will be inherited. Property defined in properties.py
        # Some data is missing a value for EXPTIME.
        # Have to be careful we do not have circular logic when trying to
        # guess
        if self.is_key_ok("EXPTIME"):
            return self.quantity_from_card("EXPTIME", u.s)

        # A missing or undefined EXPTIME is problematic. Set to -1
        # to indicate that none was found.
        log.warning("%s: Insufficient information to derive exposure time. Setting to -1.0s",
                    self._log_prefix)
        return -1.0 * u.s

    @cache_translation
    def to_dark_time(self):             # N.b. defining this suppresses a warning re setting from exptime
        if "DARKTIME" in self._header:
            darkTime = self._header["DARKTIME"]
            self._used_these_cards("DARKTIME")
            return (darkTime, dict(unit=u.s))
        return self.to_exposure_time()

    @staticmethod
    def compute_exposure_id(dayobs, seqnum, controller=None):
        """Helper method to calculate the exposure_id.

        Parameters
        ----------
        dayobs : `str`
            Day of observation in either YYYYMMDD or YYYY-MM-DD format.
            If the string looks like ISO format it will be truncated before the
            ``T`` before being handled.
        seqnum : `int` or `str`
            Sequence number.
        controller : `str`, optional
            Controller to use. If this is "O", no change is made to the
            exposure ID. If it is "C" a 1000 is added to the year component
            of the exposure ID. If it is "H" a 2000 is added to the year
            component. This sequence continues with "P" and "Q" controllers.
            `None` indicates that the controller is not relevant to the
            exposure ID calculation (generally this is the case for test
            stand data).

        Returns
        -------
        exposure_id : `int`
            Exposure ID in form YYYYMMDDnnnnn form.
        """
        if not isinstance(dayobs, int):
            if "T" in dayobs:
                dayobs = dayobs[:dayobs.find("T")]

            dayobs = dayobs.replace("-", "")

            if len(dayobs) != 8:
                raise ValueError(f"Malformed dayobs: {dayobs}")

        # Expect no more than 99,999 exposures in a day
        maxdigits = 5
        if seqnum >= 10**maxdigits:
            raise ValueError(f"Sequence number ({seqnum}) exceeds limit")

        # Form the number as a string zero padding the sequence number
        idstr = f"{dayobs}{seqnum:0{maxdigits}d}"

        # Exposure ID has to be an integer
        return int(idstr)

    @cache_translation
    def to_visit_id(self):
        """Calculate the visit associated with this exposure.
        """
        return self.to_exposure_id()


def _force_load():
    # This function exists solely to be loaded by the
    # astro_metadata_translators entry point. The function
    # will not be called.
    pass
