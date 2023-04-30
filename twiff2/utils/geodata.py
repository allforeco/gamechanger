#   FridaysForFuture Database Collector Function
#   Copyright (C) 2020 Jan Lindblad, Lena Douglas
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

""""
-------> SYNC INFO <---------
Direct copy from Coffer
Please keep this file in sync with Coffer!
"""

class Geodata:
    nix_country_list = ["afghanistan", "afganestan", "ukraine", "russia", "georgia", "belarus", "moldova"]

    @staticmethod
    def clean_zip_static(name_with_zip):
        def is_clean_word_static(word):
            tipp = "0123456789()"
            for ch in word:
                if ch in tipp:
                    return False
            return True

        name_words = name_with_zip.split(" ")
        clean_name = []
        # We don't want words containing these characters
        for name_word in name_words:
            if is_clean_word_static(name_word):
                clean_name += [name_word]
        return " ".join([w for w in clean_name if w != ''])

    @staticmethod
    def is_country_with_states_static(country):
        return country.lower() in [c.lower() for c in Geo.canonical_names[Geo.STATE]]

    @staticmethod
    def get_canonical_state_name_static(country, state):
        return state
        # FIXME: Code below not doing what the function name implies. Do we really want this to work?
        # canonical_country = Geodata.get_canonical_country_name_static(country)
        # return Geo.canonical_names[Geo.STATE][canonical_country].get(state, state)

    @staticmethod
    def get_canonical_country_name_static(country):
        return Geo.canonical_names[Geo.COUNTRY].get(country.lower(), country)

    @staticmethod
    def get_continent_from_country_static(country):
        raise 0


class Geo:
    # The Geo class handles the atlas data structure, which lists all
    # countries, states, cities, and venues known to FFF. It is
    # initialized with the known countries and states. The rest is read
    # if needed.

    # The atlas contains names of different sub-categories:
    EARTH = "earth"
    COUNTRY = "country"
    STATE = "state"
    CITY = "city/county"
    VENUE = "venue"
    Z = None

    def get_city_name(raw_city_name):
        return Geo.clean_zip(raw_city_name.split(",")[-1])

    # Returns the name of a location regardless if it has sub-locations
    # or not
    def get_label(geo_info):
        return geo_info[0] if isinstance(geo_info, tuple) else geo_info

    # Returns the location tuple for a given atlas path
    def get_named_loc(geo_path):
        p = Geo.atlas["Earth"]
        for pname in geo_path:
            if p == None:
                print(f"### geo_get_path({geo_path}): {pname} not found")
                return None
            if not isinstance(p, tuple):
                print(f"### geo_get_path({geo_path}): {pname} gives '{p}', strange format")
                return None
            if pname in p[1]:
                p = p[1][pname]
            else:
                return None
        return p

    # Return the subcategory string ("country", etc) from a location tuple
    def get_subcat(geo_tuple):
        return geo_tuple[0]

    # Return the location name("USA", "Paris", etc) from a location tuple
    def get_name(geo_tuple):
        return geo_tuple[1]

    # The canonical_names data structure contains names that we sometimes
    # get from Google Maps, which are wrong. At least from our perspective.
    # the canonical names remap such names to the name we want.
    canonical_names = {
        COUNTRY: {
            "trikomo": "Cyprus",
            "maharashtra": "India",
            "ramnagar": "India",
            "kalimantan": "Indonesia",
            "prizren": "Kosovo",
            "prishtina": "Kosovo",
            "mitrovica": "Kosovo",
            "pulwama": "Jammu and Kashmir",
            "muzaffarabad": "Jammu and Kashmir",
            "sopore": "Jammu and Kashmir",
            "jammu": "Jammu and Kashmir",
            "kashmir": "Jammu and Kashmir",
            "kathua": "Jammu and Kashmir",
            "sonamarg": "Jammu and Kashmir",
            "baramulla": "Jammu and Kashmir",
            "kulgam": "Jammu and Kashmir",
            "srinagar": "Jammu and Kashmir",
            "boujdour province": "Morocco",
            "kotli": "Pakistan",
            "shigar": "Pakistan",
            "yasin valley": "Pakistan",
            "pr": "Puerto Rico",
            "jeddah saudi arabia": "Saudi Arabia",
            "riyadh saudi arabia": "Saudi Arabia",
            "al khobar saudi arabia": "Saudi Arabia",
            "umeå": "Sweden",
            "umeå universitet": "Sweden",
            "united states": "USA",
            "usa": "USA",
            "united kingdom": "UK",
            "uk": "UK",  # Handle incorrect capitalization
            "dubai - united arab emirates": "United Arab Emirates",
            "abu dhabi - united arab emirates": "United Arab Emirates",
            "ajman - united arab emirates": "United Arab Emirates",
        },
        STATE: {
            # "Bangladesh":{},
            "Canada": {
                "AB": "AB-Alberta",
                "BC": "BC-British Columbia",
                "MB": "MB-Manitoba",
                "NB": "NB-New Brunswick",
                "NL": "NL-Newfoundland and Labrador",
                "NS": "NS-Nova Scotia",
                "NT": "NT-Northwest Territories",
                "NU": "NU-Nunavut",
                "ON": "ON-Ontario",
                "PE": "PE-Prince Edward Island",
                "QC": "QC-Quebec",
                "SK": "SK-Saskatchewan",
                "YT": "YT-Yukon",
            },
            "India": {},
            "USA": {
                "AL": "AL-Alabama",
                "AK": "AK-Alaska",
                "AZ": "AZ-Arizona",
                "AR": "AR-Arkansas",
                "CA": "CA-California",
                "CO": "CO-Colorado",
                "CT": "CT-Connecticut",
                "DE": "DE-Delaware",
                "FL": "FL-Florida",
                "GA": "GA-Georgia",
                "HI": "HI-Hawaii",
                "ID": "ID-Idaho",
                "IL": "IL-Illinois",
                "IN": "IN-Indiana",
                "IA": "IA-Iowa",
                "KS": "KS-Kansas",
                "KY": "KY-Kentucky",
                "LA": "LA-Louisiana",
                "ME": "ME-Maine",
                "MD": "MD-Maryland",
                "MA": "MA-Massachusetts",
                "MI": "MI-Michigan",
                "MN": "MN-Minnesota",
                "MS": "MS-Mississippi",
                "MO": "MO-Missouri",
                "MT": "MT-Montana",
                "NE": "NE-Nebraska",
                "NV": "NV-Nevada",
                "NH": "NH-New Hampshire",
                "NJ": "NJ-New Jersey",
                "NM": "NM-New Mexico",
                "NY": "NY-New York",
                "NC": "NC-North Carolina",
                "ND": "ND-North Dakota",
                "OH": "OH-Ohio",
                "OK": "OK-Oklahoma",
                "OR": "OR-Oregon",
                "PA": "PA-Pennsylvania",
                "RI": "RI-Rhode Island",
                "SC": "SC-South Carolina",
                "SD": "SD-South Dakota",
                "TN": "TN-Tennessee",
                "TX": "TX-Texas",
                "UT": "UT-Utah",
                "VT": "VT-Vermont",
                "VA": "VA-Virginia",
                "WA": "WA-Washington",
                "DC": "DC-District of Columbia",
                "WV": "WV-West Virginia",
                "WI": "WI-Wisconsin",
                "WY": "WY-Wyoming",
            },
        },
    }

    # atlas data structure
    #
    # The atlas data structure is built up as a set of a dictionary where
    # each element is either None (called Z in the structures), when there
    # is no further data about this place, or a 2-tuple (level, dict),
    # where level is a string indicating if what the members of the dict
    # are, e.g. countries, states, cities or venues.
    #
    # The structure is hard initialized to contain the known list of
    # countries and states around the world, as given by the Google Maps API
    # Before the structure is used, it is filled with all the cities and
    # venues that have been reported in any FFF forms so far. This is done
    # by calling Geo.init_from_livedata()

    atlas = {"Earth": (COUNTRY, {
        ## Example structure:
        ##  "Abkhazia":(CITY, {
        ##    "Sokhumi":Z,
        ##  }),
        ##  "Sweden":(CITY, {
        ##    "Abisko":Z,
        ##    "Stockholm":(VENUE, {
        ##      "Akalla":Z,
        ##      "Bromma":Z,
        ##      "Mynttorget":Z,
        ##    }),
        ##    "Alingsås":Z,
        ##    "Ammarnäs":Z,
        ##    "Aneby":Z,
        ##    "Arboga":Z,
        ##    "Arjeplog":Z,
        ##    "Arvika":Z,
        ##    "Avesta":Z,
        ##  }),
        ##  "USA":(STATE, {
        ##    "NY-New York":(CITY, {
        ##      "New York":(VENUE, {
        ##        "Bronx":Z,
        ##        "Central Park":Z,
        ##        "UN Building":Z,
        ##      }),
        ##      "Newark":Z,
        ##    }),
        ##    "AL-Alabama":Z,
        ##  }),
        ##  "France":(CITY, {
        ##    "Paimpol":Z,
        ##    "Paris":(VENUE, {
        ##      "Gare du Nord":Z,
        ##      "Champs de Mars":Z,
        ##    }),
        ##    "Pau":Z,
        ##    "Pavie":Z,
        ##    "Payrac":Z,
        ##    "Perpignan":Z,
        ##    "Pierrelatte":Z,
        ##    "Versailles":(VENUE,{
        ##      "Place d'Armes":Z,
        ##    }),
        ##    "Plaimpied-Givaudins":Z,
        ##    "Ploërmel":Z,
        ##    "Plœuc-L'Hermitage":(VENUE, {
        ##      "Plœuc-sur-Lié":Z,
        ##    }),
        ##    "Poitiers":Z,
        ##    "Pont-Audemer":Z,
        ##    "Pont-l'Abbé":Z,
        ##  }),
        "Abkhazia": Z,
        "Afghanistan": Z,
        "Albania": Z,
        "Algeria": Z,
        "Andorra": Z,
        "Angola": Z,
        "Antarctica": Z,
        "Antigua and Barbuda": Z,
        "Arctic": Z,
        "Argentina": Z,
        "Armenia": Z,
        "Aruba": Z,
        "Assam": Z,
        "Australia": Z,
        "Austria": Z,
        "Azerbaijan": Z,
        "Bahrain": Z,
        "Bangladesh": (STATE, {
            "Dhaka": Z,
            "Noakhali": Z,
            "Chittagong": Z,
            "Jessore": Z,
            "Tangail": Z,
            "Satkhira": Z,
            "Gazipur": Z,
            "Khulna": Z,
            "Feni": Z,
            "Rajshahi": Z,
            "Kushtia": Z,
            "Gaibandha": Z,
            "Jaipurhat": Z,
            "Jamalpur": Z,
            "Barisal": Z,
            "Gopalganj": Z,
            "Satkhira": Z,
            "Netrokona": Z,
            "Pirojpur": Z,
            "Barguna": Z,
            "Jhalokati": Z,
            "Bhola": Z,
            "Sunamganj": Z,
            "Habiganj": Z,
            "Moulvi Bazar": Z,
            "Sherpur": Z,
            "Mymensingh": Z,
            "Rangpur": Z,
            "Sylhet": Z,
            "Brahmanbaria": Z,
            "Cox's Bazar": Z,
            "Narayanganj Sadar Upazila": Z,
            "Thakurgaon": Z,
            "Nilphamari": Z,
            "Meherpur": Z,
            "Lakshmipur": Z,
            "Narsingdi": Z,
            "Kishoreganj": Z,
            "Chuadanga": Z,
            "Magura": Z,
            "Bogra": Z,
            "Pabna": Z,
            "Chapainawabganj": Z,
            "Natore": Z,
            "Savar Upazila": Z,
            "Comilla": Z,
            "Faridpur": Z,
        }),
        "Belarus": Z,
        "Belgium": Z,
        "Belize": Z,
        "Benin": Z,
        "Bermuda": Z,
        "Bhutan": Z,
        "Bolivia": Z,
        "Bosnia and Herzegovina": Z,
        "Botswana": Z,
        "Brazil": Z,
        "British Virgin Islands": Z,
        "Brunei": Z,
        "Bulgaria": Z,
        "Burkina Faso": Z,
        "Burundi": Z,
        "CNMI": Z,
        "Cambodia": Z,
        "Cameroon": Z,
        "Canada": (STATE, {
            "AB-Alberta": Z,
            "BC-British Columbia": Z,
            "MB-Manitoba": Z,
            "NB-New Brunswick": Z,
            "NL-Newfoundland and Labrador": Z,
            "NS-Nova Scotia": Z,
            "NT-Northwest Territories": Z,
            "NU-Nunavut": Z,
            "ON-Ontario": Z,
            "PE-Prince Edward Island": Z,
            "QC-Quebec": Z,
            "SK-Saskatchewan": Z,
            "YT-Yukon": Z,
        }),
        "Caribbean": Z,
        "Cayman Islands": Z,
        "Chile": Z,
        "China": Z,
        "Colombia": Z,
        "Costa Rica": Z,
        "Croatia": Z,
        "Cuba": Z,
        "Curaçao": Z,
        "Cyprus": Z,
        "Czechia": Z,
        "Côte d'Ivoire": Z,
        "Democratic Republic of the Congo": Z,
        "Denmark": Z,
        "Djibouti": Z,
        "Dominica": Z,
        "Dominican Republic": Z,
        "Ecuador": Z,
        "Egypt": Z,
        "El Salvador": Z,
        "Equatorial Guinea": Z,
        "Estonia": Z,
        "Eswatini": Z,
        "Ethiopia": Z,
        "Famagusta": Z,
        "Faroe Islands": Z,
        "Fiji": Z,
        "Finland": Z,
        "France": Z,
        "Gazimağusa": Z,
        "Georgia": Z,
        "Germany": Z,
        "Ghana": Z,
        "Gibraltar": Z,
        "Gilgit": Z,
        "Greece": Z,
        "Greenland": Z,
        "Grenada": Z,
        "Guadeloupe": Z,
        "Guam": Z,
        "Guatemala": Z,
        "Guernsey": Z,
        "Guinea": Z,
        "Guinea-Bissau": Z,
        "Guyana": Z,
        "Haiti": Z,
        "Honduras": Z,
        "Hong Kong": Z,
        "Hungary": Z,
        "Iceland": Z,
        "India": (STATE, {
            "Tamil Nadu": Z,
            "Bihar": Z,
            "Mumbai": Z,
            "West Bengal": Z,
            "Maharashtra": Z,
            "Jharkhand": Z,
            "Telangana": Z,
            "Madhya Pradesh": Z,
            "Karnataka": Z,
            "Haryana": Z,
            "Kerala": Z,
            "Punjab": Z,
            "Uttar Pradesh": Z,
            "Uttarakhand": Z,
            "Delhi": Z,
            "Chhattisgarh": Z,
            "Assam": Z,
            "Nagaland": Z,
            "Andhra Pradesh": Z,
            "Gujarat": Z,
            "Odisha": Z,
            "Rajasthan": Z,
            "Goa": Z,
            "Jammu & Kashmir": Z,
            "Himachal Pradesh": Z,
            "Chandigarh": Z,
            "Meghalaya": Z,
        }),
        "Indonesia": Z,
        "Iran": Z,
        "Iraq": Z,
        "Ireland": Z,
        "Isle of Man": Z,
        "Israel": Z,
        "Italy": Z,
        "Jamaica": Z,
        "Jammu and Kashmir": Z,
        "Japan": Z,
        "Jersey": Z,
        "Jordan": Z,
        "Kazakhstan": Z,
        "Kenya": Z,
        "Kiribati": Z,
        "Kosovo": Z,
        "Kuwait": Z,
        "Kyrenia": Z,
        "Kyrgyzstan": Z,
        "Latvia": Z,
        "Lebanon": Z,
        "Liberia": Z,
        "Libya": Z,
        "Liechtenstein": Z,
        "Lithuania": Z,
        "Luxembourg": Z,
        "Macedonia": Z,
        "Madagascar": Z,
        "Malawi": Z,
        "Malaysia": Z,
        "Maldives": Z,
        "Mali": Z,
        "Malta": Z,
        "Martinique": Z,
        "Mauritania": Z,
        "Mauritius": Z,
        "Mayotte": Z,
        "Mexico": Z,
        "Moldova": Z,
        "Mongolia": Z,
        "Montenegro": Z,
        "Morocco": Z,
        "Mozambique": Z,
        "Myanmar": Z,
        "Namibia": Z,
        "Nepal": Z,
        "Netherlands": Z,
        "New Caledonia": Z,
        "New Zealand": Z,
        "Nicaragua": Z,
        "Niger": Z,
        "Nigeria": Z,
        "Norfolk Island": Z,
        "North Macedonia": Z,
        "Norway": Z,
        "Pakistan": Z,
        "Palestine": Z,
        "Panama": Z,
        "Papua New Guinea": Z,
        "Paraguay": Z,
        "Peru": Z,
        "Philippines": Z,
        "Poland": Z,
        "Portugal": Z,
        "Puerto Rico": Z,
        "Qatar": Z,
        "Romania": Z,
        "Russia": Z,
        "Rwanda": Z,
        u"Réunion": Z,
        "San Marino": Z,
        "Senegal": Z,
        "Serbia": Z,
        "Seychelles": Z,
        "Sierra Leone": Z,
        "Singapore": Z,
        "Slovakia": Z,
        "Slovenia": Z,
        "Somalia": Z,
        "South Africa": Z,
        "South Korea": Z,
        "Spain": Z,
        "Sri Lanka": Z,
        "St Kitts & Nevis": Z,
        "St Vincent and the Grenadines": Z,
        "Sudan": Z,
        "Svalbard and Jan Mayen": Z,
        "Sweden": Z,
        "Switzerland": Z,
        "Syria": Z,
        "Taiwan": Z,
        "Tanzania": Z,
        "Thailand": Z,
        "The Bahamas": Z,
        "The Gambia": Z,
        "Togo": Z,
        "Tokelau": Z,
        "Trinidad and Tobago": Z,
        "Tunisia": Z,
        "Turkey": Z,
        "Turks and Caicos Islands": Z,
        "U.S. Virgin Islands": Z,
        "UK": Z,
        "USA": (STATE, {
            "AL-Alabama": Z,
            "AK-Alaska": Z,
            "AZ-Arizona": Z,
            "AR-Arkansas": Z,
            "CA-California": Z,
            "CO-Colorado": Z,
            "CT-Connecticut": Z,
            "DE-Delaware": Z,
            "FL-Florida": Z,
            "GA-Georgia": Z,
            "HI-Hawaii": Z,
            "ID-Idaho": Z,
            "IL-Illinois": Z,
            "IN-Indiana": Z,
            "IA-Iowa": Z,
            "KS-Kansas": Z,
            "KY-Kentucky": Z,
            "LA-Louisiana": Z,
            "ME-Maine": Z,
            "MD-Maryland": Z,
            "MA-Massachusetts": Z,
            "MI-Michigan": Z,
            "MN-Minnesota": Z,
            "MS-Mississippi": Z,
            "MO-Missouri": Z,
            "MT-Montana": Z,
            "NE-Nebraska": Z,
            "NV-Nevada": Z,
            "NH-New Hampshire": Z,
            "NJ-New Jersey": Z,
            "NM-New Mexico": Z,
            "NY-New York": Z,
            "NC-North Carolina": Z,
            "ND-North Dakota": Z,
            "OH-Ohio": Z,
            "OK-Oklahoma": Z,
            "OR-Oregon": Z,
            "PA-Pennsylvania": Z,
            "RI-Rhode Island": Z,
            "SC-South Carolina": Z,
            "SD-South Dakota": Z,
            "TN-Tennessee": Z,
            "TX-Texas": Z,
            "UT-Utah": Z,
            "VT-Vermont": Z,
            "VA-Virginia": Z,
            "WA-Washington": Z,
            "DC-District of Columbia": Z,
            "WV-West Virginia": Z,
            "WI-Wisconsin": Z,
            "WY-Wyoming": Z,
        }),
        "Uganda": Z,
        "Ukraine": Z,
        "United Arab Emirates": Z,
        "Uruguay": Z,
        "Uzbekistan": Z,
        "Vanuatu": Z,
        "Venezuela": Z,
        "Vietnam": Z,
        "Yemen": Z,
        "Zambia": Z,
        "Zimbabwe": Z,
        "Åland Islands": Z,
    })}
