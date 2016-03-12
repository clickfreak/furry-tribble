#!/usr/bin/env python3

import requests
import logging
import os
import sys
import json
import yaml
import tempfile
import shutil

logging.basicConfig(level=logging.DEBUG,
                        format=u'%(pathname)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s')

def main():
    api_url = "" # http://grafana.example.org:4053/api
    api_key = ""
    # print("Hello world!")
    api_session = requests.Session()
    api_session.headers.update({"Authorization": "Bearer {}".format(api_key)})

    try:
        r = api_session.get(api_url+"/datasources")
        datasources = r.json()
        # print(yaml.dump(datasources, indent=2, default_flow_style=False))
        print(json.dumps(datasources, indent=2))

    except:
        logging.error("Can't get datasources list")
        return

    try:
        r = api_session.get(api_url+"/search")
        dashboards_list = r.json()
        print(json.dumps(dashboards_list, indent=2))
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
            r = api_session.get(api_url+"/dashboards/{uri}".format(**dashboard))
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

    shutil.make_archive("grafana-backup", "gztar", root_dir=tmpdirname.name)
    tmpdirname.cleanup()

if __name__ == '__main__':
    main()
