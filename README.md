# AirWatchImporter
AirWatchImporter is an AutoPkg Processor that can autoatically import packages into AirWAtch, as well as assign them to one or multiple smart groups, and set certain deployment options such as Push Mode.

## Dependencies required
Currently, in order to run AirWatchImporter, you must first install two Python libraries:

* The `requests` library
* The `requests_toolbelt` library

These can both be install by running either:

```
easy_install requests && easy_install requests_toolbelt
```

or

```
pip install requests && pip install requests_toolbelt
```
## AutoPkg Shared Processor

As of AutoPkg 0.4.0 you can use this processor as a shared processor.

Add the processor repo:

```
autopkg repo-add https://github.com/jprichards/AirWatchImporter
```

Then use this as the processor in your recipes:

```
com.github.jprichards.AirWatchImporter/AirWatchImporter
```

See this wiki for more information on shared processor:
https://github.com/autopkg/autopkg/wiki/Processor-Locations

## Available Input Variables
* [`munki_repo_path`]()
* [`force_import`]()
* [`airwatch_url`]()
* [`airwatch_groupid`]()
* [`api_token`]()
* [`api_username`]()
* [`api_password`]()
* [`smart_group_name`]()
* [`push_mode`]()

## Sample Processor

```
<key>Process</key>
<array>
    <dict>
        <key>Processor</key>
        <string>AWImportProcessor</string>
        <key>Arguments</key>
        <dict>
            <key>munki_repo_path</key>
            <string>/Volumes/munki_repo/</string>
            <key>airwatch_url</key>
            <string>https://mdm.awmdm.com</string>
            <key>airwatch_groupid</key>
            <string>macs</string>
            <key>api_token</key>
            <string>fffffffffffffffffffffffffffffffffffffff</string>
            <key>api_username</key>
            <string>USERNAME</string>
            <key>api_password</key>
            <string>PASSWORD</string>
            <key>smart_group_name</key>
            <string>My Smart Group</string>
            <key>push_mode</key>
            <string>OnDemand</string>
        </dict>
    </dict>
</array>
```