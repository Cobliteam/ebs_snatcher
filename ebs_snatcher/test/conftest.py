from __future__ import unicode_literals

import string
import random

import pytest
import boto3
from botocore import UNSIGNED
from botocore.client import Config
from botocore.stub import Stubber


def boto3_stub(mocker, svc):
    client = boto3.client(svc, config=Config(signature_version=UNSIGNED),
                          region_name='us-east-1')
    mocker.patch('ebs_snatcher.ebs.' + svc, return_value=client)

    orig_get_waiter = type(client).get_waiter

    def get_waiter_no_delay(*args, **kwargs):
        waiter = orig_get_waiter(client, *args, **kwargs)
        waiter.config.delay = 0
        return waiter

    mocker.patch.object(client, 'get_waiter', wraps=get_waiter_no_delay)

    stub = Stubber(client)
    stub.activate()

    yield stub

    stub.deactivate()


@pytest.fixture
def ec2_stub(mocker):
    for stub in boto3_stub(mocker, 'ec2'):
        yield stub


@pytest.fixture
def sts_stub(mocker):
    for stub in boto3_stub(mocker, 'sts'):
        yield stub


@pytest.fixture
def instance_id():
    return 'i-11111111'


@pytest.fixture
def availability_zone():
    return 'us-east-1a'


@pytest.fixture
def instance_info(instance_id, availability_zone):
    return {
        'InstanceId': instance_id,
        'Placement': {'AvailabilityZone': availability_zone}
    }


@pytest.fixture
def gen_volume_id():
    def gen():
        return 'vol-' + ''.join(random.choice(string.digits) for _ in range(8))

    return gen


@pytest.fixture
def volume_id(gen_volume_id):
    return gen_volume_id()


@pytest.fixture
def attach_device():
    return '/dev/sdf'


@pytest.fixture
def attached_volume(volume_id, instance_id, attach_device):
    return {
        'VolumeId': volume_id,
        'Attachments': [{
            'Device': attach_device,
            'InstanceId': instance_id
        }]
    }


@pytest.fixture
def snapshot_id():
    return 'snap-11111111'


def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    elif isinstance(obj, (list, tuple)):
        return sorted(ordered(x) for x in obj)
    else:
        return obj
