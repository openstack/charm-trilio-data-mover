# Overview

This charm provides the TrilioVault Data Mover Service which forms
part of the [TrilioVault Cloud Backup solution][trilio.io].

# Usage

TrilioVault Data Mover relies on services from nova-compute and rabbitmq-server.

Steps to deploy the charm:

    juju deploy trilio-data-mover --config user-config.yaml
    juju deploy nova-compute
    juju deploy rabbitmq-server
    juju add-relation trilio-data-mover:amqp rabbitmq-server:amqp
    juju add-relation trilio-data-mover:juju-info nova-compute:juju-info
    juju add-relation trilio-data-mover:shared-db percona-cluster:shared-db

# Configuration

Please provide below configuration options using a config file:

    python-version: "Openstack base python version(2 or 3)"

NOTE - Default value is set to "3". Please ensure to update this based on
python version since installing python3 packages on python2 based setup
might have unexpected impact.

    backup-target-type: nfs or s3

For NFS backup target:

    nfs-shares: NFS Shares IP address only for nfs backup target

For Amazon S3 backup target:

    tv-s3-secret-key: S3 secret access key

    tv-s3-access-key: S3 access key

    tv-s3-region-name: S3 region name

    tv-s3-bucket: S3 bucket name

For non-AWS S3 backup target:

    tv-s3-secret-key: S3 secret access key

    tv-s3-access-key: S3 access key

    tv-s3-endpoint-url: S3 endpoint URL

    tv-s3-region-name: S3 region name

    tv-s3-bucket: S3 bucket name

The configuration options need to be updated based on the S3 specific
requirements and the parameters that are not needed can be omitted.

TrilioVault Packages are downloaded from the repository added in
below config parameter. Please change this only if you wish to download
TrilioVault Packages from a different source.

    triliovault-pkg-source: Repository address of triliovault packages

# Bugs

Please report bugs on [Launchpad][lp-bugs-charm-trilio-data-mover].

[lp-bugs-charm-trilio-data-mover]: https://bugs.launchpad.net/charm-trilio-data-mover/+filebug
[trilio.io]: https://www.trilio.io/triliovault/openstack
