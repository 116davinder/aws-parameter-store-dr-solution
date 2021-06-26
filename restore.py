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
        self.restore_mode = restore_mode
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

    def _read_backup_temp_file(self):
        try:
            with open(self.temp_file.name, "r") as f:
                _line = f.readlines()
                if len(_line) > 0:
                    for _item in _line:
                        _item = json.loads(_item)
                        _path = self.ssm_path_prefix + _item['Name']
                        print("*" * 50)
                        print(f"Restoring ssm key-pair {_item['Name']} at {_path} in {self.ssm_region}")
                        if self.restore_mode != "auto":
                            print("Do you want to restore above mentioned key-pair?: yes/no")
                            user_selection = input()
                            if user_selection.lower() == "yes":
                                self._write_to_ssm(_path, _item["Value"], _item["Type"], _item["DataType"])
                            else:
                                pass
                        else:
                            self._write_to_ssm(_path, _item["Value"], _item["Type"], _item["DataType"])
                            pass
                else:
                    logging.warning("Nothing has found in selected backup file")

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

    def restore(self):
        _list = self._s3_find_backups()
        if len(_list) == 0:
            logging.error(
                f"no files are found under s3://{self.s3_bucket}/{self.s3_bucket_prefix}SSM_BACKUP_*.json pattern"
            )
            sys.exit(1)

        if self.restore_mode.lower() == "auto":
            logging.info("Auto Restore Mode is ON")
            restore_file = _list[-1]
        else:
            print("*" * 50)
            print("Manual Restore Mode is ON")
            print("*" * 50)
            restore_file = common.letUserPickBackupFile(_list)

        logging.info(f"Selected Backup File: {restore_file}")
        self._s3_download_selected_backup(restore_file)
        self._read_backup_temp_file()
        self.temp_file.close()
        logging.debug(f"cleaned up temp files")


if __name__ == "__main__":
    common.setLoggingFormat()
    if len(sys.argv) != 6:
        logging.error(
            "Usage: python3 restore.py 'ssm-path' 'aws-ssm-region' 's3-bucket' 's3-bucket-prefix' 'restore-mode'"
        )
    else:
        restore = SSMRestore(
            ssm_path_prefix=sys.argv[1],
            ssm_region=sys.argv[2],
            bucket=sys.argv[3],
            bucket_prefix=sys.argv[4],
            restore_mode=sys.argv[5]
        )
        restore.restore()
