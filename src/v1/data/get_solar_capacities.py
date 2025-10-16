"""The idea is to make a csv of all the solar capacites around the world.

The csv will countain
country_code, capacity_gw, country_name, source
"""

import pandas as pd

url = (
    "https://storage.googleapis.com/emb-prod-bkt-publicdata/public-downloads/"
    "yearly_full_release_long_format.csv"
)

# read csv into pandas dataframe
df = pd.read_csv(url)


# only select year 2024
df = df[df["Year"] == 2024]
# only select solar
df = df[df["Category"] == "Capacity"]
df = df[df["Variable"] == "Solar"]

df = df.rename(
    columns={"Value": "capacity_gw", "Area": "country_name", "ISO 3 code": "country_code"},
)
df = df[["country_code", "capacity_gw", "country_name"]]
df["source"] = "Ember"

df.set_index("country_code", inplace=True)

# manually add some countries not already present in the Ember dataset
# Additional countries with reliable sources from Wikipedia/Ember 2024 data
# All data sourced from https://en.wikipedia.org/wiki/Solar_power_by_country
manual_countries = {
    "UKR": {
        "country_name": "Ukraine",
        "capacity_gw": 1.2,
        "source": ("Wikipedia - https://en.wikipedia.org/wiki/Solar_power_by_country"),
    },
    "TJK": {
        "country_name": "Tajikistan",
        "capacity_gw": 0.0006,
        "source": "CABAR.asia 2024 (600 kW USAID project) - https://cabar.asia/en/tajikistan-solar-energy-in-support-of-hydropower-plants",
    },
    "TKM": {
        "country_name": "Turkmenistan",
        "capacity_gw": 0.005,
        "source": "UNDP 2012 Report - https://www.undp.org/sites/g/files/zskgke326/files/migration/eurasia/Turkmenistan.pdf",
    },
    "TLS": {
        "country_name": "Timor-Leste",
        "capacity_gw": 0.0011,
        "source": "Asian Development Bank sector assessment 2016-2020 - https://www.adb.org/sites/default/files/linked-documents/cps-tim-2016-2020-ssa-05.pdf",
    },
    "DZA": {
        "country_name": "Algeria",
        "capacity_gw": 0.46,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "SEN": {
        "country_name": "Senegal",
        "capacity_gw": 0.23,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "AGO": {
        "country_name": "Angola",
        "capacity_gw": 0.31,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "BEN": {
        "country_name": "Benin",
        "capacity_gw": 0.13,
        "source": "https://ember-energy.org/latest-insights/global-electricity-review-2025/",
    },
    "BFA": {
        "country_name": "Burkina Faso",
        "capacity_gw": 0.09,
        "source": "https://ember-energy.org/latest-insights/global-electricity-review-2025/",
    },
    "BDI": {
        "country_name": "Burundi",
        "capacity_gw": 0.017,
        "source": "https://ember-energy.org/latest-insights/global-electricity-review-2025/",
    },
    "CMR": {
        "country_name": "Cameroon",
        "capacity_gw": 0.09,
        "source": "https://ember-energy.org/latest-insights/the-first-evidence-of-a-take-off-in-solar-in-africa/",
    },
    "CPV": {
        "country_name": "Cape Verde",
        "capacity_gw": 0.026,
        "source": "IRENA 2023 via PV Magazine - https://www.pv-magazine.com/2024/11/14/cape-verde-runs-tender-for-10-mw-of-solar/",
    },
    "CAF": {
        "country_name": "Central African Republic",
        "capacity_gw": 0.01,
        "source": "https://ember-energy.org/latest-insights/the-first-evidence-of-a-take-off-in-solar-in-africa/",
    },
    "COM": {
        "country_name": "Comoros",
        "capacity_gw": 0.004034,
        "source": "IRENA 2023 via PVKnowhow - https://www.pvknowhow.com/solar-report/comoros/",
    },
    "DJI": {
        "country_name": "Djibouti",
        "capacity_gw": 0.02,
        "source": "https://ember-energy.org/latest-insights/global-electricity-review-2025/",
    },
    "ERI": {
        "country_name": "Eritrea",
        "capacity_gw": 0.01,
        "source": "https://ember-energy.org/latest-insights/the-first-evidence-of-a-take-off-in-solar-in-africa/",
    },
    "SWZ": {
        "country_name": "Eswatini",
        "capacity_gw": 0.03,
        "source": "https://www.globalsolarcouncil.org/news/global-solar-council-africas-solar-market-set-to-surge-42-in-2025-but-finance-bottlenecks-threaten-growth/",
    },
    "GAB": {
        "country_name": "Gabon",
        "capacity_gw": 0.01,
        "source": "https://ember-energy.org/latest-insights/the-first-evidence-of-a-take-off-in-solar-in-africa/",
    },
    "GMB": {
        "country_name": "Gambia",
        "capacity_gw": 0.03,
        "source": "https://www.pv-magazine.com/2023/02/10/gambia-inaugurates-23-mw-pv-plant/",
    },
    "GNQ": {
        "country_name": "Equatorial Guinea",
        "capacity_gw": 0.005,
        "source": "https://www.ren21.net/gsr-2025/downloads/pdf/go/GSR_2025_GO_2025_Full_Report.pdf",
    },
    "GIN": {
        "country_name": "Guinea",
        "capacity_gw": 0.01,
        "source": "https://ember-energy.org/latest-insights/global-electricity-review-2025/",
    },
    "GNB": {
        "country_name": "Guinea-Bissau",
        "capacity_gw": 0.005,
        "source": "https://www.ren21.net/gsr-2025/downloads/pdf/go/GSR_2025_GO_2025_Full_Report.pdf",
    },
    "CIV": {
        "country_name": "Ivory Coast",
        "capacity_gw": 0.05,
        "source": "https://ember-energy.org/latest-insights/global-electricity-review-2025/",
    },
    "LSO": {
        "country_name": "Lesotho",
        "capacity_gw": 0.005,
        "source": "https://ember-energy.org/latest-insights/global-electricity-review-2025/",
    },
    "MRT": {
        "country_name": "Mauritania",
        "capacity_gw": 0.04,
        "source": "https://ember-energy.org/latest-insights/global-electricity-review-2025/",
    },
    "MWI": {
        "country_name": "Malawi",
        "capacity_gw": 0.03,
        "source": "https://www.ren21.net/gsr-2025/downloads/pdf/go/GSR_2025_GO_2025_Full_Report.pdf",
    },
    "STP": {
        "country_name": "Sao Tome and Principe",
        "capacity_gw": 0.0036,
        "source": "World Bank National Energy Compact 2025 - https://thedocs.worldbank.org/en/doc/680a427c0554b887598d86080fdcc775-0010012025/original/Sao-Tome-National-Energy-Compact-Mission-300.pdf",
    },
    "SLE": {
        "country_name": "Sierra Leone",
        "capacity_gw": 0.02,
        "source": "https://ember-energy.org/latest-insights/the-first-evidence-of-a-take-off-in-solar-in-africa/",
    },
    "SOM": {
        "country_name": "Somalia",
        "capacity_gw": 0.02,
        "source": "https://ember-energy.org/latest-insights/the-first-evidence-of-a-take-off-in-solar-in-africa/",
    },
    "SSD": {
        "country_name": "South Sudan",
        "capacity_gw": 0.0384,
        "source": "Combined: PVKnowhow 2025 (38.4 MW total) - https://www.pvknowhow.com/solar-report/south-sudan/",
    },
    "SYC": {
        "country_name": "Seychelles",
        "capacity_gw": 0.017,
        "source": "PVKnowhow 2024 Report - https://www.pvknowhow.com/solar-report/seychelles/",
    },
    "TCD": {
        "country_name": "Chad",
        "capacity_gw": 0.02,
        "source": "https://ember-energy.org/latest-insights/the-first-evidence-of-a-take-off-in-solar-in-africa/",
    },
    "ALB": {
        "country_name": "Albania",
        "capacity_gw": 0.21,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "COD": {
        "country_name": "Democratic Republic of Congo",
        "capacity_gw": 0.03,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "CUB": {
        "country_name": "Cuba",
        "capacity_gw": 0.28,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "GHA": {
        "country_name": "Ghana",
        "capacity_gw": 0.19,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "GTM": {
        "country_name": "Guatemala",
        "capacity_gw": 0.10,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "HND": {
        "country_name": "Honduras",
        "capacity_gw": 0.53,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "IDN": {
        "country_name": "Indonesia",
        "capacity_gw": 0.63,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "IRQ": {
        "country_name": "Iraq",
        "capacity_gw": 0.04,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "ISR": {
        "country_name": "Israel",
        "capacity_gw": 5.52,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "JOR": {
        "country_name": "Jordan",
        "capacity_gw": 2.59,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "LBN": {
        "country_name": "Lebanon",
        "capacity_gw": 1.00,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "MLI": {
        "country_name": "Mali",
        "capacity_gw": 0.10,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "MUS": {
        "country_name": "Mauritius",
        "capacity_gw": 0.147,
        "source": "Ministry of Energy Annual Report 2023-2024 - https://publicutilities.govmu.org/Documents/Annual%20Report2023-2024.pdf",
    },
    "NAM": {
        "country_name": "Namibia",
        "capacity_gw": 0.16,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "NPL": {
        "country_name": "Nepal",
        "capacity_gw": 0.25,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "PAN": {
        "country_name": "Panama",
        "capacity_gw": 0.65,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "SDN": {
        "country_name": "Sudan",
        "capacity_gw": 0.19,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "SGP": {
        "country_name": "Singapore",
        "capacity_gw": 1.348,
        "source": "Energy Market Authority Singapore 2024 - https://ema.gov.sg/resources/singapore-energy-statistics/chapter6",
    },
    "TGO": {
        "country_name": "Togo",
        "capacity_gw": 0.07,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "UZB": {
        "country_name": "Uzbekistan",
        "capacity_gw": 3.8,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "YEM": {
        "country_name": "Yemen",
        "capacity_gw": 0.29,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    "ZMB": {
        "country_name": "Zambia",
        "capacity_gw": 0.13,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
    },
    # Our World in Data sources
    "ETH": {
        "country_name": "Ethiopia",
        "capacity_gw": 0.08,
        "source": (
            "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity"
        ),
    },
    "LBY": {
        "country_name": "Libya",
        "capacity_gw": 0.02,
        "source": (
            "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity"
        ),
    },
    "MDG": {
        "country_name": "Madagascar",
        "capacity_gw": 0.01,
        "source": (
            "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity"
        ),
    },
    "MOZ": {
        "country_name": "Mozambique",
        "capacity_gw": 0.01,
        "source": (
            "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity"
        ),
    },
    "RWA": {
        "country_name": "Rwanda",
        "capacity_gw": 0.12,
        "source": (
            "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity"
        ),
    },
    "TZA": {
        "country_name": "Tanzania",
        "capacity_gw": 0.02,
        "source": (
            "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity"
        ),
    },
    "UGA": {
        "country_name": "Uganda",
        "capacity_gw": 0.04,
        "source": (
            "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity"
        ),
    },
    "ZWE": {
        "country_name": "Zimbabwe",
        "capacity_gw": 0.09,
        "source": (
            "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity"
        ),
    },
    "AFG": {
        "country_name": "Afghanistan",
        "capacity_gw": 0.02,
        "source": (
            "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity"
        ),
    },
    "BHR": {
        "country_name": "Bahrain",
        "capacity_gw": 0.065,
        "source": "IEA Report 2024 via SAU Energy - https://www.saurenergy.me/emerging-middle-eastern-nations-to-advance-re-goals/",
    },
    "BTN": {
        "country_name": "Bhutan",
        "capacity_gw": 0.04,
        "source": (
            "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity"
        ),
    },

    # ----------------------- Other small countries from "Our World in Data" ----------------------
    # These countries have very small solar capacities but are not present in the Ember dataset
    # but have reliable sources from "Our World in Data"

    # ---------------- Africa ----------------
    "BWA": {
        "country_name": "Botswana",
        "capacity_gw": 0.006,
        "source": "www.pv-magazine.com/",
    },
    "COG": {
        "country_name": "Congo",
        "capacity_gw": 0.0007,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "NER": {
        "country_name": "Niger",
        "capacity_gw": 0.08,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "LBR": {
        "country_name": "Liberia",
        "capacity_gw": 0.003,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "ESH": {
        "country_name": "Western Sahara",
        "capacity_gw": 0.1,
        "source": "WSRW Report 2024 - https://wsrw.org/en/news/renewable-energy",
    },

    # ---------------- Asia ----------------
    "HKG": {
        "country_name": "Hong Kong",
        "capacity_gw": 0.33,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "PRK": {
        "country_name": "North Korea",
        "capacity_gw": 0.14,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "MDV": {
        "country_name": "Maldives",
        "capacity_gw": 0.07,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "PSE": {
        "country_name": "Palestine",
        "capacity_gw": 0.2,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "BRN": {
        "country_name": "Brunei",
        "capacity_gw": 0.005,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "SYR": {
        "country_name": "Syria",
        "capacity_gw": 0.06,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "LAO": {
        "country_name": "Laos",
        "capacity_gw": 0.06,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "KGZ": {
        "country_name": "Kyrgyzstan",
        "capacity_gw": 0.00008,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },

    # ---------------- Caribbean ----------------
    "ATG": {
        "country_name": "Antigua and Barbuda",
        "capacity_gw": 0.02,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "BRB": {
        "country_name": "Barbados",
        "capacity_gw": 0.07,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "DMA": {
        "country_name": "Dominica",
        "capacity_gw": 0.0003,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "GRD": {
        "country_name": "Grenada",
        "capacity_gw": 0.0035,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "KNA": {
        "country_name": "Saint Kitts and Nevis",
        "capacity_gw": 0.0045,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "LCA": {
        "country_name": "Saint Lucia",
        "capacity_gw": 0.005,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "VCT": {
        "country_name": "Saint Vincent and the Grenadines",
        "capacity_gw": 0.0045,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "BHS": {
        "country_name": "Bahamas",
        "capacity_gw": 0.02,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "HTI": {
        "country_name": "Haiti",
        "capacity_gw": 0.004,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "JAM": {
        "country_name": "Jamaica",
        "capacity_gw": 0.12,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "TTO": {
        "country_name": "Trinidad and Tobago",
        "capacity_gw": 0.0045,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },

    # ---------------- Oceania ----------------
    "FJI": {
        "country_name": "Fiji",
        "capacity_gw": 0.01,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "PNG": {
        "country_name": "Papua New Guinea",
        "capacity_gw": 0.005,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "SLB": {
        "country_name": "Solomon Islands",
        "capacity_gw": 0.006,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "VUT": {
        "country_name": "Vanuatu",
        "capacity_gw": 0.005,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "WSM": {
        "country_name": "Samoa",
        "capacity_gw": 0.016,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "TON": {
        "country_name": "Tonga",
        "capacity_gw": 0.02,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "FSM": {
        "country_name": "Micronesia",
        "capacity_gw": 0.007,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "PLW": {
        "country_name": "Palau",
        "capacity_gw": 0.02,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "KIR": {
        "country_name": "Kiribati",
        "capacity_gw": 0.004,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "NRU": {
        "country_name": "Nauru",
        "capacity_gw": 0.003,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "TUV": {
        "country_name": "Tuvalu",
        "capacity_gw": 0.0045,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "MHL": {
        "country_name": "Marshall Islands",
        "capacity_gw": 0.003,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "COK": {
        "country_name": "Cook Islands",
        "capacity_gw": 0.0055,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "PYF": {
        "country_name": "French Polynesia",
        "capacity_gw": 0.07,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "NIU": {
        "country_name": "Niue",
        "capacity_gw": 0.0018,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "ASM": {
        "country_name": "American Samoa",
        "capacity_gw": 0.007,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "GUM": {
        "country_name": "Guam",
        "capacity_gw": 0.10,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "TKL": {
        "country_name": "Tokelau",
        "capacity_gw": 0.001,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },

    # ---------------- South America ----------------
    "PRY": {
        "country_name": "Paraguay",
        "capacity_gw": 0.001,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "SUR": {
        "country_name": "Suriname",
        "capacity_gw": 0.01,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "VEN": {
        "country_name": "Venezuela",
        "capacity_gw": 0.004,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "GUY": {
        "country_name": "Guyana",
        "capacity_gw": 0.018,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },

    # ---------------- Central America ----------------
    "BLZ": {
        "country_name": "Belize",
        "capacity_gw": 0.007,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "NIC": {
        "country_name": "Nicaragua",
        "capacity_gw": 0.035,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },

    # ---------------- Europe ----------------
    "AND": {
        "country_name": "Andorra",
        "capacity_gw": 0.009,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
    },
    "ISL": {
        "country_name": "Iceland",
        "capacity_gw": 0.007,
        "source": "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity",
        },

    # --- Missing entries identified on 2025-09-26 ---
    "ATA": {
        "country_name": "Antarctica",
        "capacity_gw": 0.0002,
        "source": "British Antarctic Survey renewable projects 2025 - https://www.bas.ac.uk/media-post/renewables-milestone-reached-in-antarctica/",
    },
    "ATF": {
        "country_name": "French Southern and Antarctic Lands",
        "capacity_gw": 0.0032,
        "source": "green-overseas.org & TAAF renewable energy installations - http://www.green-overseas.org/en/pays-et-territoires/french-southern-and-antarctic-lands",
    },
    "FLK": {
        "country_name": "Falkland Islands",
        "capacity_gw": 0.0034,
        "source": "Falkland Islands Energy Strategy & green-overseas.org - https://www.green-overseas.org/en/pays-et-territoires/falkland-islands",
    },
    "GRL": {
        "country_name": "Greenland",
        "capacity_gw": 0.001,
        "source": "World Population Review 2025 - https://worldpopulationreview.com/country-rankings/solar-power-by-country",
    },
    "NCL": {
        "country_name": "New Caledonia",
        "capacity_gw": 0.185,
        "source": "World Population Review 2025 - https://worldpopulationreview.com/country-rankings/solar-power-by-country",
    },
}

manual_countries_df = pd.DataFrame.from_dict(manual_countries, orient="index")
manual_countries_df.index.name = "country_code"

df = pd.concat([df, manual_countries_df])

# remove duplicate indices and will keep the last entry [which should be the manually added one]
df = df[~df.index.duplicated(keep="last")]

df.to_csv("src/v1/data/solar_capacities.csv")
