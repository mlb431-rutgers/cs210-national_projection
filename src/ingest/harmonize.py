from __future__ import annotations

STATE_FIPS_TO_CODE = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO",
    "09": "CT", "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI",
    "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
    "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
    "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
    "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
    "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
    "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
    "54": "WV", "55": "WI", "56": "WY",
}

CENSUS_B03002 = {
    "total": "B03002_001E",
    "non_hisp_total": "B03002_002E",
    "non_hisp_white": "B03002_003E",
    "non_hisp_black": "B03002_004E",
    "non_hisp_asian": "B03002_006E",
    "hisp_total": "B03002_012E",
    "hisp_white": "B03002_013E",
    "hisp_black": "B03002_014E",
    "hisp_asian": "B03002_016E",
}


def census_to_race_origin_shares(row: dict) -> dict[tuple[str, str], float]:
    total = float(row[CENSUS_B03002["total"]]) or 1.0

    nh_total = float(row[CENSUS_B03002["non_hisp_total"]])
    nh_white = float(row[CENSUS_B03002["non_hisp_white"]])
    nh_black = float(row[CENSUS_B03002["non_hisp_black"]])
    nh_asian = float(row[CENSUS_B03002["non_hisp_asian"]])
    nh_other = max(0.0, nh_total - nh_white - nh_black - nh_asian)

    h_total = float(row[CENSUS_B03002["hisp_total"]])
    h_white = float(row[CENSUS_B03002["hisp_white"]])
    h_black = float(row[CENSUS_B03002["hisp_black"]])
    h_asian = float(row[CENSUS_B03002["hisp_asian"]])
    h_other = max(0.0, h_total - h_white - h_black - h_asian)

    return {
        ("white", "non-hisp"): nh_white / total,
        ("black", "non-hisp"): nh_black / total,
        ("asian", "non-hisp"): nh_asian / total,
        ("other", "non-hisp"): nh_other / total,
        ("white", "hisp"): h_white / total,
        ("black", "hisp"): h_black / total,
        ("asian", "hisp"): h_asian / total,
        ("other", "hisp"): h_other / total,
    }
