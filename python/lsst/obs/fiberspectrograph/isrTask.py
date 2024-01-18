# This file is part of obs_fiberSpectrograph
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__all__ = ["IsrTask", "IsrTaskConfig"]

import numpy as np

import lsst.geom
import lsst.pex.config as pexConfig
import lsst.pipe.base.connectionTypes as cT

import lsst.ip.isr


class IsrTaskConnections(lsst.ip.isr.isrTask.IsrTaskConnections):
    ccdExposure = cT.Input(
        name="rawSpectrum",
        doc="Input spectrum to process.",
        storageClass="FiberSpectrum",
        dimensions=["instrument", "exposure", "detector"],
    )
    bias = cT.PrerequisiteInput(
        name="bias",
        doc="Input bias calibration.",
        storageClass="FiberSpectrum",
        dimensions=["instrument", "detector"],
        isCalibration=True,
    )
    outputExposure = cT.Output(
        name="spectrum",
        doc="Corrected spectrum.",
        storageClass="FiberSpectrum",
        dimensions=["instrument", "exposure", "detector"],
    )

    def __init__(self, *, config=None):
        super().__init__(config=config)


class IsrTaskConfig(lsst.ip.isr.IsrTaskConfig, pipelineConnections=IsrTaskConnections):
    """Configuration parameters for IsrTask.

    Items are grouped in the order in which they are executed by the task.
    """
    datasetType = pexConfig.Field(
        dtype=str,
        doc="Dataset type for input data; users will typically leave this alone, "
        "but camera-specific ISR tasks will override it",
        default="rawSpectrum",
    )


class IsrTask(lsst.ip.isr.IsrTask):
    """Apply common instrument signature correction algorithms to a raw frame.

    The process for correcting imaging data is very similar from
    camera to camera.  This task provides a vanilla implementation of
    doing these corrections, including the ability to turn certain
    corrections off if they are not needed.  The inputs to the primary
    method, `run()`, are a raw exposure to be corrected and the
    calibration data products. The raw input is a single chip sized
    mosaic of all amps including overscans and other non-science
    pixels.

    The __init__ method sets up the subtasks for ISR processing, using
    the defaults from `lsst.ip.isr`.

    Parameters
    ----------
    args : `list`
        Positional arguments passed to the Task constructor.
        None used at this time.
    kwargs : `dict`, optional
        Keyword arguments passed on to the Task constructor.
        None used at this time.
    """
    ConfigClass = IsrTaskConfig
    _DefaultName = "isr"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def ensureExposure(self, inputExposure, *args, **kwargs):
        return inputExposure

    def convertIntToFloat(self, ccdExposure):
        return ccdExposure

    def maskAmplifier(self, ccdExposure, amp, defects):
        flux = ccdExposure.flux

        saturated = flux > amp.getSaturation()
        flux[saturated] = np.NaN
        ccdExposure.mask[saturated] |= ccdExposure.getPlaneBitMask(self.config.saturatedMaskName)

        return False

    def roughZeroPoint(self, exposure):
        pass
