"""Config flow for Craven District bin collection integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import selector

from .const import DOMAIN

GET_ADDRESSES_URL = (
    "http://www.cravendc.gov.uk/Umbraco/Api/NLPGAddressLookup/GetAddressesForPostCode/"
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("postcode"): str,
    }
)

STEP_SELECT_BINS_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("general"): bool,
        vol.Required("recycling"): bool,
        vol.Required("garden"): bool,
        vol.Required("polling_interval", default=60): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=1440)
        ),
    }
)


def _enhance_bin_selection_schema(schema):
    schema.schema["general"] = selector({"boolean": {}})
    schema.schema["recycling"] = selector({"boolean": {}})
    schema.schema["garden"] = selector({"boolean": {}})
    schema.schema["polling_interval"] = selector(
        {
            "number": {
                "min": 1,
                "max": 1440,
                "mode": "box",
                "unit_of_measurement": "minutes",
            }
        }
    )


_enhance_bin_selection_schema(STEP_SELECT_BINS_DATA_SCHEMA)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Craven District bin collection."""

    VERSION = 1
    postcode = ""
    house_id = None
    address_text = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        self.postcode = user_input["postcode"]
        return await self.async_step_select_address()

    async def async_step_select_address(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the address selection step."""

        if user_input:
            address = user_input["address"].split("|")
            self.house_id = address[0]
            self.address_text = address[1]
            return await self.async_step_select_bins()

        step_schema = vol.Schema(
            {
                vol.Required("address"): str,
            }
        )

        session = async_get_clientsession(self.hass)
        response = await session.get(GET_ADDRESSES_URL + self.postcode)
        addresses = await response.json()

        address_options = [
            {
                "label": address["AddressText"],
                "value": address["UPRN"] + "|" + address["AddressText"],
            }
            for address in addresses
        ]

        step_schema.schema["address"] = selector(
            {"select": {"options": address_options, "mode": "dropdown"}}
        )

        return self.async_show_form(step_id="select_address", data_schema=step_schema)

    async def async_step_select_bins(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the bin selection step."""

        if user_input:
            bins = []

            if user_input["general"]:
                bins.append("General")
            if user_input["recycling"]:
                bins.append("Recycling")
            if user_input["garden"]:
                bins.append("GardenWaste")

            data = {
                "house_id": self.house_id,
                "bins": bins,
                "polling_interval": user_input["polling_interval"],
            }

            return self.async_create_entry(title=str(self.address_text), data=data)

        return self.async_show_form(
            step_id="select_bins", data_schema=STEP_SELECT_BINS_DATA_SCHEMA
        )


class OptionsFlowHandler(OptionsFlow):
    """Options flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            bins = []

            if user_input["general"]:
                bins.append("General")
            if user_input["recycling"]:
                bins.append("Recycling")
            if user_input["garden"]:
                bins.append("GardenWaste")

            data = {
                "house_id": self.config_entry.data["house_id"],
                "bins": bins,
                "polling_interval": user_input["polling_interval"],
            }

            self.hass.config_entries.async_update_entry(
                self.config_entry, data=data, options={}
            )
            return self.async_create_entry(title="", data={})

        bins = self.config_entry.data["bins"]
        polling_interval = self.config_entry.data["polling_interval"]

        schema = vol.Schema(
            {
                vol.Required("general", default="General" in bins): bool,
                vol.Required("recycling", default="Recycling" in bins): bool,
                vol.Required("garden", default="GardenWaste" in bins): bool,
                vol.Required("polling_interval", default=polling_interval): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=1440)
                ),
            }
        )

        _enhance_bin_selection_schema(schema)

        return self.async_show_form(step_id="init", data_schema=schema)
