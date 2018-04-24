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
import datetime

from autopkglib import Processor, ProcessorError, get_pref
from requests_toolbelt import StreamingIterator #dependency from requests

__all__ = ["AirWatchImporter"]

class AirWatchImporter(Processor):
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
        },
        "smart_group_name": {
            "required": False,
            "description": "The name of the group that the app should \
                            be assigned to."
        },
        "push_mode": {
            "required": False,
            "description": "Tells AirWatch how to deploy the app, Auto \
                            or On-Demand."
        },
        "deployment_date": {
            "required": False,
            "description": "This sets the date that the deployment of \
                            the app should begin."
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
        return r.json()

    def convertTime(self, deployment_time):
        if int(deployment_time) <= 23:
            if int(deployment_time) is 24:
                self.output("deployment_time was set to 24, changing to 0")
                deployment_time = 0
            else:
                raise ProcessorError("Please enter a valid 24-hour time (i.e. between 0-23)")

        today = datetime.date.today()
        timestamp = time.strftime('%H')
        utc_datetime = datetime.datetime.utcnow()
        utc_datetime_formatted = utc_datetime.strftime("%H")
        time_difference = ((int(utc_datetime_formatted) - int(timestamp)) * 60 * 60)
        #availability_time = datetime.timedelta(hours=int(time_difference))
        if int(utc_datetime_formatted) < int(deployment_time):
            sec_to_add = int(((int(deployment_time) - int(timestamp)) * 60 * 60) + int(time_difference))
        elif int(utc_datetime_formatted) > int(deployment_time):
            sec_to_add = int(((24 - int(timestamp) + int(deployment_time)) * 60 * 60) + int(time_difference))

    def awimport(self, pkg, pkg_path, pkg_info, pkg_info_path, icon, icon_path):
        self.output("Beginning the AirWatch import process for %s." % self.env["NAME"] ) ## Add name of app being imported
        BASEURL = self.env.get("airwatch_url")
        GROUPID = self.env.get("airwatch_groupid")
        APITOKEN = self.env.get("api_token")
        USERNAME = self.env.get("api_username")
        PASSWORD = self.env.get("api_password")
        SMARTGROUP = self.env.get("smart_group_name")
        PUSHMODE = self.env.get("push_mode")

        ## Get some global variables for later use
        app_version = self.env["munki_importer_summary_result"]["data"]["version"]
        app_name = self.env["munki_importer_summary_result"]["data"]["name"]


        # create baseline headers
        hashed_auth = base64.b64encode('{}:{}'.format(USERNAME, PASSWORD))
        basicauth = 'Basic {}'.format(hashed_auth.encode('utf-8'))
        headers = {'aw-tenant-code': APITOKEN,
                   'Accept': 'application/json',
                   'authorization': basicauth}

        # get OG ID from GROUPID
        try:
            r = requests.get(BASEURL + '/api/system/groups/search?groupid=' + GROUPID, headers=headers)
            result = r.json()
        except AttributeError:
            raise ProcessorError('AirWatchImporter: Unable to retrieve an ID for the Organizational Group specified: %s' % GROUPID)
        except:
            raise ProcessorError('AirwatchImporter: Something went wrong when making the OG ID API call.')

        if GROUPID in result['LocationGroups'][0]['GroupId']:
            ogid = result['LocationGroups'][0]['Id']['Value']
        self.output('OG ID: {}'.format(ogid))

        if not pkg_path == None:
            self.output("Uploading pkg...")
            # upload pkg, dmg, mpkg file (application/octet-stream)
            headers['Content-Type'] = 'application/octet-stream'
            posturl = BASEURL + '/api/mam/blobs/uploadblob?filename=' + \
                      os.path.basename(pkg_path) + '&organizationgroup=' + \
                      str(ogid) + '&moduleType=Application' # Application only for pkg/dmg upload
            try:
                res = self.streamFile(pkg_path, posturl, headers)
                pkg_id = res['Value']
                self.output('Pkg ID: {}'.format(pkg_id))
            except KeyError:
                raise ProcessorError('AirWatchImporter: Something went wrong while uploading the pkg.')
        else:
            raise ProcessorError('AirWatchImporter: Did not receive a pkg_path from munkiimporter.')

        if not pkg_info_path == None:
            self.output("Uploading pkg_info...")
            # upload pkginfo plist (text/xml)
            headers['Content-Type'] = 'text/xml'
            posturl = BASEURL + '/api/mam/blobs/uploadblob?filename=' + \
                      os.path.basename(pkg_info_path) + '&organizationgroup=' + \
                      str(ogid) + '&moduleType=General' # General for pkginfo and icon
            try:
                res = self.streamFile(pkg_info_path, posturl, headers)
                pkginfo_id = res['Value']
                self.output('PkgInfo ID: {}'.format(pkginfo_id))
            except KeyError:
                raise ProcessorError('AirWatchImporter: Something went wrong while uploading the pkginfo.')
        else:
            raise ProcessorError('AirWatchImporter: Did not receive a pkg_info_path from munkiimporter.')

        if not icon_path == None:
            self.output("Uploading icon...")
            # upload icon file (image/png)
            headers['Content-Type'] = 'image/png'
            posturl = BASEURL + '/api/mam/blobs/uploadblob?filename=' + \
                      os.path.basename(icon_path) + '&organizationgroup=' + \
                      str(ogid) + '&moduleType=General' # General for pkginfo and icon
            try:
                res = self.streamFile(icon_path, posturl, headers)
                icon_id = res['Value']
                self.output('Icon ID: {}'.format(icon_id))
            except KeyError:
                self.output('Something went wrong while uploading the icon.')
                self.output('Continuing app object creation...')
                pass
        else:
            icon_id = ''

        ## We need to reset the headers back to JSON
        headers = {'aw-tenant-code': APITOKEN,
                   'authorization': basicauth,
                   'Content-Type': 'application/json'}

        ## Create a dict with the app details to be passed to AW
        ## to create the App object
        app_details = {"pkgInfoBlobId": str(pkginfo_id),
                        "applicationBlobId": str(pkg_id),
                        "applicationIconId": str(icon_id),
                        "isManagedInstall": True}

        ## Make the API call to create the App object 
        self.output("Creating App Object in AirWatch...")
        r = requests.post(BASEURL + '/api/mam/groups/%s/macos/apps' % ogid, headers=headers, json=app_details)
        if not r.status_code == 200 or not r.status_code == 204:
            raise ProcessorError('AirWatchImporter: Unable to successfully create the App Object.') 
        ## Now get the new App ID from the server
        try:
            r = requests.get(BASEURL + '/api/mam/apps/search?locationgroupid=%s&applicationname=%s' % (ogid, app_name), headers=headers)
            search_results = r.json()
            for app in search_results["Application"]:
                if app["ActualFileVersion"] == str(app_version) and app['ApplicationName'] in app_name:
                    aw_app_id = app["Id"]["Value"]
                    self.output('App ID: %s' % aw_app_id)
                    break
        except AttributeError:
            raise ProcessorError('AirWatchImporter: Unable to retrieve the App ID for the newly created app')

        ## Get the Smart Group ID to assign the package to
        ## we need to replace any spaces with '%20' for the API call
        condensed_sg = SMARTGROUP.replace(" ", "%20")
        r = requests.get(BASEURL + "/api/mdm/smartgroups/search?name=%s" % condensed_sg, headers=headers)
        smart_group_results = r.json()
        for sg in smart_group_results["SmartGroups"]:
            if SMARTGROUP in sg["Name"]:
                sg_id = sg["SmartGroupID"]
                self.output('Smart Group ID: %s' % sg_id)

        ## Create the app assignment details
        app_assignment = {
                          "SmartGroupIds": [
                            sg_id
                          ],
                          "DeploymentParameters": {
                            "PushMode": PUSHMODE
                            }
                        }

        ## Make the API call to assign the App
        r = requests.post(BASEURL + '/api/mam/apps/internal/%s/assignments' % aw_app_id, headers=headers, json=app_assignment)
        if not r.status_code == 200 or not r.status_code == 204:
            self.output('Unable to successfully assign the app [%s] to the group [%s]' % (self.env['NAME'], SMARTGROUP))
        return "Application was successfully uploaded to AirWatch."

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
        
        try:
            pkginfo_path = self.env["munki_importer_summary_result"]["data"]["pkginfo_path"]
        except:
            pkginfo_path = None

        # run_results is an array of autopackager.results,
        # which is itself an array.
        # look through all the results for evidence that
        # something was imported
        # this could probably be done as an array comprehension
        # but might be harder to grasp...
#        for result in run_results:
#            self.output(result)
#            for item in result:
#                if "MunkiImporter" in item.get("Processor"):
#                    self.output("We found MunkiImporter")
#                    if item["Output"]["pkginfo_repo_path"]:
#                        something_imported = True
#                        break
        if pkginfo_path:
            something_imported = True

        if not something_imported and not self.env.get("force_import"):
            self.output(run_results)
            self.output("No updates so nothing to import to AirWatch")
            self.env["airwatch_resultcode"] = 0
            self.env["airwatch_stderr"] = ""
        elif self.env.get("force_import") and not something_imported:
            #TODO: Upload all pkgs/pkginfos/icons to AW from munki repo
            #Look for munki code where it tries to find the icon in the repo
            pass
        else:  
            pi = self.env["pkginfo_repo_path"]
            pkg = self.env["pkg_repo_path"]
            icon_path = None
            #self.output(self.awimport('pkginfo', pi))
            #self.output(self.awimport('pkg', pkg))

            self.output(self.awimport('pkg', pkg, 'pkginfo', pi, 'icon', icon_path))


if __name__ == "__main__":
    PROCESSOR = MakeCatalogsProcessor()
    PROCESSOR.execute_shell()
