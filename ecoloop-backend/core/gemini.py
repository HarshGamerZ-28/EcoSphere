import httpx
import json
import os
from typing import Optional
from dotenv import load_dotenv

# Load from root .env first (production), then fallback
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

async def call_gemini(prompt: str, api_key: Optional[str] = None, temperature: float = 0.7) -> Optional[str]:
    """Call Gemini API and return raw text response."""
    key = api_key or GEMINI_API_KEY
    if not key:
        return None
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": 1500}
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(f"{GEMINI_URL}?key={key}", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

async def ai_match_waste(waste_name: str, category: str, quantity: str,
                         description: str, api_key: Optional[str] = None) -> list[dict]:
    """Use Gemini to find best buyer matches for a waste material."""
    prompt = f"""You are EcoLoop's AI for India's B2B circular economy platform.
Match this industrial waste with verified buyers. Respond ONLY with valid JSON array, no markdown.

Waste: {waste_name}
Category: {category}
Quantity: {quantity or 'unspecified'}
Properties: {description or 'standard grade'}

Return exactly 3 buyer matches as JSON array:
[{{
  "company": "Indian company name",
  "type": "Industry type",
  "location": "City, State",
  "score": 85,
  "reasoning": "Specific reason this buyer needs this waste as raw material",
  "co2_saved": "X.X tonnes CO2 saved vs landfill",
  "price_range": "₹XX–₹XX/kg",
  "tags": ["tag1", "tag2", "tag3"],
  "compliance": "CPCB/GST/ISO etc"
}}]

Rules: scores 65–98, first match highest. Use realistic Indian company names and locations."""

    raw = await call_gemini(prompt, api_key, temperature=0.8)
    if not raw:
        raise ValueError("Gemini API returned empty response")
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)

async def ai_generate_description(waste_name: str, category: str, api_key: Optional[str] = None) -> str:
    """Generate a professional listing description for a waste material."""
    prompt = f"""Write a concise 2-sentence professional listing description for industrial waste on India's B2B circular economy marketplace.
Waste: {waste_name}
Category: {category}
Include: material properties, typical industrial use cases, quality notes.
Max 60 words. Plain text only. No bullet points."""
    result = await call_gemini(prompt, api_key, temperature=0.6)
    if not result:
        raise ValueError("Gemini API returned empty response for description")
    return result.strip()

async def ai_waste_insights(waste_name: str, category: str, api_key: Optional[str] = None) -> str:
    """Get market insights for a waste material."""
    prompt = f"""You are an industrial waste expert for India's circular economy.
Give 3 key insights about "{waste_name}" ({category}) waste:
1. Best recycling/reuse method available in India
2. Current market price range (in ₹/kg, India-specific)
3. Environmental benefit if diverted from landfill (quantified)
Format as 3 short bullet points. Max 80 words total. Be specific and data-driven."""
    result = await call_gemini(prompt, api_key, temperature=0.5)
    if not result:
        raise ValueError("Gemini API returned empty response for insights")
    return result.strip()

# ── Fallback (no API key) ──────────────────────────
FALLBACK_MATCHES = {
    "Plastic Scrap": [
        {"company":"PlasCycle India Pvt Ltd","type":"Plastic Recycler","location":"Pune, Maharashtra","score":94,"reasoning":"Specialized HDPE/LDPE recycler with 500T/month capacity. Same state reduces logistics cost by 30%.","co2_saved":"2.1 tonnes CO₂","price_range":"₹40–55/kg","tags":["Food-grade OK","Same-state","Daily pickup"],"compliance":"CPCB Reg."},
        {"company":"GreenPak Solutions","type":"Packaging Manufacturer","location":"Ahmedabad, Gujarat","score":86,"reasoning":"Sources recycled plastic for flexible packaging. Offers long-term contracts at premium rates.","co2_saved":"1.6 tonnes CO₂","price_range":"₹35–48/kg","tags":["Bulk buyer","Long-term contract"],"compliance":"ISO 9001"},
        {"company":"EcoMold Pvt Ltd","type":"Injection Moulding","location":"Surat, Gujarat","score":76,"reasoning":"Uses recycled plastic for industrial components. Flexible on grade requirements.","co2_saved":"1.1 tonnes CO₂","price_range":"₹30–40/kg","tags":["Any grade","Weekly pickup"],"compliance":"GST Reg."},
    ],
    "Metal Waste": [
        {"company":"GreenMetal Inc","type":"Metal Recycler","location":"Pune, Maharashtra","score":97,"reasoning":"India top-rated metal recycler on EcoLoop. Certified smelting facility, same-day pickup for 1T+ orders.","co2_saved":"3.8 tonnes CO₂","price_range":"₹100–135/kg","tags":["Gold Tier","Certified smelter","Best price"],"compliance":"CPCB + ISO 14001"},
        {"company":"AlloyWorks Ltd","type":"Alloy Manufacturer","location":"Rajkot, Gujarat","score":88,"reasoning":"Aluminum specialist for automotive alloys. Competitive pricing for 500kg+ lots.","co2_saved":"2.4 tonnes CO₂","price_range":"₹95–120/kg","tags":["Aluminum specialist","5T/day"],"compliance":"BIS Certified"},
        {"company":"SteelCraft India","type":"Steel Fabricator","location":"Mumbai, Maharashtra","score":74,"reasoning":"Accepts mixed metal scraps for structural steel. Convenient Mumbai pickup.","co2_saved":"1.7 tonnes CO₂","price_range":"₹80–100/kg","tags":["Mixed metals OK"],"compliance":"GST Reg."},
    ],
    "Electronic Waste": [
        {"company":"CircuitTech Recyclers","type":"E-Waste Processor","location":"Bangalore, Karnataka","score":96,"reasoning":"Category-1 CPCB authorized e-waste recycler. Full documentation for PCB and precious metal recovery.","co2_saved":"5.8 tonnes CO₂","price_range":"₹160–200/kg","tags":["CPCB Cat-1","Precious metals","Full docs"],"compliance":"CPCB E-Waste Auth."},
        {"company":"MetalReclaim Ltd","type":"Precious Metal Recovery","location":"Mumbai, Maharashtra","score":87,"reasoning":"Extracts gold, silver, palladium from PCBs. Provides assay report with payment.","co2_saved":"3.5 tonnes CO₂","price_range":"₹140–180/kg","tags":["Assay report","Gold extraction"],"compliance":"BIS + CPCB"},
        {"company":"GreenChip India","type":"Component Refurbisher","location":"Delhi NCR","score":68,"reasoning":"Refurbishes working components for secondary market. Simpler compliance requirements.","co2_saved":"1.8 tonnes CO₂","price_range":"₹100–140/kg","tags":["Working parts only"],"compliance":"GST Reg."},
    ],
}

def get_fallback_matches(category: str) -> list[dict]:
    default = FALLBACK_MATCHES.get("Metal Waste")
    return FALLBACK_MATCHES.get(category, default)
