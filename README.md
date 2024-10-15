This repo contains multiple scripts that together complete the entire task of identifying needs to to change existing construction cards due to a new law.

The steps are as follows:

1. Upload pdfs to storage
   upload_to_bucket.py

2. Create Chunks
   create_chunks.py

3. Create sections from chunks
   chunks_to_sections.py

4. Run LLM on sections and create a text output per pdf
   main.py

# Dev setup

Developed with Python 3.10

1. Copy .env from the project you you want to run the scripts against to this directory. Naming follows the Microsoft example repo so a .env
   copied from thre should work out of the box.

```sh
cp ../project/.env .env
```

2. Create venv

```sh
python3 -m venv venv
```

3. Activate venv in the current shell

```sh
source venv/bin/activate
```

4. Initialize venv (repeat this step when adding new packages to requirement.in)

```sh
pip install pip-tools
```

5. Compile requirement.in into requirements.txt

```sh
pip-compile requirements.in
```

6. Install requirements.txt

```sh
pip install -r requirements.txt
```

7. (optional) Point your IDE to the venv
   VSC: Ctrl+Shift+P -> Python: Select Interpreter -> venv/bin/python

# Running scripts

1. Activate venv in the current shell

```sh
source venv/bin/activate
```

2. Run the script

Per project variables are set and loaded from the .env. Some per script variables are set as command line arguments. Such as which directory to upload into etc.

```sh
python create_chunks.py --from_dir ./data --to_dir ./chunks
```

# Document AI Infra

1. Set variables

```sh
export PROJECT_ID="rakennustieto"
export BUCKET_NAME="rakennustieto-bucket"
export SERVICE_ACCOUNT_NAME="document-ai-sa"
export LOCATION="eu"
export REGION="EUROPE-NORTH1"
export PROCESSOR_DISPLAY_NAME="Extract structure"
export PROCESSOR_TYPE="LAYOUT_PARSER_PROCESSOR"
export SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

```

2. Login and set project

```sh
gcloud auth application-default login
gcloud config set project $PROJECT_ID
gcloud auth application-default set-quota-project $PROJECT_ID
```

3. Enable services

```sh
gcloud services enable documentai.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable iam.googleapis.com
gcloud services enable cloudbilling.googleapis.com
```

4. Link billing account
   (This assumes you have 1 billing account and you want to use that for the project)

```sh
BILLING_ACCOUNT_ID=$(gcloud billing accounts list --format="value(ACCOUNT_ID)")
gcloud beta billing projects link $PROJECT_ID --billing-account=$BILLING_ACCOUNT_ID
```

5. Create service account and give it roles

```sh
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
 --display-name "Document AI Service Account"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
 --role="roles/documentai.apiUser"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
 --role="roles/storage.admin"
```

6. Create service account key file to local directory

```sh
gcloud iam service-accounts keys create ~/key.json \
 --iam-account $SERVICE_ACCOUNT_EMAIL

mv ~/key.json ./gcp-sa-key.json
```

7. Create Document AIprocessor

```sh
PROCESSOR_RESPONSE=$(curl -X POST  -H "Authorization: Bearer $(gcloud auth print-access-token)"   -H "Content-Type: application/json; charset=utf-8"   -d "{
    \"type\": \"${PROCESSOR_TYPE}\",
\"displayName\": \"${PROCESSOR_DISPLAY_NAME}\"
  }"   "https://${LOCATION}-documentai.googleapis.com/v1/projects/${PROJECT_ID}/locations/${LOCATION}/processors")
PROCESSOR_FULL_NAME=$(echo $PROCESSOR_RESPONSE | jq -r '.name')

```

8. Create bucket, make it uniform access and ensure it's not public

```sh
gsutil mb -l $REGION gs://${PROJECT_ID}-bucket/
gsutil uniformbucketlevelaccess set on gs://${PROJECT_ID}-bucket/
gsutil iam ch -d allUsers gs://${PROJECT_ID}-bucket/
```

9. Echo some variables to .env

```sh
echo "PROCESSOR_FULL_NAME=$PROCESSOR_FULL_NAME" >> .env
echo "BUCKET_NAME=$BUCKET_NAME" >> .env
echo "PROJECT_ID=$PROJECT_ID" >> .env
echo "LOCATION=$LOCATION" >> .env
```
