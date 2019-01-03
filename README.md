# AirWatchImporter
AirWatchImporter is an AutoPkg Processor that can automatically import packages into AirWatch, as well as assign them to one or multiple smart groups, and set certain deployment options such as Push Mode.

## Dependencies

### Server Side
You _must_ be running AirWatch Console 9.3.0.0 or higher.

### Client/AutoPkg Side

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
* [`munki_repo_path`](https://github.com/jprichards/AirWatchImporter/wiki/munki_repo_path)
* [`force_import`](https://github.com/jprichards/AirWatchImporter/wiki/force_import)
* [`airwatch_url`](https://github.com/jprichards/AirWatchImporter/wiki/airwatch_url)
* [`airwatch_groupid`](https://github.com/jprichards/AirWatchImporter/wiki/airwatch_groupid)
* [`api_token`](https://github.com/jprichards/AirWatchImporter/wiki/api_token)
* [`api_username`](https://github.com/jprichards/AirWatchImporter/wiki/api_username)
* [`api_password`](https://github.com/jprichards/AirWatchImporter/wiki/api_password)
* [`smart_group_name`](https://github.com/jprichards/AirWatchImporter/wiki/smart_group_name)
* [`push_mode`](https://github.com/jprichards/AirWatchImporter/wiki/push_mode)

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

## Example AutoPkg Recipe

```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Description</key>
    <string>Creates a munki package, imports it into the AirWatch Admin console.</string>
    <key>Identifier</key>
    <string>com.blah.airwatch.Firefox_EN</string>
    <key>Input</key>
    <dict>
        <key>NAME</key>
        <string>Firefox_EN</string>
    </dict>
    <key>ParentRecipe</key>
    <string>com.github.autopkg.munki.firefox-rc-en_US</string>
    <key>MinimumVersion</key>
    <string>0.4.0</string>
    <key>Process</key>
    <array>
        <dict>
            <key>Processor</key>
            <string>AirWatchImporter</string>
            <key>Arguments</key>
            <dict>
                <key>munki_repo_path</key>
                <string>MUNKI_REPO_PATH_HERE</string>
                <key>airwatch_url</key>
                <string>AIRWATCH_URL_HERE</string>
                <key>airwatch_groupid</key>
                <string>GROUP_ID_HERE</string>
                <key>api_token</key>
                <string>API_TOKEN_HERE</string>
                <key>api_username</key>
                <string>API_USERNAME_HERE</string>
                <key>api_password</key>
                <string>API_PASSWORD_HERE</string>
                <key>smart_group_name</key>
                <string>SMART_GROUP_NAME</string>
            </dict>
        </dict>
    </array>
</dict>
</plist>
```
