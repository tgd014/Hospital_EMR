# Procedure catalog setup

The procedure picker searches CMS's FY 2027 ICD-10-PCS order file. It also allows a clinician to enter a custom procedure name; custom entries are saved without a catalog code.

Apply the database change and load the catalog from the Hospital_EMR project directory:

```powershell
python manage.py migrate
python manage.py import_icd10pcs "C:\Users\kundo\Downloads\zip-file-4-2027-icd-10-pcs-order-file-long-and-abbreviated-titles.zip"
```

The importer accepts the CMS ZIP directly or the extracted `icd10pcs_order_2027.txt` file. Re-importing refreshes catalog titles and active codes. Existing encounter records keep the title snapshot saved when the procedure was recorded.

ICD-10-PCS is a U.S. inpatient procedure classification. The catalog is a searchable reference; clinicians can enter procedures that are absent from it.

Sources:

- CMS ICD-10 files: https://www.cms.gov/medicare/coding-billing/icd-10-codes
- ONC terminology licensing summary: https://healthit.gov/resources/cartos-oncs-terminology-service/
