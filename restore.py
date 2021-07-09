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
import argparse


class SSMRestore:
    def __init__(self, ssm_path_prefix, ssm_region, bucket, bucket_prefix, restore_mode):
        self.ssm_region = ssm_region
        self.ssm_client_config = Config(
            region_name=self.ssm_region,
            retries={
                "max_attempts": 3,
            },
        )
        self.ssm_client = boto3.client("ssm", config=self.ssm_client_config)
        self.s3_bucket = bucket
        self.s3_bucket_prefix = bucket_prefix
        self.ssm_path_prefix = ssm_path_prefix
        self.temp_file = tempfile.NamedTemporaryFile(
            prefix="ssm_restore_", suffix=".json"
        )
        self.restore_mode = restore_mode.lower()
        self.s3_client = boto3.client("s3")

    def _s3_find_backups(self):
        _restore_files = []
        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
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
                    logging.debug(key_data["Key"])
                    _restore_files.append(key_data["Key"])

            _restore_files.sort()
            logging.debug(f"list of backup files found: {_restore_files}")
            return _restore_files

        except ClientError as e:
            logging.error(e)
            sys.exit(1)

    def _s3_download_selected_backup(self, file_name):
        try:
            self.s3_client.download_file(
                self.s3_bucket, file_name, self.temp_file.name
            )
            logging.debug(f"temporary backup file: {self.temp_file.name}")
        except ClientError as e:
            logging.error(e)
            sys.exit(1)

    def _write_to_ssm(self, _path, _value, _type, _data_type):
        try:
            self.ssm_client.put_parameter(
                Name=_path,
                Description="Restored by AWS Parameter Store DR Automation",
                Value=_value,
                Type=_type,
                Overwrite=True,
                Tier="Intelligent-Tiering",
                DataType=_data_type
            )
        except ClientError as e:
            logging.error(e)
            sys.exit(1)

    def _read_backup_temp_file(self):
        with open(self.temp_file.name, "r") as f:
            _lines = f.readlines()
            if len(_lines) > 0:
                if self.restore_mode != 'auto':
                    print("*" * 50)
                    print("List of key-pairs in selected backup file")
                    print("*" * 50)
                    restore_key = common.letUserPickBackupFile(_lines)
                    if restore_key is not None:
                        restore_key = json.loads(restore_key)
                        _path = self.ssm_path_prefix + restore_key['Name']
                        logging.info(f"Restoring ssm key-pair {restore_key['Name']} at {_path} in {self.ssm_region}")
                        self._write_to_ssm(
                            self.ssm_path_prefix + restore_key['Name'],
                            restore_key["Value"],
                            restore_key["Type"],
                            restore_key["DataType"]
                        )
                    else:
                        logging.error("unknown selection")
                else:
                    for _item in _lines:
                        _item = json.loads(_item)
                        _path = self.ssm_path_prefix + _item['Name']
                        logging.info(f"Restoring ssm key-pair {_item['Name']} at {_path} in {self.ssm_region}")
                        self._write_to_ssm(_path, _item["Value"], _item["Type"], _item["DataType"])
            else:
                logging.warning("Nothing has found in selected backup file")

    def restore(self):
        _list = self._s3_find_backups()
        if len(_list) == 0:
            logging.error(
                f"no files are found under s3://{self.s3_bucket}/{self.s3_bucket_prefix}SSM_BACKUP_*.json pattern"
            )
            sys.exit(1)

        if self.restore_mode == "auto":
            logging.info("Auto Restore Mode is ON")
            restore_file = _list[-1]
        else:
            print("*" * 50)
            print("Manual Restore Mode is ON")
            print("*" * 50)
            restore_file = common.letUserPickBackupFile(_list)

        if restore_file is not None:
            logging.info(f"Selected Backup File: {restore_file}")
            self._s3_download_selected_backup(restore_file)
            self._read_backup_temp_file()
        else:
            logging.error("unknown selection")
        self.temp_file.close()
        logging.debug(f"cleaned up temp files")


if __name__ == "__main__":
    common.setLoggingFormat()

    parser = argparse.ArgumentParser(description='AWS Parameter Store Restore Script Options')
    parser.add_argument(
        "--ssm-restore-path-prefix",
        "--sp",
        nargs=1,
        required=True,
        type=str,
        help="Provide ssm path with space separated"
             " Example: --ssm-restore-path-prefix /AUTO"
    )
    parser.add_argument(
        "--region",
        nargs=1,
        required=True,
        type=str,
        help="Provide ssm region to which backup should be restored."
             " Example: --region us-east-1"
    )
    parser.add_argument(
        "--bucket",
        nargs=1,
        required=True,
        type=str,
        help="Provide name of the aws s3 bucket where backup is stored."
             " Example: --bucket test-davinder-s3"
    )
    parser.add_argument(
        "--bucket-prefix",
        nargs=1,
        type=str,
        required=True,
        help="(optional) Provide bucket prefix of the aws s3 bucket where backup is stored."
             " Example: --bucket-prefix SSM/"
    )
    parser.add_argument(
        "--restore-mode",
        nargs=1,
        type=str,
        required=True,
        help="Provide restore method."
             " Example: --restore-mode auto/manual"
    )
    args = parser.parse_args()

    restore = SSMRestore(
        ssm_path_prefix=args.ssm_restore_path_prefix[0].strip(),
        ssm_region=args.region[0].strip(),
        bucket=args.bucket[0].strip(),
        bucket_prefix=args.bucket_prefix[0].strip(),
        restore_mode=args.restore_mode[0].strip()
    )
    restore.restore()
