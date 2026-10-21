# Screenshots still to capture

These are the views recruiters look for most. Take each one in the Azure portal, save it in
[`../screenshots`](../screenshots) with the file name below, and add it to the README section shown.
Before saving, make sure no subscription ID, key, SAS token, connection string or password is visible.

| File name | What to capture | README section |
|---|---|---|
| `02-adf-pipeline-canvas.png` | ADF Studio → Author → `pl_dynamic_git_to_raw`, with the ForEach opened so the Copy activity is visible | 1. Bronze |
| `02b-adf-run-succeeded.png` | ADF Studio → Monitor → Pipeline runs, showing a **Succeeded** run and the 10 copy activities | 1. Bronze |
| `02c-adls-raw-container.png` | Storage account `awvmac03` → Containers → `raw`, showing one folder per table | 1. Bronze |
| `05b-databricks-write-clean.png` | The last cell of `Clean_Layer` writing Parquet, plus the `clean` container showing the output folders | 2. Silver |
| `07-synapse-query-result.png` | `SELECT TOP 100 * FROM final.sales` with the result grid | 3. Gold |
| `08-synapse-external-table.png` | `SELECT TOP 100 * FROM final.extsales` and the `final/extsales` folder in storage | 3. Gold |
| `09-powerbi-report.png` | The Power BI report built on the `final` views | 4. Reporting |

## Exporting the real definitions (optional)

- **Data Factory:** ADF Studio → Manage → ARM template → **Export ARM template**, then replace the files in `adf/`.
- **Databricks:** open `Clean_Layer` → File → Export → **Source file**, then replace `databricks/Clean_Layer.py`.
- **Synapse:** each SQL script → `...` → **Export**, then replace the files in `synapse/`.

Check every exported file for secrets before committing it.
