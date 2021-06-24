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
and Once upload to S3 is complete it will be auto cleaned up.

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
* It will take last backup file from S3 and restore it of given SSM Path Prefix.
* It will download the latest backup file from S3 Bucket with Given S3 Prefix location
and assumes backup files starts with `SSM_BACKUP_` and ends with `.json`.
* It will also create a temporary file to store all key-value pairs, example `/tmp/ssm_restore_xxxx.json`
and Once restored to SSM is complete it will be removed.

### Note*
If you want to restore on same path then `ssm-restore-path` should be empty.

**Usage**
```bash
python3 restore.py 'ssm-restore-path' 'ssm-aws-region' 's3-bucket' 's3-bucket-prefix'
```

### Examples
**Example 1**
```bash
python3 restore.py '' 'eu-central-1' 'test-davinder-s3' 'SSM/'
```

**Output 1**
```bash
python3 restore.py '' 'eu-central-1' 'test-davinder-s3' 'SSM/'
{"@timestamp": "2021-06-24 11:03:10,018","level": "INFO","thread": "MainThread","name": "botocore.credentials","message": "Found credentials in environment variables."}
{"@timestamp": "2021-06-24 11:03:11,269","level": "INFO","thread": "MainThread","name": "root","message": "Selected Backup File: SSM/SSM_BACKUP_2021-06-24.json"}
{"@timestamp": "2021-06-24 11:19:15,791","level": "INFO","thread": "MainThread","name": "root","message": "restoring ssm key-pair /Test/ANSIBLE_VAULT_PASSWORD at /Test/ANSIBLE_VAULT_PASSWORD"}
{"@timestamp": "2021-06-24 11:19:16,729","level": "INFO","thread": "MainThread","name": "root","message": "restoring ssm key-pair /Test1/ANSIBLE_VAULT_PASSWORD at /Test1/ANSIBLE_VAULT_PASSWORD"}
{"@timestamp": "2021-06-24 11:19:16,974","level": "INFO","thread": "MainThread","name": "root","message": "cleaned up temp files"}
```

**Example 2**
```bash
python3 restore.py '/DAV' 'eu-central-1' 'test-davinder-s3' 'SSM/'
```

**Output 2**
```bash
python3 restore.py '' 'eu-central-1' 'test-davinder-s3' 'SSM/'
{"@timestamp": "2021-06-24 11:03:10,018","level": "INFO","thread": "MainThread","name": "botocore.credentials","message": "Found credentials in environment variables."}
{"@timestamp": "2021-06-24 11:03:11,269","level": "INFO","thread": "MainThread","name": "root","message": "Selected Backup File: SSM/SSM_BACKUP_2021-06-24.json"}
{"@timestamp": "2021-06-24 11:19:15,791","level": "INFO","thread": "MainThread","name": "root","message": "restoring ssm key-pair /Test/ANSIBLE_VAULT_PASSWORD at /DAV/Test/ANSIBLE_VAULT_PASSWORD"}
{"@timestamp": "2021-06-24 11:19:16,729","level": "INFO","thread": "MainThread","name": "root","message": "restoring ssm key-pair /Test1/ANSIBLE_VAULT_PASSWORD at /DAV/Test1/ANSIBLE_VAULT_PASSWORD"}
{"@timestamp": "2021-06-24 11:19:16,974","level": "INFO","thread": "MainThread","name": "root","message": "cleaned up temp files"}
```