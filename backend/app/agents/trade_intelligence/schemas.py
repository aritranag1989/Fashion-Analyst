from pydantic import BaseModel


class TradeContextRequest(BaseModel):
    reporter_country: str = "392"  # UN M49 numeric code for Japan
    partner_country: str = "356"  # UN M49 numeric code for India
    hs_code: str | None = None
