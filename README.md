# cw-event-to-dd-downtime
CloudWatch event to set Datadog downtimes.

## Description

Schedule Downtime of Datadog by AWS CloudWatch Event.  
Supports Downtime in any time range and any scope.  
"forever" range is not supported.  

## Requirements

- [Apex – Serverless Infrastructure](http://apex.run/)

# Usage

## Download

```bash
git clone git@github.com:htnosm/cw-event-to-dd-downtime.git
cd cw-event-to-dd-downtime
```

### Python Environment Created with Virtualenv

- e.g.)

```bash
virtualenv -p python3 env
. ./env/bin/activate
```

## Create infrastructure

```bash
cp project.json.example project.json
# Initializing provider for terraform
apex infra init
# Create IAM Role and KMS Key
apex infra plan
apex infra apply
```

```bash
# Get role and kms_key_id from Outputs
apex infra output

# Input "iam_role_arn" to "role"
vi project.json

# Input "kms_key_arn" to "kms_arn"
cp functions/cw-event-to-dd-downtime/function.json.example functions/cw-event-to-dd-downtime/function.json
vi functions/cw-event-to-dd-downtime/function.json
```

## Set KMS key

```bash
# Get Encript DatadogApiKey and DatadogApplicationKey from Outputs
_KEY_ID="Your KMS Key"
_DD_API_KEY="Your Datadog API Key"
_DD_APP_KEY="Your Datadog Application Key"

for _TEXT in ${_DD_API_KEY} ${_DD_APP_KEY} ; do
  aws kms encrypt \
    --key-id "${_KEY_ID}" \
    --plaintext "${_TEXT}" \
    --encryption-context "proc=cw-event-to-dd-downtime" \
    --output text --query CiphertextBlob
done

# Input Encript DatadogApiKey and DatadogApplicationKey
vi functions/cw-event-to-dd-downtime/function.json
```

### check decript KMS

```bash
_ENCRYPTED_DD_API_KEY="Encript DatadogApiKey"
_ENCRYPTED_DD_APP_KEY="Encript DatadogApplicationKey"

for _TEXT in ${_ENCRYPTED_DD_API_KEY} ${_ENCRYPTED_DD_APP_KEY} ; do
  aws kms decrypt \
    --ciphertext-blob fileb://<(echo "${_TEXT}" | base64 --decode) \
    --encryption-context "proc=cw-event-to-dd-downtime" \
    --output text --query Plaintext \
    | base64 --decode ; echo ""
done
```

## Deploy

```bash
apex deploy cw-event-to-dd-downtime --dry-run
apex deploy cw-event-to-dd-downtime
```

### Test invoke function

```bash
# create / update(rerun)
apex invoke cw-event-to-dd-downtime < functions/cw-event-to-dd-downtime/event.json -L
# cancel
apex invoke cw-event-to-dd-downtime < functions/cw-event-to-dd-downtime/event_cancel.json -L
```

#### sample event json

- e.g.) Full Option

```json
{
  "Cancel": false,
  "ConvertHost": true,
  "DownTimeTZ": "Asia/Tokyo",
  "TimeRangeMinutes": 15,
  "SkipMinutes": 1,
  "Scopes": [
    "['host:i-xxxxxxxxxxxxxxxxx', 'scope:dev']",
    "['host:i-xxxxxxxxxxxxxxxxx', 'role:web']"
  ],
  "Message": " @slack-notify-channel "
}
```

## Parameters

| Key | Default | Allowed Value | Note |
| :--- | --- | --- | --- |
| Cancel | false | true / false | true is downtime cancel. |
| ConvertHost | false | true / false | true is convert instance-id to Datadog host name |
| DownTimeTZ | "UTC" | e.g.) "Asia/Tokyo" | Possible values for Datadog Downtime. |
| TimeRangeMinutes | 30 | integer | Schedule END value of Datadog Downtime. |
| SkipMinutes | 5 | integer | When the same scope downtime, less than the set minutes it will not be updated. |
| Scopes | ""(None) | "[ 'key1:value1',... ]", "[...]", ... | Required, scope array list of Datadog Downtime. |
| Message | ""(None) | string | message and notify of Datadog Downtime. |

# CloudWatch Events

- Configure input uses "Constant (JSON text)" or "Input Transformer"

## Add Rules

There is a sample under infrastracture.

```bash
cp infrastructure/aws_cloudwatch_event.tf.example infrastructure/aws_cloudwatch_event.tf

apex infra plan
apex infra apply
```

# Delete Resources

```bash
apex infra destroy
apex delete cw-event-to-dd-downtime
```
