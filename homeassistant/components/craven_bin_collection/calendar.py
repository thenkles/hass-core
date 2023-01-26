"""Calendar platform."""

from collections.abc import Iterable
from datetime import timedelta
import logging
from typing import Any, cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .bin_collection_api import BinCollectionApi
from .bin_collection_entity import BinCollectionEntity

_LOGGER = logging.getLogger(
    __name__,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Async setup entry."""

    address_id = entry.data.get("house_id")
    bins = cast(Iterable[Any], entry.data.get("bins"))
    polling_interval = cast(float, entry.data.get("polling_interval"))

    api = BinCollectionApi(hass, address_id)
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Bin collection",
        update_method=api.fetch_collection_dates,
        update_interval=timedelta(minutes=polling_interval),
    )

    entities = [
        BinCollectionEntity(coordinator, hass, entry.title, address_id, bin)
        for bin in bins
    ]

    # await coordinator.async_config_entry_first_refresh()
    await coordinator.async_refresh()

    async_add_entities(entities)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Async setup platform."""
    if discovery_info is None:
        return

    return True
