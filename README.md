# aws-parameter-store-dr-solution

**Notes***
1. This application won't handle Credentials of AWS.
   You must check aws or boto3 guide for it.
2. This application won't create s3 bucket, it assumes you have it will right bucket policies.
3. This application won't encrypt any data. It assumes you have enabled AWS S3 Server Side Encryption.
4. S3 Bucket Prefix should be unique because application assumes backup files starts with `SSM_BACKUP_` and ends with `.json`
will be stored only.
5. PEP8 Rules are not followed by me.
6. This Application won't take backup of SSM Parameter `description` and `tags`  currently.

## Backup Solution
* It will take backup of given comma separated SSM Paths only not there sub/child paths.
* It will also create a temporary file to store all key-value pairs, example `/tmp/ssm_backup_xxxx.json`
and Once upload to S3 is complete it will be auto cleaned.

**Usage**
```bash
python3 backup.py 'ssm-paths' 'ssm-aws-region' 's3-bucket' 's3-bucket-prefix'
```

### Examples

**Example**
```bash
python3 backup.py '/Test/ANSIBLE_VAULT_PASSWORD,/Test1/ANSIBLE_VAULT_PASSWORD' 'us-east-1' 'test-davinder-s3' 'SSM/'
```

**Output**
```bash
python3 backup.py '/Test/ANSIBLE_VAULT_PASSWORD,/Test1/ANSIBLE_VAULT_PASSWORD' 'us-east-1' 'test-davinder-s3' 'SSM/'
{"@timestamp": "2021-06-24 10:54:54,768","level": "INFO","thread": "MainThread","name": "botocore.credentials","message": "Found credentials in environment variables."}
{"@timestamp": "2021-06-24 10:54:54,787","level": "INFO","thread": "MainThread","name": "root","message": "pulling data from /Test/ANSIBLE_VAULT_PASSWORD"}
{"@timestamp": "2021-06-24 10:54:56,157","level": "INFO","thread": "MainThread","name": "root","message": "pulling data from /Test1/ANSIBLE_VAULT_PASSWORD"}
{"@timestamp": "2021-06-24 10:54:57,999","level": "INFO","thread": "MainThread","name": "root","message": "backup is parked in AWS S3 at s3://test-davinder-s3/SSM/SSM_BACKUP_2021-06-24.json"}
{"@timestamp": "2021-06-24 10:54:57,999","level": "INFO","thread": "MainThread","name": "root","message": "cleaned temp files"}
```

## Restore Solution
* It will creates a temporary file to store all key-value pairs, example `/tmp/ssm_restore_xxxx.json`
and Once restored to SSM is complete it will be cleaned.
* Restore Modes: `auto` / `manual`

**Auto**

It will download last backup file that starts with `SSM_BACKUP_` and ends with `.json` from given S3 bucket with given S3 prefix location then it will restore all the SSM key-pairs from selected backup on given `ssm-restore-path`.

**Manual**

It will fetch all of backup files that starts with `SSM_BACKUP_` and ends with `.json` from given S3 Bucket with given S3 prefix location and will ask user to select backup with option.

It will ask user to select which key-pair to restore from selected backup on given `ssm-restore-path`

### Note*
* If you want to restore on same path then `ssm-restore-path` should be empty like `''`.
* if backup file is empty then restore will fail with warning message `Nothing has found in selected backup file`.

**Usage**
```bash
python3 restore.py 'ssm-restore-path' 'ssm-aws-region' 's3-bucket' 's3-bucket-prefix' 'restore-mode'
```

### Examples
**Auto Mode Example 1**
```bash
python3 restore.py '' 'eu-west-2' 'test-davinder-s3' 'SSM/' 'auto'
{"@timestamp": "2021-06-26 16:55:00,004","level": "INFO","thread": "MainThread","name": "botocore.credentials","message": "Found credentials in environment variables."}
{"@timestamp": "2021-06-26 16:55:01,276","level": "INFO","thread": "MainThread","name": "root","message": "Auto Restore Mode is ON"}
{"@timestamp": "2021-06-26 16:55:01,277","level": "INFO","thread": "MainThread","name": "root","message": "Selected Backup File: SSM/SSM_BACKUP_2021-06-26.json"}
{"@timestamp": "2021-06-26 16:55:01,890","level": "INFO","thread": "MainThread","name": "root","message": "Restoring ssm key-pair /Test/ANSIBLE_VAULT_PASSWORD at /Test/ANSIBLE_VAULT_PASSWORD in eu-west-2"}
{"@timestamp": "2021-06-26 16:55:02,926","level": "INFO","thread": "MainThread","name": "root","message": "Restoring ssm key-pair /Test1/ANSIBLE_VAULT_PASSWORD at /Test1/ANSIBLE_VAULT_PASSWORD in eu-west-2"}
```
**Auto Mode Example 2**
```bash
python3 restore.py '/AUTO' 'eu-west-2' 'test-davinder-s3' 'SSM/' 'auto'
{"@timestamp": "2021-06-26 16:55:00,004","level": "INFO","thread": "MainThread","name": "botocore.credentials","message": "Found credentials in environment variables."}
{"@timestamp": "2021-06-26 16:55:01,276","level": "INFO","thread": "MainThread","name": "root","message": "Auto Restore Mode is ON"}
{"@timestamp": "2021-06-26 16:55:01,277","level": "INFO","thread": "MainThread","name": "root","message": "Selected Backup File: SSM/SSM_BACKUP_2021-06-26.json"}
{"@timestamp": "2021-06-26 16:55:01,890","level": "INFO","thread": "MainThread","name": "root","message": "Restoring ssm key-pair /Test/ANSIBLE_VAULT_PASSWORD at /AUTO/Test/ANSIBLE_VAULT_PASSWORD in eu-west-2"}
{"@timestamp": "2021-06-26 16:55:02,926","level": "INFO","thread": "MainThread","name": "root","message": "Restoring ssm key-pair /Test1/ANSIBLE_VAULT_PASSWORD at /AUTO/Test1/ANSIBLE_VAULT_PASSWORD in eu-west-2"}
```

**Manual Mode Example 1**
```bash
python3 restore.py '/MANUAL' 'eu-central-1' 'test-davinder-s3' 'SSM/' 'manual'
{"@timestamp": "2021-06-26 16:00:34,329","level": "INFO","thread": "MainThread","name": "botocore.credentials","message": "Found credentials in environment variables."}
**************************************************
Manual Restore Mode is ON
**************************************************
Please select:
1) SSM/SSM_BACKUP_2021-06-23.json
2) SSM/SSM_BACKUP_2021-06-24.json
3) SSM/SSM_BACKUP_2021-06-25.json
4) SSM/SSM_BACKUP_2021-06-26.json
Enter number: 3
{"@timestamp": "2021-06-26 16:00:42,408","level": "INFO","thread": "MainThread","name": "root","message": "Selected Backup File: SSM/SSM_BACKUP_2021-06-25.json"}
{"@timestamp": "2021-06-26 16:00:44,055","level": "WARNING","thread": "MainThread","name": "root","message": "Nothing has found in selected backup file"}
```

**Manual Mode Example 2**
```bash
python3 restore.py '/MANUAL' 'eu-central-1' 'test-davinder-s3' 'SSM/' 'manual'
{"@timestamp": "2021-06-26 16:57:02,788","level": "INFO","thread": "MainThread","name": "botocore.credentials","message": "Found credentials in environment variables."}
**************************************************
Manual Restore Mode is ON
**************************************************
Please select:
1) SSM/SSM_BACKUP_2021-06-23.json
2) SSM/SSM_BACKUP_2021-06-24.json
3) SSM/SSM_BACKUP_2021-06-25.json
4) SSM/SSM_BACKUP_2021-06-26.json
Enter number: 4
{"@timestamp": "2021-06-26 16:57:08,977","level": "INFO","thread": "MainThread","name": "root","message": "Selected Backup File: SSM/SSM_BACKUP_2021-06-26.json"}
**************************************************
List of key-pairs in selected backup file
**************************************************
Please select:
1) {"Name": "/Test/ANSIBLE_VAULT_PASSWORD", "Type": "SecureString", "Value": "xxxxxxxxxxx", "DataType": "text"}
2) {"Name": "/Test1/ANSIBLE_VAULT_PASSWORD", "Type": "SecureString", "Value": "yyyyyyyyyyy", "DataType": "text"}
Enter number: 2
{"@timestamp": "2021-06-26 16:57:16,354","level": "INFO","thread": "MainThread","name": "root","message": "Restoring ssm key-pair /Test1/ANSIBLE_VAULT_PASSWORD at /MANUAL/Test1/ANSIBLE_VAULT_PASSWORD in eu-west-2"}
```