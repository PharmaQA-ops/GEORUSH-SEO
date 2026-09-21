# GEORUSH GA4 / GSC Connector Guide

## Google Analytics 4

GEORUSH includes a connector path for GA4.

Required: - GA4 property ID - Google service-account credentials -
Viewer or appropriate reporting access granted to the service account

Backend variables: `GA4_PROPERTY_ID` `GOOGLE_APPLICATION_CREDENTIALS`

After configuration: 1. Restart GEORUSH backend. 2. Open Analytics. 3.
Confirm `GA4 CONFIGURED`. 4. Click `Load GA4 Report`.

## Google Search Console

GSC is used for real query/ranking evidence. The application can work
from an approved GSC export and has a backend search-analytics path.

Do not label crawl-derived keyword themes as Google rankings.

## Data governance

Only connect company-owned properties and approved service accounts.
Store credentials outside the repository and rotate them according to
company policy.
