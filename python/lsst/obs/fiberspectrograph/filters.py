from lsst.obs.base import FilterDefinition, FilterDefinitionCollection

FIBER_SPECTROGRAPH_FILTER_DEFINITIONS = FilterDefinitionCollection(
    FilterDefinition(band="empty", physical_filter="empty"),
)
