# -*- coding: utf8 -*-

import os
import logging
from datadog import initialize, api
import urllib3
import json
from datetime import datetime, timedelta, timezone
import time
import re
import boto3
from base64 import b64decode
from retry import retry

logger = logging.getLogger()
logger.setLevel(logging.INFO)
urllib3.disable_warnings()

encrypted_datadog_api_key = os.environ['DatadogApiKey']
encrypted_datadog_app_key = os.environ['DatadogApplicationKey']
downtimes = None
infrastructure = None

datadog_api_key = boto3.client('kms').decrypt(CiphertextBlob=b64decode(encrypted_datadog_api_key), EncryptionContext={ 'proc': 'cw-event-to-dd-downtime' })['Plaintext'].decode('utf-8')
datadog_app_key = boto3.client('kms').decrypt(CiphertextBlob=b64decode(encrypted_datadog_app_key), EncryptionContext={ 'proc': 'cw-event-to-dd-downtime' })['Plaintext'].decode('utf-8')
regexp = re.compile(" |\[|\]|'")
message_prefix = "# cw-event-to-dd-downtime:\n"

def datadog_initialize(convert_host):
  # Monitors
  options = {
    'api_key': datadog_api_key,
    'app_key': datadog_app_key
  }
  initialize(**options)
  global downtimes
  downtimes = api.Downtime.get_all()

  # Infrastructure
  if convert_host:
    global infrastructure
    url = 'https://app.datadoghq.com/reports/v2/overview'
    http = urllib3.PoolManager()
    options = {
      'api_key': datadog_api_key,
      'application_key': datadog_app_key
    }
    r = http.request('GET', url, fields=options)
    infrastructure = json.loads(r.data.decode('UTF-8'))

def search_aws_id(host_before):
  host_after = None
  for row in infrastructure['rows']:
    if 'aws_id' in row and row['aws_id'] == host_before:
      host_after = row['host_name']
  return(host_after)

@retry(tries=3, delay=2, backoff=2)
def set_downtime(cancel, scope, start_ts, end_ts, message, downtime_tz, skip_sec):
  scope_list = regexp.sub("", scope).split(",")
  scope_list.sort()
  result_ids = []
  skip_ids = []

  for d in downtimes:
    if not d['disabled'] and d['active'] and d['recurrence'] == None:
      if d['scope'] == scope_list and message_prefix in d['message']:
        if cancel:
          result = api.Downtime.delete(d['id'])
          result_ids.append(d['id'])
        else:
          end_diff = int(end_ts) - int(d['end'])
          logger.info("end_ts diff = " + str(end_diff) + " sec")
          if end_diff > skip_sec:
            result = api.Downtime.update(id=d['id'], scope=scope_list, end=end_ts, message=message, timezone=downtime_tz)
            result_ids.append(result['id'])
            time.sleep(1)
          else:
            skip_ids.append(d['id'])

  if len(result_ids) == 0 and len(skip_ids) == 0:
    if cancel:
      return("canceled target not found")
    else:
      result = api.Downtime.create(scope=scope_list, end=end_ts, message=message, timezone=downtime_tz)
      time.sleep(1)
      return("created " + str(result['id']))
  else:
    if cancel:
      return("canceled " + ",".join(map(str, result_ids)))
    else:
      return("updated " + ",".join(map(str, result_ids)) + " / skipped " + ",".join(map(str, skip_ids)))

def lambda_handler(event, context):
  # Convert for Input Transformer strings
  if type(event) == str:
    event = json.loads(event)

  # Set parameters
  rundate = datetime.utcnow()
  cancel = event['Cancel'] if 'Cancel' in event and event['Cancel'] else False
  convert_host = event['ConvertHost'] if 'ConvertHost' in event and not event['ConvertHost'] else False
  downtime_tz = event['DownTimeTZ'] if 'DownTimeTZ' in event else os.environ['DownTimeTZ']
  time_range_minutes = event['TimeRangeMinutes'] if 'TimeRangeMinutes' in event else int(os.environ['TimeRangeMinutes'])
  skip_minites = event['SkipMinutes'] if 'SkipMinutes' in event else int(os.environ['SkipMinutes'])
  skip_sec = skip_minites * 60
  message = message_prefix + str(event['Message']) if 'Message' in event else message_prefix
  logger.info("Parameters: { cancel:" + str(cancel) + ", convert_host:" + str(convert_host) + ", downtime_tz:" + str(downtime_tz) + ", time_range_minutes:" + str(time_range_minutes) + ", skip_sec:" + str(skip_sec) + ", message:" + str(message) + '}')

  # Set TimeRange
  start_ts = rundate.strftime('%s')
  end_ts = (rundate + timedelta(minutes=time_range_minutes)).strftime('%s')
  logger.info("From: " + str(start_ts) + " - To: " + str(end_ts))

  # Datadog Initialize
  datadog_initialize(convert_host)

  for scope in event['Scopes']:
    logger.info("scope: " + str(scope))
    # Convert Host
    if convert_host:
      scope_list = regexp.sub("", scope).split(",")
      for scope_value in scope_list:
        if scope_value.startswith("host:"):
          host_before = scope_value.replace(" ", "").replace("host:", "")
          host_after = search_aws_id(host_before)
          if host_after != None:
            scope = scope.replace("'host:" + host_before + "'", "'host:" + host_after + "'")
            logger.info("scope(convert): " + str(scope))
    # Set Downtime
    result = set_downtime(cancel, scope, start_ts, end_ts, message, downtime_tz, skip_sec)
    logger.info(result)
