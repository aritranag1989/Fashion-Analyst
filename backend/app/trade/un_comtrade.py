import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.trade.base import TradeDataProvider, TradeFlowRecord

# UN Comtrade country-level, HS-coded trade statistics. Free "preview" endpoint works without a
# subscription key at a reduced rate limit; setting UN_COMTRADE_API_KEY switches to the full data
# endpoint. See https://comtradeapi.un.org for the current API contract - verify field names
# against the live docs before relying on this in production, as UN Comtrade has changed its API
# shape across versions.
_PREVIEW_BASE_URL = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
_DATA_BASE_URL = "https://comtradeapi.un.org/data/v1/get/C/A/HS"

FLOW_CODE_TO_LABEL = {"M": "import", "X": "export"}


class UNComtradeProvider(TradeDataProvider):
    provider_name = "un_comtrade"
    granularity = "country"

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.un_comtrade_api_key
        self._client = httpx.AsyncClient(timeout=30.0)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_trade_flows(
        self, reporter_country: str, partner_country: str, hs_code: str | None = None
    ) -> list[TradeFlowRecord]:
        base_url = _DATA_BASE_URL if self._api_key else _PREVIEW_BASE_URL
        params = {
            "reporterCode": reporter_country,
            "partnerCode": partner_country,
            "cmdCode": hs_code or "TOTAL",
            "flowCode": "M,X",
        }
        headers = {"Ocp-Apim-Subscription-Key": self._api_key} if self._api_key else {}

        response = await self._client.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        payload = response.json()

        records: list[TradeFlowRecord] = []
        for row in payload.get("data", []):
            records.append(
                TradeFlowRecord(
                    reporter_country=str(row.get("reporterDesc", reporter_country)),
                    partner_country=str(row.get("partnerDesc", partner_country)),
                    hs_code=str(row.get("cmdCode", hs_code or "TOTAL")),
                    trade_flow=FLOW_CODE_TO_LABEL.get(row.get("flowCode"), row.get("flowCode", "")),
                    year=int(row.get("period", 0)),
                    value_usd=row.get("primaryValue"),
                    quantity=row.get("qty"),
                    source_name="UN Comtrade",
                    source_url=str(response.url),
                )
            )
        return records
