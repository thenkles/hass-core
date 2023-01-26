"""Bin collection entity."""

from __future__ import annotations

from datetime import datetime, time
import logging

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import CoordinatorEntity

GET_COLLECTION_DATES_URL = "https://www.cravendc.gov.uk/Umbraco/Api/NLPGAddressLookup/GetWasteCollectionDates2/"

_LOGGER = logging.getLogger(
    __name__,
)


class BinCollectionEntity(CoordinatorEntity, CalendarEntity):
    """Representation of a calendar event."""

    def __init__(self, coordinator, hass, address_text, address_id, bin_type) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._state = None
        self._id = address_id + "." + bin_type
        self._name = address_text + " - " + bin_type
        self._address_id = address_id
        self._bin_type = bin_type
        self._session = async_get_clientsession(hass)
        self._next_collection_date = None

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._id

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    def _create_event(self, event_date, bin_type):
        start = datetime.combine(event_date, time(0, 0, 0, 0))
        end = datetime.combine(event_date, time(23, 59, 59, 999999))

        return CalendarEvent(
            start=start,
            end=end,
            summary=bin_type,
            description="Bin collection",
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next event."""
        if self._bin_type not in self.coordinator.data["collection_dates"]:
            return None

        if len(self.coordinator.data["collection_dates"][self._bin_type]) == 0:
            return None

        event_date = self.coordinator.data["collection_dates"][self._bin_type][0]

        return self._create_event(event_date, self._bin_type)

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""

        if self._bin_type not in self.coordinator.data["collection_dates"]:
            return []

        if len(self.coordinator.data["collection_dates"][self._bin_type]) == 0:
            return []

        return [
            self._create_event(event_date, self._bin_type)
            for event_date in self.coordinator.data["collection_dates"][self._bin_type]
            if start_date.date() <= event_date <= end_date.date()
        ]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the light on.

        Example method how to request data updates.
        """
        # Do the turning on.
        # ...

        # Update the data
        await self.coordinator.async_request_refresh()
