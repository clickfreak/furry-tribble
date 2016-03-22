#!/usr/bin/env python3

import requests
import logging
import os
import sys
import json
import yaml
import tempfile
import shutil
import argparse

logging.basicConfig(level=logging.DEBUG,
                        format=u'%(levelname)-8s [%(asctime)s]  %(message)s')
                        # format=u'%(funcName)-15s [%(lineno)-3d]# %(levelname)-8s [%(asctime)s]  %(message)s')
                        # format=u'%(pathname)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s')

class GrafanaTool(object):
    def __init__(self, apiurl, apikey):
        self.apiurl = apiurl
        self.apikey = apikey

        self.api_session = requests.Session()
        self.api_session.headers.update({"Authorization": "Bearer {}".format(self.apikey)})

    def do_backup(self, archivename='grafana-backup'):
        try:
            r = self.api_session.get(self.apiurl+"/datasources")
            datasources = r.json()
            # print(yaml.dump(datasources, indent=2, default_flow_style=False))
            # print(json.dumps(datasources, indent=2))

        except:
            logging.error("Can't get datasources list")
            return

        try:
            r = self.api_session.get(self.apiurl+"/search")
            dashboards_list = r.json()
            # print(json.dumps(dashboards_list, indent=2))
        except:
            logging.error("Can't get dashboards list")
            return

        tmpdirname = tempfile.TemporaryDirectory()
        dashboards_dir = tmpdirname.name+"/dashboards"
        os.makedirs(dashboards_dir, exist_ok=True)

        with open(tmpdirname.name+"/datasources.json", "w") as fp:
            json.dump(datasources, fp, indent=2)

        for dashboard in dashboards_list:
            try:
                r = self.api_session.get(self.apiurl+"/dashboards/{uri}".format(**dashboard))
                dashboard_ref = r.json()
                filename = dashboard_ref["meta"]["slug"]+".json"
                fp = open(dashboards_dir+"/"+filename, "w")
                r = json.dump(dashboard_ref, fp, indent=2)
                fp.close()
                logging.debug(dashboards_dir+"/"+filename)

            except:
                logging.error("Can't get dashboard '{title}' with id {id} ({uri})".format(**dashboard))
                tmpdirname.cleanup()
                raise

        shutil.make_archive(archivename, "gztar", root_dir=tmpdirname.name)
        tmpdirname.cleanup()

    def do_restore(self, archive_path='grafana-backup'):
        try:
            # Oh! python 3.4...
            file_list = os.listdir('{}/{}'.format(archive_path, "dashboards"))
            for file in file_list:
                if file.endswith('.json'):
                    dashboard_ref = json.load(open('{}/{}/{}'.format(archive_path, "dashboards", file)))
                    # dashboard_ref = dict()
                    # del dashboard_ref['dashboard']['id']
                    # print(dashboard_ref.keys())
                    # print(json.dumps(dashboard_ref, indent=2))
        except FileNotFoundError as e:
            logging.error("Something wrong with directory path {}".format(e.filename))



def main():
    params_parser = argparse.ArgumentParser(
        description='Grafana dashboards and datasources backup',
        epilog='Create tarball with grafana data'
    )
    required = params_parser.add_argument_group('required named arguments')

    required.add_argument('--api-key', metavar='<key>', dest='key',
        help='Your API Key, it must have admin permissions', required=True)

    required.add_argument('--api-url', metavar='<url>', dest='url',
        help='Api url', required=True)

    required.add_argument('--archive-dir', metavar='<path>', dest='archive_path',
        help='Path to dir with extracted backup', required=False, default='grafana-backup')

    params_parser.add_argument('--archivename', metavar="<name>", dest="archivename",
        help='Archive name of output file (WITHOUT FILE EXTENSION)', default='grafana-backup')

    params_parser.add_argument('action', default='backup', choices=['backup', 'restore'],
        help='Action, it can be "backup" or "restore"')

    args = params_parser.parse_args()

    tool = GrafanaTool(args.url, args.key)

    if args.action == 'backup':
        tool.do_backup(args.archivename)

    if args.action == 'restore':
        tool.do_restore(args.archive_path)


if __name__ == '__main__':
    main()
