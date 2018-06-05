#!/usr/bin/python
import argparse
import datetime
import json
import os
import socket
import signal
import logging
import subprocess

import boto
from boto.s3.connection import OrdinaryCallingFormat
from boto.s3.key import Key

#
##
### Script params

AWS_ID = ""
AWS_KEY = ""

LOG_DIR = "/var/log/nginx"
UPLOAD_DIR = os.path.join(LOG_DIR, 'upload')
PID_FILE = '/var/run/nginx.pid'
FORCE_RELOAD = False


#
##
### script log config
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler('/var/log/lb_rotate.log')
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)


def date_to_dict(datestring):
    date_dict = {}
    date_dict['year'] = datestring[0:4]
    date_dict['month'] = datestring[4:6]
    date_dict['day'] = datestring[6:8]
    date_dict['hour'] = datestring[8:10]
    return date_dict


def gzip_to_s3upload(filename):
    if filename.endswith('.gz'):
        logger.warn('Reprocessing already zipped file')
        return filename

    destname = filename + '.gz'
    if not os.path.isfile(destname):
        logging.info('Zipping %s into %s', filename, destname)
        with open(destname, 'wxb') as f:
            subprocess.check_call(['gzip', '--stdout', '--fast', filename], stdout=f)
        os.remove(filename)
        return destname
    else:
        logging.warn('File %s already exists', destname)
    return destname


def upload_file_to_s3(bucket_name, filename):
    orig_file_key = os.path.basename(filename)
    # app, env, logtype, logdate = orig_file_key.split('.')[0].split('_') # actually only logdate needed
    logdate = orig_file_key.split('.')[0].split('_')[-1]
    date_dict = date_to_dict(logdate)
    final_s3_key = '{}/{}/{}/{}_{}'.format(date_dict['year'], date_dict['month'], date_dict['day'],
                                           socket.gethostname(), orig_file_key)

    try:
        conn = boto.connect_s3(AWS_ID, AWS_KEY, is_secure=True, calling_format=OrdinaryCallingFormat(), )
        bucket = conn.get_bucket(bucket_name)
        k = Key(bucket)
        k.key = final_s3_key
        k.set_contents_from_filename(os.path.join(UPLOAD_DIR, filename))
    except Exception as e:
        logger.error(e)
    os.remove(os.path.join(UPLOAD_DIR, filename))


def get_upload_file_dict():
    file_dict = {}
    for logfile_name in os.listdir(UPLOAD_DIR):
        if os.path.isdir(os.path.join(UPLOAD_DIR, logfile_name)):
            full_dir_path = os.path.join(UPLOAD_DIR, logfile_name)
            for gname in os.listdir(full_dir_path):
                full_file_path = os.path.join(full_dir_path, gname)
                gzipped_fname = gzip_to_s3upload(full_file_path)
                file_dict[logfile_name] = gzipped_fname
        else:
            logger.warning('File without category : {}'.format(logfile_name))
    return file_dict


def reload_nginx():
    if not os.path.exists(PID_FILE):
        logger.error('No Nginx pid file at{}'.format(PID_FILE))
        exit(1)
        return
    with open(PID_FILE, 'r') as fileobj:
        pid = int(fileobj.read())
    os.kill(pid, signal.SIGUSR1)
    logger.info('Nginx reloaded')


def rename_file(source_folder_root, dest_folder_root, basename, extension, ts):
    source_file = os.path.join(source_folder_root, basename + extension)
    dest_file = os.path.join(dest_folder_root, basename + '_' + ts + extension)
    if os.path.exists(source_file):
        logger.info('Moving {0} -> {1}'.format(source_file, dest_file))
        os.rename(source_file, dest_file)
    else:
        logger.info('File {0} does not exist'.format(source_file))


def rotate_logs(log_config):
    if os.path.exists(PID_FILE):
        ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        ext = '.log'
        source_folder_root = LOG_DIR
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        for env in log_config:
            for log_type in log_config[env]:
                dirname = log_config[env][log_type]['bucket_name']
                full_dir_name = os.path.join(UPLOAD_DIR, dirname)
                if not os.path.exists(full_dir_name):
                    os.makedirs(full_dir_name)
                rename_file(source_folder_root, full_dir_name, log_config[env][log_type]['logfile_name'], ext, ts)


def main():
    parser = argparse.ArgumentParser(description='Log rotation')
    parser.add_argument('--config', dest='config', type=str, required=True, help='Json config file')
    args = parser.parse_args()

    with open(args.config) as jsonfile:
        json_config = json.load(jsonfile)

    rotate_logs(json_config)
    reload_nginx()
    file_dict = get_upload_file_dict()
    for bucket, file_name in file_dict.items():
        logger.info('Uploading file : {}'.format(file_name))
        upload_file_to_s3(bucket, file_name)


if __name__ == '__main__':
    main()
