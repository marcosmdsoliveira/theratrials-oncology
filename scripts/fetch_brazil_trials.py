"""
Fetch active non-theranostic clinical trials recruiting in Brazil
from ClinicalTrials.gov API v2.

Output: structured JSON for manual curation into trials_br.js
"""
import json
import urllib.request
import urllib.parse
import time
import sys

API_BASE = "https://clinicaltrials.gov/api/v2/studies"

QUERIES = [
    # Próstata (non-theranostic)
    {"label": "Próstata", "neoplasia": "prostata", "terms": "prostate cancer", "extra": "enzalutamide OR olaparib OR abiraterone OR darolutamide OR talazoparib OR niraparib OR ipatasertib OR cabozantinib"},
    {"label": "Próstata IO", "neoplasia": "prostata", "terms": "prostate cancer", "extra": "pembrolizumab OR nivolumab OR atezolizumab OR ipilimumab"},
    # Mama
    {"label": "Mama", "neoplasia": "mama", "terms": "breast cancer", "extra": "trastuzumab deruxtecan OR sacituzumab OR capivasertib OR alpelisib OR ribociclib OR abemaciclib OR tucatinib"},
    # ccRCC
    {"label": "ccRCC", "neoplasia": "rim", "terms": "renal cell carcinoma", "extra": "belzutifan OR cabozantinib OR lenvatinib OR nivolumab OR pembrolizumab"},
    # Melanoma
    {"label": "Melanoma", "neoplasia": "melanoma", "terms": "melanoma", "extra": "relatlimab OR tebentafusp OR pembrolizumab OR nivolumab OR ipilimumab OR lifileucel"},
    # Hematologia - Mieloma
    {"label": "Mieloma", "neoplasia": "mieloma", "terms": "multiple myeloma", "extra": "teclistamab OR talquetamab OR elranatamab OR ciltacabtagene OR idecabtagene OR belantamab"},
    # Hematologia - Linfoma
    {"label": "Linfoma", "neoplasia": "linfoma", "terms": "lymphoma", "extra": "glofitamab OR epcoritamab OR loncastuximab OR polatuzumab OR mosunetuzumab"},
    # Bexiga / Urotelial
    {"label": "Urotelial", "neoplasia": "urotelial", "terms": "urothelial carcinoma OR bladder cancer", "extra": "enfortumab OR sacituzumab OR erdafitinib OR pembrolizumab OR nivolumab OR avelumab"},
    # Pâncreas
    {"label": "Pâncreas", "neoplasia": "pancreas", "terms": "pancreatic cancer", "extra": "olaparib OR niraparib OR pembrolizumab OR nab-paclitaxel"},
    # Endométrio
    {"label": "Endométrio", "neoplasia": "endometrio", "terms": "endometrial cancer", "extra": "dostarlimab OR pembrolizumab OR lenvatinib OR mirvetuximab"},
    # Cérvix
    {"label": "Cérvix", "neoplasia": "cervix", "terms": "cervical cancer", "extra": "tisotumab OR pembrolizumab OR cemiplimab OR bevacizumab"},
    # Hepatocarcinoma
    {"label": "HCC", "neoplasia": "hcc", "terms": "hepatocellular carcinoma", "extra": "atezolizumab OR bevacizumab OR durvalumab OR tremelimumab OR lenvatinib OR cabozantinib"},
    # Glioma
    {"label": "Glioma", "neoplasia": "glioma", "terms": "glioblastoma OR glioma", "extra": "temozolomide OR bevacizumab OR pembrolizumab OR nivolumab OR vorasidenib"},
    # Tireoide
    {"label": "Tireoide", "neoplasia": "tireoide", "terms": "thyroid cancer", "extra": "selpercatinib OR pralsetinib OR cabozantinib OR lenvatinib OR pembrolizumab"},
]

def fetch_studies(condition_terms, intervention_terms, max_results=20):
    """Query ClinicalTrials.gov API v2 for recruiting studies in Brazil."""
    params = {
        "query.cond": condition_terms,
        "query.intr": intervention_terms,
        "filter.overallStatus": "RECRUITING",
        "filter.geo": "distance(lat[-19.9191],lon[-43.9386],500mi)",  # BH center, wide radius
        "countTotal": "true",
        "pageSize": str(max_results),
        "fields": "NCTId,BriefTitle,OfficialTitle,Phase,OverallStatus,Condition,InterventionName,InterventionType,LeadSponsorName,LocationCity,LocationState,LocationCountry,LocationFacility,BriefSummary,EligibilityCriteria,StudyType",
        "format": "json",
    }
    url = API_BASE + "?" + urllib.parse.urlencode(params)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TheraTrials-Oncology/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return None

def fetch_studies_v2(condition_terms, intervention_terms, max_results=20):
    """Alternate query using query.term for broader matching."""
    params = {
        "query.term": f"({condition_terms}) AND ({intervention_terms}) AND AREA[LocationCountry]Brazil",
        "filter.overallStatus": "RECRUITING",
        "countTotal": "true",
        "pageSize": str(max_results),
        "fields": "NCTId,BriefTitle,OfficialTitle,Phase,OverallStatus,Condition,InterventionName,InterventionType,LeadSponsorName,LocationCity,LocationState,LocationCountry,LocationFacility,BriefSummary,EligibilityCriteria",
        "format": "json",
    }
    url = API_BASE + "?" + urllib.parse.urlencode(params)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TheraTrials-Oncology/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data
    except Exception as e:
        print(f"  ERROR v2: {e}", file=sys.stderr)
        return None

def extract_studies(data, label, neoplasia):
    """Extract relevant info from API response."""
    results = []
    if not data or "studies" not in data:
        return results

    for study in data["studies"]:
        proto = study.get("protocolSection", {})
        ident = proto.get("identificationModule", {})
        status_mod = proto.get("statusModule", {})
        design = proto.get("designModule", {})
        sponsor_mod = proto.get("sponsorCollaboratorsModule", {})
        eligibility = proto.get("eligibilityModule", {})
        desc = proto.get("descriptionModule", {})

        # Get locations in Brazil
        locations_mod = proto.get("contactsLocationsModule", {})
        locations = locations_mod.get("locations", [])
        br_locations = [l for l in locations if l.get("country") == "Brazil"]

        if not br_locations:
            continue

        nct = ident.get("nctId", "")
        title = ident.get("briefTitle", "")
        official_title = ident.get("officialTitle", "")

        # Phase
        phases = design.get("phases", [])
        phase_str = ", ".join(p.replace("PHASE", "Fase ") for p in phases) if phases else "N/A"

        # Sponsor
        lead = sponsor_mod.get("leadSponsor", {})
        sponsor = lead.get("name", "")

        # Interventions
        arms_mod = proto.get("armsInterventionsModule", {})
        interventions = arms_mod.get("interventions", [])
        interv_names = [i.get("name", "") for i in interventions]
        interv_types = list(set(i.get("type", "") for i in interventions))

        # Brazil cities/states
        cities = list(set(l.get("city", "") for l in br_locations if l.get("city")))
        states = list(set(l.get("state", "") for l in br_locations if l.get("state")))
        facilities = [f"{l.get('facility', '')} · {l.get('city', '')}/{l.get('state', '')}" for l in br_locations]

        # Brief summary
        summary = desc.get("briefSummary", "")[:300]

        # Eligibility
        elig_text = eligibility.get("eligibilityCriteria", "")[:500]

        results.append({
            "nct": nct,
            "title": title,
            "official_title": official_title,
            "phase": phase_str,
            "sponsor": sponsor,
            "interventions": interv_names,
            "intervention_types": interv_types,
            "brazil_cities": cities,
            "brazil_states": states,
            "brazil_facilities": facilities,
            "summary": summary,
            "eligibility_snippet": elig_text,
            "neoplasia_group": neoplasia,
            "neoplasia_label": label,
            "url": f"https://clinicaltrials.gov/study/{nct}",
        })

    return results

# Collect existing NCTs to avoid duplicates
existing_ncts = {
    "NCT06119581", "NCT05828550", "NCT06330064", "NCT06224842", "NCT04534205",
    "NCT06252649", "NCT05176366", "NCT06547957", "NCT05924139", "NCT06568029",
    "NCT06283745", "NCT06125262",
}

all_results = []
seen_ncts = set(existing_ncts)

for q in QUERIES:
    print(f"\n{'='*60}")
    print(f"Searching: {q['label']} ({q['neoplasia']})")
    print(f"  Condition: {q['terms']}")
    print(f"  Intervention: {q['extra'][:80]}...")

    data = fetch_studies_v2(q["terms"], q["extra"], max_results=15)

    total = 0
    if data:
        total = data.get("totalCount", 0)
        print(f"  Total matches: {total}")

        studies = extract_studies(data, q["label"], q["neoplasia"])
        new_studies = []
        for s in studies:
            if s["nct"] not in seen_ncts:
                seen_ncts.add(s["nct"])
                new_studies.append(s)

        print(f"  New unique studies with Brazil sites: {len(new_studies)}")
        for s in new_studies:
            cities_str = ", ".join(s["brazil_cities"][:3])
            print(f"    {s['nct']}: {s['title'][:80]}... [{cities_str}]")

        all_results.extend(new_studies)
    else:
        print(f"  No results or API error")

    time.sleep(0.5)  # Be nice to the API

print(f"\n{'='*60}")
print(f"TOTAL NEW TRIALS FOUND: {len(all_results)}")
print(f"Across {len(set(r['neoplasia_group'] for r in all_results))} neoplasia groups")

# Save raw results
output_path = r"C:\Users\marco\Desktop\TheraTrials Oncology\site\scripts\brazil_trials_raw.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

print(f"\nSaved to: {output_path}")
