# ARMIS Backend

This is the backend + frontend for the ARMIS project.
- Upload sensor data from Arduino via `/upload`
- Dashboard fetches `/data` and displays live values
- Chief Engine triggers **email alerts** if thresholds are crossed

## Deployment
- Hosted on Render
- Uses Flask + Gunicorn
- Secrets stored in Render environment variables
