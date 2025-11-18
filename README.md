# 📊 Meta Ads Reporter (MAR)

Meta Ads Reporter is a command-line tool for retrieving, parsing, and exporting 
**Meta (Facebook/Instagram) Ads API insights** across multiple ad accounts with 
proper authentication, token validation, MAC extraction, pagination handling, 
and CSV/table output options.

**Version:** 0.1.0

**Author:** Joe Thompson (jopeymonster)

---

# 🚀 Features

### 🔐 Secure Authentication

* Uses **appsecret_proof** for server-side API requests
* Validates tokens through `/debug_token`
* Supports token caching to reduce API hits

### 📁 Flexible Account Selection

Choose between:

* `--all-accounts` — scan all active ad accounts associated with your token
* `--account-group <name>` — load grouped accounts from an external JSON file
* Supports arbitrary account files using `--accounts-file`

### 📊 Insights Retrieval

* Automatic pagination for large datasets
* Campaign-level metrics
* Normalizes results by:

  * account name
  * MAC (Marketing Attribution Code)
  * input date range and segmentation

### 📄 Output Options

* CSV export with timestamped or custom filenames
* Terminal table display (via `tabulate`)

### 🧩 Modular Architecture

* `auth.py` — Token and appsecret_proof management
* `meta_client.py` — Wrapped Graph API client
* `ads_report.py` — Reporting engine
* `accounts.py` — Account grouping and normalization
* `common.py` — Shared utilities, date handling, MAC extraction

---

# 📦 Installation

```bash
git clone https://github.com/jopeymonster/mar_proto.git
cd mar_proto
pip install -r requirements.txt
```

---

# ▶️ Running the Tool

You can run via script:

```bash
python main.py --config /path/to/auth_info.json --account-group sports-active-us --accounts-file /path/to/accounts_info.json
```

Or using module mode:

```bash
python -m mar_proto --config /path/to/auth_info.json --account-group sports-active-us
```

---

# 🔧 Required Files

### **1. auth_info.json**

```json
{
  "auth_dict": {
    "app_id": "YOUR_APP_ID",
    "app_secret": "YOUR_APP_SECRET",
    "access_token": "YOUR_LONG_LIVED_ACCESS_TOKEN",
    "appsecret_proof": null,
    "cache_path": null
  }
}
```

### **2. accounts_info.json**

```json
{
  "my-active-accounts": {
    "NIKE Ad Account": "123456789",
    "ACME Ad Account": "897654321"
  }
}
```

---

# ⌛ Date Range Options

The tool supports:

* Specific date
* Date range
* Segmentation by:

  * day
  * week
  * month
  * quarter
  * year

Input formats:

```
YYYY-MM-DD
YYYYMMDD
```

---

# 🔍 MAC (Marketing Attribution Code): A custom extension for deeper analysis.
  - Embed a custom identifier in your campaign naming convention:
    ```
    Campaign Name :marketing_attribution_code
    ```
    Examples:
    - `Nike Shoes - Holiday Sales :nikeholidaysales`
    - `Chicago - Legal - FRG :chi_frg_legal`
    - `GoogleAdsCampaign: MyCampaign :my_marketing_attribution_code`
  - Uses:
    - Audit UTM parameters against campaigns.
    - Link Ads activity with ERP or CRM systems.
    - Add a flexible reporting dimension for cross-channel analysis.
  - If no `:marketing_attribution_code` is present, the report will return `None`/blank.

Automatically derive Marketing Attribution Codes from `CampaignName`  
(takes the substring after the final colon). 

Detects MAC values based on:

* Colon format (`:mac`, `: mac`)
  
MACs are **not** added or modified in campaign names — only parsed and reported.

---

# 📁 Output Examples

### CSV sample

Saved to:

```
~/meta_report_2025-11-03_14-12-55.csv
```

### Table sample

```
+----------------+---------------------------+-------------+
| account_name   | campaign_name             | impressions |
+----------------+---------------------------+-------------+
| NIKE           | Black Friday Retargeting  |  102,394    |
```

---

# ⚡ License

MIT License — see [LICENSE](LICENSE).

---

# 💬 Support

For questions, bugs, or enhancements:
[https://github.com/jopeymonster/mar_proto/issues](https://github.com/jopeymonster/mar_proto/issues)

---

## 📄 Legal

The developers of this application are not responsible for any actions
performed using this tool. Your privacy is respected—see our
[Privacy Policy](https://jopeymonster.github.io/privacy/).