#! /bin/python3

import os
import boto3
import logging
from common import common
import sys
from botocore.config import Config
from botocore.exceptions import ClientError
import json
from datetime import date


class SSMBackup:
    def __init__(self, ssm_path_prefix=None, ssm_region=None, bucket=None, bucket_prefix=None):
        self.ssm_region = ssm_region
        self.ssm_client_config = Config(
            region_name=self.ssm_region,
            retries={
                'max_attempts': 3,
            }
        )
        self.s3_bucket = bucket
        self.s3_bucket_prefix = bucket_prefix
        self.ssm_path_prefix = ssm_path_prefix
        logging.info(f"SSM Parameter Path: {ssm_path_prefix} and its sub paths")

        self.temp_file = "/tmp/ssm.json"
        self.backup_file = self.s3_bucket_prefix + date.today().strftime("%y-%m-%d") + ".json"

    def _get_ssm_values(self):
        _results = []
        try:
            ssm_client = boto3.client('ssm', config=self.ssm_client_config)
        except ClientError as e:
            logging.error(e)
            sys.exit(1)

        try:
            if ssm_client.can_paginate('get_parameters_by_path'):
                paginator = ssm_client.get_paginator('get_parameters_by_path')
                page_iterator = paginator.paginate(
                    Path=self.ssm_path_prefix,
                    Recursive=True,
                    WithDecryption=True,
                    MaxResults=10,
                )

                for path in page_iterator:
                    _results += path['Parameters']
            else:
                logging.error("paginator creation failed")
                sys.exit(1)

        except ClientError as e:
            logging.error(f"unable to fetch ssm values: {e}")
            sys.exit(1)

        with open(self.temp_file, "w") as f:
            for item in _results:
                _dict = {
                    "Name": item['Name'],
                    "Type": item['Type'],
                    "Value": item['Value'],
                    "DataType": item['DataType']
                }
                f.write(json.dumps(_dict))
                f.write("\n")

    def upload_s3(self):

        self._get_ssm_values()

        try:
            s3_client = boto3.client('s3')
            s3_client.upload_file(self.temp_file,self.s3_bucket,self.backup_file)
            logging.info(f"upload successful at s3://{self.s3_bucket}/{self.backup_file}")
            os.remove(self.temp_file)
            logging.info("cleaned temp files.")
        except ClientError as e:
            logging.error(f"{self.backup_file} upload failed error {e}")


if __name__ == "__main__":
    common.setLoggingFormat()
    if len(sys.argv) != 5:
        logging.error("Usage: python3 backup.py 'ssm-path' 'aws-region' 's3-bucket' 's3-bucket-prefix'")
    else:
        backup = SSMBackup(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
        backup.upload_s3()
