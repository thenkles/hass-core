"""Craven bin collection API."""
from datetime import date, datetime
import logging

from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

GET_COLLECTION_DATES_URL = "https://www.cravendc.gov.uk/Umbraco/Api/NLPGAddressLookup/GetWasteCollectionDates2/"


class BinCollectionApi:
    """Craven bin collection API client."""

    def __init__(self, hass, address_id):
        """Class constructor."""
        self._session = async_get_clientsession(hass)
        self._address_id = address_id

    async def fetch_collection_dates(self):
        """Fetch collection dates."""

        response = await self._session.get(GET_COLLECTION_DATES_URL + self._address_id)
        response_data = await response.json()

        collection_dates = {}

        for entry in response_data["CollectionCallenader"]:
            collection_date = datetime.fromisoformat(entry["Date"]).date()
            bin_type = entry["CollectionType"]

            if bin_type not in collection_dates:
                collection_dates[bin_type] = []

            if collection_date >= date.today():
                collection_dates[bin_type].append(collection_date)

        for bin_type in collection_dates:  # pylint: disable=consider-using-dict-items
            collection_dates[bin_type].sort()

        return {"raw": response_data, "collection_dates": collection_dates}
