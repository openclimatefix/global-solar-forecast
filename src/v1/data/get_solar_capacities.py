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
    "TKM": {
        "country_name": "Turkmenistan",
        "capacity_gw": 0.0,
        "source": ("The Global Economy - https://www.theglobaleconomy.com/"),
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
        "capacity_gw": 0.03,
        "source": "https://ember-energy.org/latest-insights/global-electricity-review-2025/",
    },
    "CAF": {
        "country_name": "Central African Republic",
        "capacity_gw": 0.01,
        "source": "https://ember-energy.org/latest-insights/the-first-evidence-of-a-take-off-in-solar-in-africa/",
    },
    "COM": {
        "country_name": "Comoros",
        "capacity_gw": 0.005,
        "source": "https://www.ren21.net/gsr-2025/downloads/pdf/go/GSR_2025_GO_2025_Full_Report.pdf",
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
    "LES": {
        "country_name": "Lesotho",
        "capacity_gw": 0.005,
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
        "capacity_gw": 0.005,
        "source": "https://www.ren21.net/gsr-2025/downloads/pdf/go/GSR_2025_GO_2025_Full_Report.pdf",
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
        "capacity_gw": 0.01,
        "source": "https://www.ren21.net/gsr-2025/downloads/pdf/go/GSR_2025_GO_2025_Full_Report.pdf",
    },
    "SYC": {
        "country_name": "Seychelles",
        "capacity_gw": 0.01,
        "source": "https://ember-energy.org/latest-insights/global-electricity-review-2025/",
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
        "country_name": "Dem. Rep. Congo",
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
        "capacity_gw": 0.13,
        "source": (
            "Wikipedia (Ember 2024 data) - https://en.wikipedia.org/wiki/Solar_power_by_country"
        ),
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
        "capacity_gw": 0.05,
        "source": (
            "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity"
        ),
    },
    "BTN": {
        "country_name": "Bhutan",
        "capacity_gw": 0.04,
        "source": (
            "Our World in Data - https://ourworldindata.org/grapher/installed-solar-pv-capacity"
        ),
    },
    "BWA": {
        "country_name": "Botswana",
        "capacity_gw": 0.006,
        "source": "www.pv-magazine.com/",
    },
}

manual_countries_df = pd.DataFrame.from_dict(manual_countries, orient="index")
manual_countries_df.index.name = "country_code"

df = pd.concat([df, manual_countries_df])

df.to_csv("src/v1/data/solar_capacities.csv")
