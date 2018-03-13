#!/usr/bin/python
#
# Copyright 2013 Greg Neagle
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""autopkg processor to upload files from a munki repo to AirWatch"""

import base64
import os.path
import plistlib
import requests #dependency
import subprocess

from autopkglib import Processor, ProcessorError, get_pref
from requests_toolbelt import StreamingIterator #dependency from requests

__all__ = ["AWImportProcessor"]

class AWImportProcessor(Processor):
    """Uploads apps from munki repo to AirWatch"""
    input_variables = {
        "munki_repo_path": {
            "required": True,
            "description": "Path to the munki repo.",
        },
        "force_import": {
            "required": False,
            "description":
                "If not false or empty or undefined, force an AW import",
        },
        "airwatch_url": {
            "required": True,
            "description": "Base url of your AirWatch server \
                            (eg. https://myorg.awmdm.com)"
        },
        "airwatch_groupid": {
            "required": True,
            "description": "Group ID of AirWatch Organization Group \
                            where files will be uploaded"
        },
        "api_token": {
            "required": True,
            "description": "AirWatch API Token",
        },
        "api_username": {
            "required": True,
            "description": "AirWatch API Username",
        },
        "api_password": {
            "required": True,
            "description": "AirWatch API User Password",
        }
    }
    output_variables = {
        "makecatalogs_resultcode": {
            "description": "Result code from the makecatalogs operation.",
        },
        "makecatalogs_stderr": {
            "description": "Error output (if any) from makecatalogs.",
        },
        "airwatch_resultcode": {
            "description": "Result code from the AW Import.",
        },
        "airwatch_stderr": {
            "description": "Error output (if any) from the AW Import.",
        },
    }

    description = __doc__

    def streamFile(self, filepath, url, headers):
        '''expects headers w/ token, auth, and content-type'''
        streamer = StreamingIterator(os.path.getsize(filepath), open(filepath, 'rb'))
        r = requests.post(url, data=streamer, headers=headers)
        self.output(r.json())
        return r.json()

    def awimport(self, filetype, filepath):
        BASEURL = self.env.get("airwatch_url")
        GROUPID = self.env.get("airwatch_groupid")
        APITOKEN = self.env.get("api_token")
        USERNAME = self.env.get("api_username")
        PASSWORD = self.env.get("api_password")

        # create baseline headers
        hashed_auth = base64.b64encode('{}:{}'.format(USERNAME, PASSWORD))
        basicauth = 'Basic {}'.format(hashed_auth.encode('utf-8'))
        headers = {'aw-tenant-code': APITOKEN,
                   'Accept': 'application/json',
                   'authorization': basicauth}

        # get OG ID from GROUPID
        r = requests.get(BASEURL + '/api/system/groups/search?groupid=' + GROUPID, headers=headers)
        for result in r.text['LocationGroups'][0]:
            if result['GroupId'] == GROUPID:
                ogid = result['Id']['Value']
        self.output(print 'OG ID: {}'.format(ogid))

        if filetype == 'pkg':
            # upload pkg, dmg, mpkg file (application/octet-stream)
            headers['Content-Type'] = 'application/octet-stream'
            posturl = BASEURL + '/api/mam/blobs/uploadblob?filename=' + \
                      os.path.basename(filepath) + '&organizationgroup=' + \
                      str(ogid) + '&moduleType=Application' # Application only for pkg/dmg upload

            res = streamFile(filepath, posturl, headers)
            pkg_id = res['Value']
            self.output(print 'Pkg ID: {}'.format(pkg_id))
            return pkg_id
        elif filetype == 'pkginfo':
            # upload pkginfo plist (text/xml)
            headers['Content-Type'] = 'text/xml'
            posturl = BASEURL + '/api/mam/blobs/uploadblob?filename=' + \
                      os.path.basename(filepath) + '&organizationgroup=' + \
                      str(ogid) + '&moduleType=General' # General for pkginfo and icon

            res = streamFile(filepath, posturl, headers)
            pkginfo_id = res['Value']
            self.output(print 'PkgInfo ID: {}'.format(pkginfo_id))
            return pkginfo_id
        elif filetype == 'icon':
            # upload icon file (image/png)
            headers['Content-Type'] = 'image/png'
            posturl = BASEURL + '/api/mam/blobs/uploadblob?filename=' + \
                      os.path.basename(ICON_FILEPATH) + '&organizationgroup=' + \
                      str(ogid) + '&moduleType=General' # General for pkginfo and icon

            res = streamFile(ICON_FILEPATH, posturl, headers)
            icon_id = res['Value']
            print 'Icon ID: {}'.format(icon_id)
            return icon_id



    def main(self):
        '''Rebuild Munki catalogs in repo_path'''

        cache_dir = get_pref("CACHE_DIR") or os.path.expanduser(
            "~/Library/AutoPkg/Cache")
        current_run_results_plist = os.path.join(
            cache_dir, "autopkg_results.plist")
        try:
            run_results = plistlib.readPlist(current_run_results_plist)
        except IOError:
            run_results = []

        something_imported = False
        # run_results is an array of autopackager.results,
        # which is itself an array.
        # look through all the results for evidence that
        # something was imported
        # this could probably be done as an array comprehension
        # but might be harder to grasp...
        for result in run_results:
            for item in result:
                if item.get("Processor") == "MunkiImporter":
                    if item["Output"].get("pkginfo_repo_path"):
                        something_imported = True
                        break

        if not something_imported and not self.env.get("force_import"):
            self.output("No updates so nothing to import to AirWatch")
            self.env["airwatch_resultcode"] = 0
            self.env["airwatch_stderr"] = ""
        elif self.env.get("force_import") and not something_imported:
            #TODO: Upload all pkgs/pkginfos/icons to AW from munki repo
            #Look for munki code where it tries to find the icon in the repo
            pass
        else:
            for result in run_results:
                for item in result:
                    if item.get("Processor") == "MunkiImporter":
                        if item["Output"].get("pkginfo_repo_path"):
                            pi = item["Output"].get("pkginfo_repo_path")
                            self.output(print awimport('pkginfo', pi))
                        if item["Output"].get("pkg_repo_path"):
                            pkg = item["Output"].get("pkginfo_repo_path")
                            self.output(print awimport('pkg', pkg))




if __name__ == "__main__":
    PROCESSOR = MakeCatalogsProcessor()
    PROCESSOR.execute_shell()
