#!/usr/bin/python
# -*- coding: utf-8 -*-


from psycopg2 import connect
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import argparse


def create_empty_database(db_host, db_user, db_pass, db_name):
    try:
        con = connect(user=db_user, host=db_host, password=db_pass, dbname='postgres')
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    except Exception as e:
        print(e)
        print("Unable to connect to the database.")

    cur = con.cursor()

    try:
        cur.execute('DROP DATABASE {}'.format(str(db_name)))
    except Exception as e:
        print("PRE RUN : test if database already exists : {}".format(e))
        pass

    try:
        cur.execute('CREATE DATABASE {}'.format(str(db_name)))
        cur.execute('SELECT datname FROM pg_database')
        dbs = cur.fetchall()
        print(dbs)
        print('####')
        for db in dbs:
            print("Database : {}".format(db))
        cur.close()
        con.close()
    except Exception as e:
        print(e)
        print("Error: ", sys.exc_info()[1])


def drop_database(db_host, db_user, db_pass, db_name):
    try:
        con = connect(user=db_user, host=db_host, password=db_pass, dbname='postgres')
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    except:
        print("Unable to connect to the database.")
        pass
    cur = con.cursor()
    try:
        cur.execute('DROP DATABASE {}'.format(str(db_name)))
    except Exception as e:
        print(e)

    try:
        cur.execute('SELECT datname FROM pg_database')
        dbs = cur.fetchall()
        print(dbs)
        print('####')
        for db in dbs:
            print("Database : {}".format(db))
        cur.close()
        con.close()
    except Exception as e:
        print(e)
        print("Error: ", sys.exc_info()[1])


def list_database(db_host, db_user, db_pass):
    try:
        con = connect(user=db_user, host=db_host, password=db_pass, dbname='postgres')
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    except Exception as e:
        print(e)
        print("Unable to connect to the database.")

    cur = con.cursor()
    try:
        cur.execute('SELECT datname FROM pg_database')
        dbs = cur.fetchall()
        print(dbs)
        print('####')
        for db in dbs:
            print("Database : {}".format(db))
        cur.close()
        con.close()
    except Exception as e:
        print(e)
        print("Error: ", sys.exc_info()[1])



def main(args):
    if args.action == 'list':
        list_database(args.db_host, args.db_user, args.db_password)
    elif args.action == 'create':
        create_empty_database(args.db_host, args.db_user, args.db_password, args.db_name)
    elif args.action == 'drop':
        drop_database(args.db_host, args.db_user, args.db_password, args.db_name)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='database_maintenance')
    parser.add_argument('--action', default='list', choices=["list", "create", "drop"],
                        help="database action to be performed")
    parser.add_argument('--db-host', help='dabatase host', required=True)
    parser.add_argument('--db-default-db', help='default admin database', default='postgres')
    parser.add_argument('--db-user', help="database user", required=True)
    parser.add_argument('--db-password', help="database password", required=True)
    parser.add_argument('--db-name', help="database name", default='test_db')

    args = parser.parse_args()
    args.db_name = "db_{}".format(args.db_name.replace("-", "_").replace(".", "_"))
    main(args)
