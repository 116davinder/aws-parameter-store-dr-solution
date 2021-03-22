# aws-parameter-store-dr-solution

**Notes***
1. This application won't handle Credentials of AWS.
   You must check aws or boto3 guide for it.
2. This application won't create s3 bucket, it assumes you have it will right bucket policies.
3. This application won't encrypt any data. It assumes you have enabled AWS S3 Server Side Encryption.
4. S3 Bucket Prefix should be unique because application assumes backup files that ends with `.json`
will be stored only.
5. PEP8 Rules are not followed by me.

## Backup Solution
It will take backup of given SSM Path and its sub-path into given s3 bucket.
It will also create a temporary file to store all key-value pairs, example `/tmp/2021-03-22.json`
and Once upload to S3 is complete it will be removed.

**Usage**
```bash
python3 backup.py 'ssm-path' 'aws-region' 's3-bucket' 's3-bucket-prefix'
```
**Example**
```bash
python3 backup.py '/Test' 'us-east-1' 'test-davinder-s3' 'SSM/'
```
**Output**
```bash
python3 backup.py /Test us-east-1 test-davinder-s3 SSM/
{"@timestamp": "2021-03-22 19:35:01,348","level": "INFO","thread": "MainThread","name": "root","message": "SSM Parameter Path: /Test and its sub paths"}
{"@timestamp": "2021-03-22 19:35:01,360","level": "INFO","thread": "MainThread","name": "botocore.credentials","message": "Found credentials in environment variables."}
{"@timestamp": "2021-03-22 19:35:05,339","level": "INFO","thread": "MainThread","name": "root","message": "upload successful at s3://test-davinder-s3/SSM/21-03-22.json"}
```

## Restore Solution
It will take a backup file from S3 and restore it of given SSM Path Prefix.
It will download the latest backup file from S3 Bucket with Given S3 Prefix location
and ends with `.json`.
It will also create a temporary file to store all key-value pairs, example `/tmp/ssm.json`
and Once restored to SSM is complete it will be removed.

**Usage**
```bash
python3 restore.py 'ssm-path' 'aws-region' 's3-bucket' 's3-bucket-prefix'
```
**Example**
```bash
python3 restore.py '/Test' 'us-east-1' 'test-davinder-s3' 'SSM/'
```

**Output**
```bash
python3 backup.py '/Test' 'us-east-1' 'test-davinder-s3' 'SSM/'
.....
```