# Overview

This charm provides the TrilioVault Data Mover Service which forms
part of the [TrilioVault Cloud Backup solution][trilio.io].

# Usage

The TrilioVault Data Mover relies on a database service, nova-compute service
and RabbitMQ messaging:

    juju deploy trilio-data-mover --config user-config.yaml
    juju deploy nova-compute
    juju deploy rabbitmq-server
    juju add-relation trilio-data-mover:amqp rabbitmq-server:amqp
    juju add-relation trilio-data-mover:juju-info nova-compute:juju-info
    juju add-relation trilio-data-mover:shared-db percona-cluster:shared-db

TrilioVault will also need to be deployed with other services in order to
provide a fully functional TrilioVault backup solution. Refer to the
[TrilioVault Data Protection][deployment-guide] section in the deployment
guide for more information.

# Storage Options

TrilioVault supports NFS and S3 backends for storing workload backups. The
storage type used by TrilioVault is determined by the value in the
`backup-target-type` charm config option.

## NFS

To configure the TrilioVault Data Mover to access backups in an NFS share,
set the `backup-target-type` option of the charm to `nfs` and set the `nfs-shares`
option of the charm to specify a valid NFS share.

    juju config trilio-data-mover backup-target-type=nfs
    juju config trilio-data-mover nfs-shares=10.40.3.20:/srv/triliovault

Mount settings for the NFS shares can be configured using the `nfs-options`
config option.

The TrilioVault Workload Manager application will also need to be configured to
use the same nfs-share.

## S3

To configure the TrilioVault Data Mover to access store backups in an S3 share,
set the `backup-target-type` option of the charm to `s3` and set the following
configuration options to provide information regarding the S3 service:

* `tv-s3-endpoint-url` the URL of the s3 storage (can be omitted if using AWS)
* `tv-s3-secret-key` the secret key for accessing the s3 storage
* `tv-s3-access-key` the access key for accessing the s3 storage
* `tv-s3-region-name` the region for accessing the s3 storage
* `tv-s3-bucket` the s3 bucket to use to storage backups in
* `tv-s3-ssl-cert` the SSL CA to use when connecting to the s3 service

    juju config trilio-data-mover tv-s3-endpoint-url=http://s3.example.com/
    juju config trilio-data-mover tv-s3-secret-key=superSecretKey
    juju config trilio-data-mover tv-s3-access-key=secretAccessKey
    juju config trilio-data-mover tv-s3-region-name=RegionOne
    juju config trilio-data-mover tv-s3-bucket=backups

The configuration options need to be updated based on the S3 specific
requirements and the parameters that are not needed can be omitted.

# TrilioVault Packages

TrilioVault Packages are downloaded from the repository added in
below config parameter. Please change this only if you wish to download
TrilioVault Packages from a different source.

    triliovault-pkg-source: Repository address of triliovault packages

# Bugs

Please report bugs on [Launchpad][lp-bugs-charm-trilio-data-mover].

[lp-bugs-charm-trilio-data-mover]: https://bugs.launchpad.net/charm-trilio-data-mover/+filebug
[trilio.io]: https://www.trilio.io/triliovault/openstack
[deployment-guide]: https://docs.openstack.org/project-deploy-guide/charm-deployment-guide/latest/app-trilio-vault.html
