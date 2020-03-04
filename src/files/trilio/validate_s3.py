#!/usr/bin/python

import os
import boto3
import botocore
import argparse
from urllib.parse import urlparse


def validate_s3_credentials(s3_access_key_id, s3_secret_access_key,
                            s3_endpoint, s3_region, s3_bucket,
                            use_ssl, s3_signature_version):
    """ Validate the S3 credentials.

    Validate all of the S3 credentials by attempting to get
    some bucket information.

    Returns:
        Success will be returned otherwise error 403, 404, or
        500 will be retured with any relevent information.
    """

    s3_config_object = None
    if s3_signature_version != 'default' and s3_signature_version != '':
        s3_config_object = botocore.client.Config(
            signature_version=s3_signature_version)

    s3_client = boto3.client('s3',
                             region_name=s3_region,
                             use_ssl=use_ssl,
                             aws_access_key_id=s3_access_key_id,
                             aws_secret_access_key=s3_secret_access_key,
                             endpoint_url=s3_endpoint,
                             config=s3_config_object)

    s3_client.head_bucket(Bucket=s3_bucket)

    # Add a check to see if the current object store will support
    # our path length.
    long_key = os.path.join(
        'tvault_config/',
        'workload_f5190be6-7f80-4856-8c24-149cb40500c5/',
        'snapshot_f2e5c6a7-3c21-4b7f-969c-915bb408c64f/',
        'vm_id_e81d1ac8-b49a-4ccf-9d92-5f1ef358f1be/',
        'vm_res_id_72477d99-c475-4a5d-90ae-2560f5f3b319_vda/',
        'deac2b8a-dca9-4415-adc1-f3c6598204ed-segments/',
        '0000000000000000.00000000')
    s3_client.put_object(
        Bucket=s3_bucket, Key=long_key, Body='Test Data')

    s3_client.delete_object(Bucket=s3_bucket, Key=long_key)

    return {'status': 'Success'}


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--access-key', required=True)
    parser.add_argument('-s', '--secret-key', required=True)
    parser.add_argument('-e', '--endpoint-url', default=None)
    parser.add_argument('-b', '--bucket-name', required=True)
    parser.add_argument('-r', '--region-name', default='us-east-2')
    parser.add_argument('-v', '--signature-version', default='default')
    args = parser.parse_args()

    s3_access_key_id = args.access_key
    s3_secret_access_key = args.secret_key
    s3_endpoint = args.endpoint_url if args.endpoint_url else None
    use_ssl = True if (s3_endpoint and
                       urlparse(s3_endpoint).scheme == 'https') else False
    s3_region = args.region_name if args.region_name else None
    s3_bucket = args.bucket_name
    s3_signature_version = args.signature_version

    try:
        validate_s3_credentials(s3_access_key_id, s3_secret_access_key,
                                s3_endpoint, s3_region, s3_bucket,
                                use_ssl, s3_signature_version)
    except Exception:
        raise


main()
