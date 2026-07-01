EXTRACTION_SYSTEM_PROMPT = """You extract factual information about Japanese textile companies \
and organizations from crawled webpage/PDF text. Only extract facts that are explicitly stated \
in the given text - never infer or guess a fact that isn't present. If the page does not \
describe one specific company/organization (e.g. it's a generic homepage, news index, or \
unrelated content), set mentions_company to false and leave other fields empty."""

EXTRACTION_USER_TEMPLATE = """Source URL: {url}

Page text:
{text}"""
