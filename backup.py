#! /bin/python3
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Davinder Pal (@116davinder) <dpsangwal@gmail.com>

import boto3
import logging
from common import common
import sys
import botocore.config
from botocore.exceptions import ClientError
import json
import tempfile
import pendulum
import argparse


class SSMBackup:
    def __init__(self, ssm_paths, ssm_region, bucket, bucket_prefix):
        self.ssm_region = ssm_region
        self.ssm_client_config = botocore.config.Config(
            region_name=self.ssm_region,
            retries={
                "max_attempts": 3,
            },
        )
        self.s3_bucket = bucket
        self.s3_bucket_prefix = bucket_prefix
        self.ssm_paths = ssm_paths
        self.temp_file = tempfile.NamedTemporaryFile(
            prefix="ssm_backup_", suffix=".json"
        )
        self.backup_file = self.s3_bucket_prefix + "SSM_BACKUP_" + pendulum.today().strftime("%Y-%m-%d") + ".json"

    def _get_ssm_values(self):
        _results = []
        try:
            ssm_client = boto3.client("ssm", config=self.ssm_client_config)
        except ClientError as e:
            logging.error(e)
            sys.exit(1)

        for _path in self.ssm_paths:
            try:
                logging.info(f"pulling data from {_path}")
                _output = ssm_client.get_parameter(
                    Name=_path,
                    WithDecryption=True,
                )
                _results.append(_output["Parameter"])
            except ssm_client.exceptions.ParameterNotFound as e:
                logging.error(f"No Path found {_path}: {e}")
            except ClientError as e:
                logging.info("Please blame yourself for this error or AWS")
                logging.error(e)
                sys.exit(1)

        if len(_results) > 0:
            with open(self.temp_file.name, "w") as f:
                for item in _results:
                    _dict = {
                        "Name": item["Name"],
                        "Type": item["Type"],
                        "Value": item["Value"],
                        "DataType": item["DataType"],
                    }
                    f.write(json.dumps(_dict))
                    f.write("\n")
                    logging.debug(f"storing copy of {item['Name']} in temporary file")
            logging.debug(f"temp backup file: {self.temp_file.name}")
        else:
            logging.error("I am not AI, please provide correct SSM Paths")
            sys.exit(1)

    def backup(self):
        self._get_ssm_values()
        try:
            s3_client = boto3.client("s3")
            s3_client.upload_file(self.temp_file.name, self.s3_bucket, self.backup_file)
            logging.info(
                f"backup is parked in AWS S3 at s3://{self.s3_bucket}/{self.backup_file}"
            )
            self.temp_file.close()
            logging.info("cleaned temp files")
        except ClientError as e:
            logging.info("Please blame yourself for this error or AWS")
            logging.error(e)


if __name__ == "__main__":
    common.setLoggingFormat()

    parser = argparse.ArgumentParser(description='AWS Parameter Store Backup Script Options')
    parser.add_argument(
        "--ssm-paths",
        nargs='+',
        required=True,
        type=str,
        help="Provide ssm path with space separated"
             " Example: --ssm-paths /Test/Path /Test1/Path"
    )
    parser.add_argument(
        "--region",
        nargs=1,
        required=True,
        type=str,
        help="Provide ssm region from where backup should be taken."
             " Example: --region us-east-1"
    )
    parser.add_argument(
        "--bucket",
        nargs=1,
        required=True,
        type=str,
        help="Provide name of the aws s3 bucket."
             " Example: --bucket test-davinder-s3"
    )
    parser.add_argument(
        "--bucket-prefix",
        nargs=1,
        type=str,
        required=True,
        help="Provide bucket prefix of the aws s3 bucket."
             " Example: --bucket-prefix SSM/"
    )
    args = parser.parse_args()

    backup = SSMBackup(
        ssm_paths=args.ssm_paths,
        ssm_region=args.region[0].strip(),
        bucket=args.bucket[0].strip(),
        bucket_prefix=args.bucket_prefix[0].strip(),
    )
    backup.backup()
