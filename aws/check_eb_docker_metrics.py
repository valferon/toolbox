#!/usr/bin/env python
import json
import boto3
import requests


def init_session():
    s = boto3.session.Session()
    return s.resource('ec2')


def main():
    ec2 = init_session()
    for i in ec2.instances.all():
        if i.tags is None:
            continue
        for t in i.tags:
            if t['Key'] == 'Name':

                if t['Value'].startswith('[my host tag]'):
                    print(" {0} {1} ({2}) - [{3}] --> {4}".format(
                        i.id, t['Value'], i.instance_type, i.state['Name'], i.private_ip_address
                    ))
                    print(json.loads(requests.get('http://{}/metrics'.format(i.private_ip_address)).text))


if __name__ == '__main__':
    main()
