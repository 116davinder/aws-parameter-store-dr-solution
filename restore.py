#! /bin/python3
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Davinder Pal (@116davinder) <dpsangwal@gmail.com>

import boto3
import logging
from common import common
import sys
from botocore.config import Config
from botocore.exceptions import ClientError
import json
import tempfile


class SSMRestore:
    def __init__(self, ssm_path_prefix, ssm_region, bucket, bucket_prefix):
        self.ssm_region = ssm_region
        self.ssm_client_config = Config(
            region_name=self.ssm_region,
            retries={
                "max_attempts": 3,
            },
        )
        self.s3_bucket = bucket
        self.s3_bucket_prefix = bucket_prefix
        self.ssm_path_prefix = ssm_path_prefix
        self.temp_file = tempfile.NamedTemporaryFile(
            prefix="ssm_restore_", suffix=".json"
        )

    def _write_to_ssm(self):
        try:
            ssm_client = boto3.client("ssm", config=self.ssm_client_config)

            with open(self.temp_file.name, "r") as f:
                for item in f.readlines():
                    item = json.loads(item)

                    logging.info(
                        f"restoring ssm key-pair {item['Name']} at {self.ssm_path_prefix + item['Name']}"
                    )
                    ssm_client.put_parameter(
                        Name=self.ssm_path_prefix + item["Name"],
                        Description="Restored by AWS Parameter Store DR Automation",
                        Value=item["Value"],
                        Type=item["Type"],
                        Overwrite=True,
                        Tier="Intelligent-Tiering",
                        DataType=item["DataType"],
                    )

        except ClientError as e:
            logging.error(e)
            sys.exit(1)

    def _s3_download(self):
        _restore_files = []
        try:
            s3_client = boto3.client("s3")
            paginator = s3_client.get_paginator("list_objects_v2")
            operation_parameters = {
                "Bucket": self.s3_bucket,
                "Prefix": self.s3_bucket_prefix,
            }
            page_iterator = paginator.paginate(**operation_parameters)
            filtered_iterator = page_iterator.search(
                "Contents[?contains(Key, 'SSM_BACKUP_') && contains(Key, '.json')][]"
            )
            for key_data in filtered_iterator:
                if key_data is not None:
                    _restore_files.append(key_data["Key"])

            _restore_files.sort()
            if len(_restore_files) > 0:
                logging.info(f"Selected Backup File: {_restore_files[-1]}")
                s3_client.download_file(
                    self.s3_bucket, _restore_files[-1], self.temp_file.name
                )
                logging.debug(f"temporary file: {self.temp_file.name}")
            else:
                logging.error(
                    f"no files are found under s3://{self.s3_bucket}/{self.s3_bucket_prefix}SSM_BACKUP_*.json pattern"
                )
                sys.exit(1)
        except ClientError as e:
            logging.error(e)
            sys.exit(1)

    def restore(self):
        self._s3_download()
        self._write_to_ssm()
        self.temp_file.close()
        logging.info(f"cleaned up temp files")


if __name__ == "__main__":
    common.setLoggingFormat()
    if len(sys.argv) != 5:
        logging.error(
            "Usage: python3 restore.py 'ssm-path' 'aws-ssm-region' 's3-bucket' 's3-bucket-prefix'"
        )
    else:
        restore = SSMRestore(
            ssm_path_prefix=sys.argv[1],
            ssm_region=sys.argv[2],
            bucket=sys.argv[3],
            bucket_prefix=sys.argv[4],
        )
        restore.restore()
