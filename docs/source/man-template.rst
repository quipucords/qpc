QPC_VAR_PROGRAM_NAME
==========================

Name
----

QPC_VAR_PROGRAM_NAME - Inspect and report on product entitlement metadata from various sources, including networks and systems management solutions.


Synopsis
--------

``QPC_VAR_PROGRAM_NAME command subcommand [options]``

Description
-----------

The QPC_VAR_PROJECT tool, accessed through the ``QPC_VAR_PROGRAM_NAME`` command, is an inspection and reporting tool. It is designed to identify environment data, or *facts*, such as the number of physical and virtual systems on a network, their operating systems, and other configuration data. In addition, it is designed to identify and report more detailed facts for some versions of key Red Hat packages and products for the Linux based IT resources in that network. The ability to inspect the software and systems that are running on your network improves your ability to understand and report on your usage. Ultimately, this inspection and reporting process is part of the larger system administration task of managing your inventories.

The QPC_VAR_PROJECT tool uses two types of configuration to manage the inspection process. A *credential* contains configuration, such as the username and password or SSH key of the user that runs the inspection process. Certain credential types also support the use of an access token as an alternative authentication method. A *source* defines the entity to be inspected and one or more credentials to use during the inspection process. The entity to be inspected can be a host, subnet, network, or systems management solution such as Openshift, Red Hat Advanced Cluster Security, Ansible Automation Platform, vCenter Server, or Satellite. You can save multiple credentials and sources to use with QPC_VAR_PROJECT in various combinations as you run inspection processes, or *scans*. When you have completed a scan, you can access the output as a *report* to review the results.
By default, the credentials and sources that are created when using QPC_VAR_PROJECT are encrypted in a database. The values are encrypted with AES-256 encryption. They are decrypted when the QPC_VAR_PROJECT server runs a scan by using a *vault password* to access the encrypted values that are stored in the database.

The QPC_VAR_PROJECT tool is an *agentless* inspection tool, so there is no need to install the tool on the sources to be inspected.

This manual page describes the commands, subcommands, and options for the ``QPC_VAR_PROGRAM_NAME`` command and includes usage information and example commands.

Usage
-----

The ``QPC_VAR_PROGRAM_NAME`` command has several subcommands that encompass the inspection and reporting workflow. Within that workflow, ``QPC_VAR_PROGRAM_NAME`` performs the following major tasks:

* Logging in to the server:

  ``QPC_VAR_PROGRAM_NAME server login --username admin``

* Creating credentials:

  ``QPC_VAR_PROGRAM_NAME cred add --name=credname1 --type=type --username=user1 --password``

* Creating sources:

  ``QPC_VAR_PROGRAM_NAME source add --name=sourcename1 --type=type --hosts server1.example.com server2.example.com --cred credname1 credname2``

* Creating scans:

  ``QPC_VAR_PROGRAM_NAME scan add --name=scan1 --sources sourcename1 sourcename2``

* Running a scan:

  ``QPC_VAR_PROGRAM_NAME scan start --name=scan1``

* Working with scans:

  ``QPC_VAR_PROGRAM_NAME scan show --name=scan1``

* Working with scan jobs:

  ``QPC_VAR_PROGRAM_NAME scan job --id=1``

* Generating reports:

  ``QPC_VAR_PROGRAM_NAME report deployments --id 1 --csv --output-file=~/scan_result.csv``

The following sections describe these commands, their subcommands, and their options in more detail. They also describe additional tasks that are not highlighted in the previous list of major workflow tasks.

Server Authentication
---------------------

Use the ``QPC_VAR_PROGRAM_NAME server`` command to configure connectivity with the server and to log in to and log out of the server.

Configuring the server
~~~~~~~~~~~~~~~~~~~~~~

To configure the connection to the server, supply the host address. Supplying a port for the connection is optional.

**QPC_VAR_PROGRAM_NAME server config --host=** *host* **[--port=** *port* **]**

``--host=host``

  Required. Sets the host address for the server. If you are running the ``QPC_VAR_PROGRAM_NAME`` command on the same system as the server, the default host address for the server is ``127.0.0.1``.

``--port=port``

  Optional. Sets the port to use to connect to the server. The default is ``9443``.


Logging in to the server
~~~~~~~~~~~~~~~~~~~~~~~~

To log in to the server after the connection is configured, use the ``login`` subcommand. This command retrieves a token that is used for authentication with any command line interface commands that follow it.

**QPC_VAR_PROGRAM_NAME server login [--username=** *username* **] [--password=** *password* **]**

``--username=username``

  Optional. Sets the username that is used to log in to the server. If omitted, QPC_VAR_PROGRAM_NAME will prompt for the server username.

``--password=password``

  Optional. Sets the password that is used to log in to the server. If omitted, QPC_VAR_PROGRAM_NAME will prompt for the server password.


Logging out of the server
~~~~~~~~~~~~~~~~~~~~~~~~~

To log out of the server, use the ``logout`` subcommand. This command removes the token that was created when the ``login`` command was used.

**QPC_VAR_PROGRAM_NAME server logout**


Viewing the server status
~~~~~~~~~~~~~~~~~~~~~~~~~

To view or save the status information for the server, use the ``status`` subcommand. This command returns data about your QPC_VAR_PROJECT server environment, such as server build and API versions, environment variable information, installed prerequisites and versions, and other server metadata that can help diagnose issues during troubleshooting.

**QPC_VAR_PROGRAM_NAME server status [--output-file** *path* **]**

``--output-file=path``

  Optional. Sets the path to a file location where the status information is saved.


Credentials
-----------

Use the ``QPC_VAR_PROGRAM_NAME cred`` command to create and manage credentials.

A credential contains a username-password pair, SSH key, or access token to authenticate with the remote servers during a scan. The QPC_VAR_PROJECT tool uses SSH to connect to servers on the network and uses credentials to access those servers.

When a scan runs, it uses a source that contains information such as the host names, IP addresses, a network, or a systems management solution to be accessed. The source also contains references to the credentials that are required to access those systems. A single source can contain a reference to multiple credentials as needed to connect to all systems in that network or systems management solution.

Creating and Editing Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a credential, supply the type of credential and supply SSH credentials as either a username-password pair, a username-key pair, or an access token. The QPC_VAR_PROJECT tool stores each set of credentials in a separate credential entry.

**QPC_VAR_PROGRAM_NAME cred add --name=** *name* **--type=** *(network | vcenter | satellite | openshift | rhacs | ansible)* **--username=** *username* (**--password** | **--sshkeyfile** *(ssh_keyfile | -)*) **[--sshpassphrase]** **--become-method=** *(sudo | su | pbrun | pfexec | doas | dzdo | ksu | runas )* **--become-user=** *user* **[--become-password]** **[--token]**

``--name=name``

  Required. Sets the name of the new credential. For the value, use a descriptive name that is meaningful to your organization. For example, you could identify the user or server that the credential relates to, such as ``admin12`` or ``server1_jdoe``. Do not include the password as part of this value, because the value for the ``--name`` option might be logged or printed during ``QPC_VAR_PROGRAM_NAME`` execution.

``--type=type``

  Required. Sets the type of credential. The value must be ``network``, ``vcenter``, ``satellite``, ``openshift``, ``rhacs`` or ``ansible``. You cannot edit a credential's type after creating it.

``--username=username``

  Required for both password and SSH key authentication. Sets the username of the SSH identity that is used to bind to the server.

``--password``

  Prompts for the password for the ``--username`` identity. Mutually exclusive with the ``--sshkeyfile`` and ``--token`` options.

``--sshkeyfile (ssh_keyfile | -)``

  Reads the private SSH key for the ``--username`` identity from the ``ssh_keyfile`` path specified. If the ``ssh_keyfile`` specified is ``-``, prompts for the private SSH key for the ``--username`` identity. Mutually exclusive with the ``--password`` and ``--token`` options.

``--sshpassphrase``

  Prompts for the passphrase to be used when connecting with an SSH key that requires a passphrase. Can only be used with the ``--sshkeyfile`` option.

``--become-method=become_method``

  Sets the method to become for privilege escalation when running a network scan. The value must be ``sudo``, ``su``, ``pbrun``, ``pfexec``, ``doas``, ``dzdo``, ``ksu``, or ``runas``. The default is set to ``sudo`` when the credential type is ``network``.

``--become-user=user``

  Sets the user to become when running a privileged command during a network scan.

``--become-password``

  Prompts for the privilege escalation password to be used when running a network scan.

``--token``

  Prompts for the access token for authentication. Mutually exclusive with the ``--sshkeyfile`` and ``--password`` options.

The information in a credential might change, including passwords, become passwords, SSH keys, the become_method, tokens or even the username. For example, your local security policies might require you to change passwords periodically. Use the ``QPC_VAR_PROGRAM_NAME cred edit`` command to change credential information. The parameters for ``QPC_VAR_PROGRAM_NAME cred edit`` are the same as those for ``QPC_VAR_PROGRAM_NAME cred add``.

**QPC_VAR_PROGRAM_NAME cred edit --name=** *name* **--username=** *username* (**--password** | **--sshkeyfile** *(ssh_keyfile | -)*) **[--sshpassphrase]** **--become-method=** *(sudo | su | pbrun | pfexec | doas | dzdo | ksu | runas )* **--become-user=** *user* **[--become-password]** **[--token]**

Listing and Showing Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``QPC_VAR_PROGRAM_NAME cred list`` command returns the details for every credential that is configured for QPC_VAR_PROJECT. This output includes the name and username for each entry. Secret values such as passwords and tokens are never displated in the output.

**QPC_VAR_PROGRAM_NAME cred list --type=** *(network | vcenter | satellite | openshift | rhacs | ansible)*

``--type=type``

  Optional.  Filters the results by credential type.  The value must be ``network``, ``vcenter``, ``satellite``, ``openshift``, ``rhacs``, or ``ansible``.

The ``QPC_VAR_PROGRAM_NAME cred show`` command is the same as the ``QPC_VAR_PROGRAM_NAME cred list`` command, except that it returns details for a single specified credential.

**QPC_VAR_PROGRAM_NAME cred show --name=** *name*

``--name=name``

  Required. Contains the name of the credential entry to display.


Clearing Credentials
~~~~~~~~~~~~~~~~~~~~

As the network infrastructure changes, it might be necessary to delete some credentials. Use the ``clear`` subcommand to delete credentials.

**IMPORTANT:** Remove or change the credential from any source that uses it *before* clearing a credential. Otherwise, any attempt to use the source to run a scan runs the command with a nonexistent credential, an action that causes the ``QPC_VAR_PROGRAM_NAME`` command to fail.

**QPC_VAR_PROGRAM_NAME cred clear (--name** *name* **| --all)**

``--name=name``

  Contains the credential to clear. Mutually exclusive with the ``--all`` option.

``--all``

  Clears all credentials. Mutually exclusive with the ``--name`` option.


Sources
-------

Use the ``QPC_VAR_PROGRAM_NAME source`` command to create and manage sources.

A source contains a single entity or a set of multiple entities that are to be inspected. A source can be one or more physical machines, virtual machines, or containers, or it can be a collection of network information, including IP addresses or host names, or it can be information about a systems management solution such as Openshift, Red Hat Advanced Cluster Security, Ansible Automation Platform, vCenter Server, or Satellite. The source also contains information about the SSH ports and SSH credentials that are needed to access the systems to be inspected. The SSH credentials are provided through reference to one or more of the QPC_VAR_PROJECT credentials that you configure.

When you configure a scan, it contains references to one or more sources, including the credentials that are provided in each source. Therefore, you can reference sources in different scan configurations for various purposes, for example, to scan your entire infrastructure or a specific sector of that infrastructure.

Creating and Editing Sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a source, supply the type of source with the ``type`` option, one or more host names or IP addresses to connect to with the ``--hosts`` option, and the credentials needed to access those systems with the ``--cred`` option. The ``QPC_VAR_PROGRAM_NAME source`` command allows multiple entries for the ``hosts`` and ``cred`` options. Therefore, a single source can access a collection of servers and subnets as needed to create an accurate and complete scan.

**QPC_VAR_PROGRAM_NAME source add --name=** *name*  **--type=** *(network | vcenter | satellite | openshift | rhacs | ansible)* **--hosts** *ip_address* **--cred** *credential* **[--exclude-hosts** *ip_address* **]** **[--port=** *port* **]** **[--use-paramiko=** *(True | False)* **]** **[--ssl-cert-verify=** *(True | False)* **]** **[--ssl-protocol=** *protocol* **]** **[--disable-ssl=** *(True | False)* **]**

``--name=name``

  Required. Sets the name of the new source. For the value, use a descriptive name that is meaningful to your organization, such as ``APSubnet`` or ``Lab3``.

``--type=type``

  Required. Sets the type of source.  The value must be ``network``, ``vcenter``, ``satellite``, ``openshift``, ``rhacs``, or ``ansible``. The type cannot be edited after a source is created.

``--hosts ip_address``

  Sets the host name, IP address, or IP address range to use when running a scan. You can also provide a path for a file that contains a list of host names or IP addresses or ranges, where each item is on a separate line. The following examples show several different formats that are allowed as values for the ``--hosts`` option:

  * A specific host name:

    ``--hosts server.example.com``

  * A specific IP address:

    ``--hosts 192.0.2.19``

  * An IP address range, provided in CIDR or Ansible notation. This value is only valid for the ``network`` type:

    ``--hosts 192.0.2.[0:255]``
    or
    ``--hosts 192.0.2.0/24``

  * A file:

    ``--hosts /home/user1/hosts_file``

``--exclude-hosts ip_address``

  Optional. Sets the host name, IP address, or IP address range to exclude when running a scan. Values for this option use the same formatting as the ``--hosts`` option examples.

``--cred credential``

  Contains the name of the credential to use to authenticate to the systems that are being scanned. If the individual systems that are being scanned each require different authentication credentials, you can use more than one credential. To add multiple credentials to the source, separate each value with a space, for example:

  ``--cred first_auth second_auth``

  **IMPORTANT:** A credential must exist before you attempt to use it in a source. A credential must be of the same type as the source.

``--port=port``

  Optional. Sets a port to be used for the scan. This value supports connection and inspection on a non-standard port. By default, a Network scan uses port 22, vCenter, Ansible, RHACS and Satellite scans use port 443, and an Openshift scan uses port 6443.

``--use-paramiko=(True | False)``

  Optional. Changes the Ansible connection method from the default open-ssh to the python ssh implementation.

``--ssl-cert-verify=(True | False)``

  Optional. Determines whether SSL certificate validation will be performed for the scan.

``--ssl-protocol=protocol``

  Optional. Determines the SSL protocol to be used for a secure connection during the scan. The value must be ``SSLv23``, ``TLSv1``, ``LSv1_1``, or ``TLSv1_2``.

``--disable-ssl=(True | False)``

  Optional. Determines whether SSL communication will be disabled for the scan.

The information in a source might change as the structure of the network changes. Use the ``QPC_VAR_PROGRAM_NAME source edit`` command to edit a source to accommodate those changes.

Although ``QPC_VAR_PROGRAM_NAME source`` options can accept more than one value, the ``QPC_VAR_PROGRAM_NAME source edit`` command is not additive. To edit a source and add a new value for an option, you must enter both the current and the new values for that option. Include only the options that you want to change in the ``QPC_VAR_PROGRAM_NAME source edit`` command. Options that are not included are not changed.

**QPC_VAR_PROGRAM_NAME source edit --name** *name* **[--hosts** *ip_address* **] [--cred** *credential* **] **[--exclude-hosts** *ip_address* **] [--port=** *port* **]** **[--use-paramiko=** *(True | False)* **]** **[--ssl-cert-verify=** *(True | False)* **]** **[--ssl-protocol=** *protocol* **]** **[--disable-ssl=** *(True | False)* **]**

For example, if a source contains a value of ``server1creds`` for the ``--cred`` option, and you want to change that source to use both the ``server1creds`` and ``server2creds`` credentials, you would edit the source as follows:

``QPC_VAR_PROGRAM_NAME source edit --name=mysource --cred server1creds server2creds``

**TIP:** After editing a source, use the ``QPC_VAR_PROGRAM_NAME source show`` command to review those edits.

Listing and Showing Sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``QPC_VAR_PROGRAM_NAME source list`` command returns the details for all configured sources. The output of this command includes the host names, IP addresses, or IP ranges, the credentials, and the ports that are configured for each source.

**QPC_VAR_PROGRAM_NAME source list [--type=** *(network | vcenter | satellite | openshift | rhacs | ansible)* **]**

``--type=type``

  Optional.  Filters the results by source type. The value must be ``network``, ``vcenter``, ``satellite``, ``openshift``, ``rhacs``, or ``ansible``.


The ``QPC_VAR_PROGRAM_NAME source show`` command is the same as the ``QPC_VAR_PROGRAM_NAME source list`` command, except that it returns details for a single specified source.

**QPC_VAR_PROGRAM_NAME source show --name=** *source*

``--name=source``

  Required. Contains the source to display.


Clearing Sources
~~~~~~~~~~~~~~~~

As the network infrastructure changes, it might be necessary to delete some sources. Use the ``QPC_VAR_PROGRAM_NAME source clear`` command to delete sources.

**QPC_VAR_PROGRAM_NAME source clear (--name=** *name* **| --all)**

``--name=name``

  Contains the name of the source to clear. Mutually exclusive with the ``--all`` option.

``--all``

  Clears all stored sources. Mutually exclusive with the ``--name`` option.


Scans
-----

Use the ``QPC_VAR_PROGRAM_NAME scan`` command to create, run and manage scans.

A scan contains a set of one or more sources of any type, plus additional options that refine how the scan runs, such as the products to omit from the scan, and the maximum number of parallel system scans. Because a scan can combine sources of different types, you can include any combination of Network, OpenShift, Red Hat Advanced Cluster Security, Ansible Automation Platform, Satellite, and vCenter Server sources in a single scan. When you configure a scan to include multiple sources of different types, for example a Network source and a Satellite source, the same part of your infrastructure might be scanned more than once. The results for this type of scan could show duplicate information in the reported results. However, you have the option to view the unprocessed detailed report that would show these duplicate results for each source type, or a processed deployments report with deduplicated and merged results.

The creation of a scan groups sources, the credentials contained within those sources, and the other options so that the act of running the scan is repeatable. When you run the scan, each instance is saved as a scan job.

Creating and Editing Scans
~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the ``QPC_VAR_PROGRAM_NAME scan add`` command to create scan objects with one or more sources. This command creates a scan object that references the supplied sources and contains any options supplied by the user.

**QPC_VAR_PROGRAM_NAME scan add --name** *name* **--sources=** *source_list* **[--max-concurrency=** *concurrency* **]** **[--disabled-optional-products=** *products_list* **]** **[--enabled-ext-product-search=** *products_list* **]** **[--ext-product-search-dirs=** *search_dirs_list* **]**

``--sources=source_list``

  Required. Contains the list of source names to use to run the scan.

``--max-concurrency=concurrency``

  Optional. Sets the maximum number of parallel system scans. If this value is not provided, the default is ``50``.

``--disabled-optional-products=products_list``

  Optional. Contains the list of products to exclude from inspection. Valid values are ``jboss_eap``, ``jboss_fuse``, and ``jboss_ws``.

``--enabled-ext-product-search=products_list``

  Optional. Contains the list of products to include for the extended product search. Extended product search is used to find products that might be installed in non-default locations. Valid values are ``jboss_eap``, ``jboss_fuse``, and ``jboss_ws``.

``--ext-product-search-dirs=search_dirs_list``

  Optional. Contains a list of absolute paths of directories to search with the extended product search. This option uses the provided list of directories to search for the presence of Red Hat JBoss Enterprise Application Platform (JBoss EAP), Red Hat Fuse (formerly Red Hat JBoss Fuse), and Red Hat JBoss Web Server (JBoss Web Server).

The information in a scan might change as the structure of the network changes. Use the ``QPC_VAR_PROGRAM_NAME scan edit`` command to edit an existing scan to accommodate those changes.

Although ``QPC_VAR_PROGRAM_NAME scan`` options can accept more than one value, the ``QPC_VAR_PROGRAM_NAME scan edit`` command is not additive. To edit a scan and add a new value for an option, you must enter both the current and the new values for that option. Include only the options that you want to change in the ``QPC_VAR_PROGRAM_NAME scan edit`` command. Options that are not included are not changed.

**QPC_VAR_PROGRAM_NAME scan edit --name** *name* **[--sources=** *source_list* **]** **[--max-concurrency=** *concurrency* **]** **[--disabled-optional-products=** *products_list* **]** **[--enabled-ext-product-search=** *products_list* **]** **[--ext-product-search-dirs=** *search_dirs_list* **]**

For example, if a scan contains a value of ``network1source`` for the ``--sources`` option, and you want to change that scan to use both the ``network1source`` and ``satellite1source`` sources, you would edit the scan as follows:

``QPC_VAR_PROGRAM_NAME scan edit --name=myscan --sources network1source satellite1source``

If you want to reset the ``--disabled-optional-products``, ``--enabled-ext-product-search``, or ``--ext-product-search-dirs`` back to their default values, you must provide the flag without any product values.

For example, if you want to reset the ``--disabled-optional-products`` option back to the default values, you would edit the scan as follows:

``QPC_VAR_PROGRAM_NAME scan edit --name=myscan --disabled-optional-products``

**TIP:** After editing a scan, use the ``QPC_VAR_PROGRAM_NAME scan show`` command to review those edits.

Listing and Showing Scans
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``QPC_VAR_PROGRAM_NAME scan list`` command returns the summary details for all created scan objects or all created scan objects of a certain type. The output of this command includes the identifier, the source or sources, and any options supplied by the user.

**QPC_VAR_PROGRAM_NAME scan list** **--type=** *(connect | inspect)*

``--type=type``

  Optional. Filters the results by scan type. This value must be ``connect`` or ``inspect``. A scan of type ``connect`` is a scan that began the process of connecting to the defined systems in the sources, but did not transition into inspecting the contents of those systems. A scan of type ``inspect`` is a scan that moves into the inspection process.

The ``QPC_VAR_PROGRAM_NAME scan show`` command is the same as the ``QPC_VAR_PROGRAM_NAME scan list`` command, except that it returns summary details for a single specified scan object.

**QPC_VAR_PROGRAM_NAME scan show --name** *name*

``--name=name``

  Required. Contains the name of the scan object to display.

Clearing Scans
~~~~~~~~~~~~~~

As the network infrastructure changes, it might be necessary to delete some scan objects. Use the ``QPC_VAR_PROGRAM_NAME scan clear`` command to delete scans.

**QPC_VAR_PROGRAM_NAME scan clear (--name=** *name* **| --all)**

``--name=name``

  Contains the name of the source to clear. Mutually exclusive with the ``--all`` option.

``--all``

  Clears all stored scan objects. Mutually exclusive with the ``--name`` option

Scanning
--------

Use the ``QPC_VAR_PROGRAM_NAME scan start`` command to create and run a scan job from an existing scan object. This command scans all of the host names or IP addresses that are defined in the supplied sources of the scan object from which the job is created. Each instance of a scan job is assigned a unique numeric *scan job identifier* to identify the scan results, so that the results data can be viewed later. Each instance of a scan job is also assigned a numeric *report identifier* for the generated report data. Because some scan jobs do not result in report generation, scan job identifiers and report identifiers might not match.

**IMPORTANT:** If any SSH agent connection is set up for a target host, that connection will be used as a fallback connection.

**QPC_VAR_PROGRAM_NAME scan start --name** *scan_name*

``--name=name``

  Contains the name of the scan object to run.

Viewing Scan Jobs
~~~~~~~~~~~~~~~~~

The ``QPC_VAR_PROGRAM_NAME scan job`` command returns the list of scan jobs for a scan object or information about a single scan job for a scan object. For the list of scan jobs, the output of this command includes the scan job identifiers for each currently running or completed scan job, the current state of each scan job, and the source or sources for that scan. For information about a single scan job, the output of this command includes status of the scan job, the start time of the scan job, and (if applicable) the end time of the scan job.

**QPC_VAR_PROGRAM_NAME scan job (--name** *scan_name* | **--id=** *scan_job_identifier* **) --status=** *(created | pending | running | paused | canceled | completed | failed)*

``--name=name``

  Contains the name of the scan object for which to display the scan jobs. Mutually exclusive with the ``--id`` option.

``--id=scan_job_identifier``

  Contains the identifier of a specified scan job to display. Mutually exclusive with the ``--name`` option.

``--status=status``

  Optional. Filters the results by scan job state. This value must be ``created``, ``pending``, ``running``, ``paused``, ``canceled``, ``completed``, or ``failed``.

Canceling Scans
~~~~~~~~~~~~~~~

When scan jobs are queued and running, you might need to stop the execution of scan jobs due to the needs of other business processes in your organization. The ``cancel`` subcommand enable you to control scan job execution.

The ``QPC_VAR_PROGRAM_NAME scan cancel`` command cancels the execution of a scan job.

**QPC_VAR_PROGRAM_NAME scan cancel --id=** *scan_job_identifier*

``--id=scan_job_identifier``

  Required. Contains the identifier of the scan job to cancel.


Reports
-------

Use the ``QPC_VAR_PROGRAM_NAME report`` command to retrieve a report from a scan. You can retrieve a report in a JavaScript Object Notation (JSON) format or in a comma-separated values (CSV) format. There are three different types of reports that you can retrieve, a *details* report, a *deployments* report, and an *insights* report.


Viewing the Details Report
~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``QPC_VAR_PROGRAM_NAME report details`` command retrieves a detailed report that contains the unprocessed facts that are gathered during a scan. These facts are the raw output from Network, vCenter, Satellite, Openshift, Red Hat Advanced Cluster Security and Ansible scans, as applicable.

**QPC_VAR_PROGRAM_NAME report details (--scan-job** *scan_job_identifier* **|** **--report** *report_identifier* **)** **(--json|--csv)** **--output-file** *path*

``--scan-job=scan_job_identifier``

  Contains the scan job identifier to use to retrieve the report. Mutually exclusive with the ``--report`` option.

``--report=report_identifier``

  Contains the report identifier to use to retrieve the report. Mutually exclusive with the ``--scan-job`` option.

``--json``

  Displays the results of the report in JSON format. Mutually exclusive with the ``--csv`` option.

``--csv``

  Displays the results of the report in CSV format. Mutually exclusive with the ``--json`` option.

``--output-file=path``

  Optional. Sets the path to a file location where the report data is saved. The file extension must be ``.json`` for the JSON report or ``.csv`` for the CSV report. When the field is not provided and `--json` specified, a JSON report will be generated to stdout.

Viewing the Deployments Report
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``QPC_VAR_PROGRAM_NAME report deployments`` command retrieves a report that contains the processed fingerprints from a scan. A *fingerprint* is the set of system, product, and entitlement facts for a particular physical or virtual machine. A processed fingerprint results from a procedure that merges facts from various sources, and, when possible, deduplicates redundant systems.

For example, the raw facts of a scan that includes both Network and vCenter sources could show two instances of a machine, indicated by an identical MAC address. The deployments report results in a deduplicated and merged fingerprint that shows both the Network and vCenter facts for that machine as a single set.

**QPC_VAR_PROGRAM_NAME report deployments (--scan-job** *scan_job_identifier* **|** **--report** *report_identifier* **)** **(--json|--csv)** **--output-file** *path*

``--scan-job=scan_job_identifier``

  Contains the scan job identifier to use to retrieve the report. Mutually exclusive with the ``--report`` option.

``--report=report_identifier``

  Contains the report identifier to use to retrieve the report. Mutually exclusive with the ``--scan-job`` option.

``--json``

  Displays the results of the report in JSON format. Mutually exclusive with the ``--csv`` option.

``--csv``

  Displays the results of the report in CSV format. Mutually exclusive with the ``--json`` option.

``--output-file=path``

  Optional. Sets the path to a file location where the report data is saved. The file extension must be ``.json`` for the JSON report or ``.csv`` for the CSV report. When the field is not provided and `--json` specified, a JSON report will be generated to stdout.

Viewing the Insights Report
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``QPC_VAR_PROGRAM_NAME report insights`` command retrieves a report that contains the hosts to be uploaded to the subscription insights service. A *host* is the set of system, product, and entitlement facts for a particular physical or virtual machine.

**QPC_VAR_PROGRAM_NAME report insights (--scan-job** *scan_job_identifier* **|** **--report** *report_identifier* **)** **--output-file** *path*

``--scan-job=scan_job_identifier``

  Contains the scan job identifier to use to retrieve the report. Mutually exclusive with the ``--report`` option.

``--report=report_identifier``

  Contains the report identifier to use to retrieve the report. Mutually exclusive with the ``--scan-job`` option.

``--output-file=path``

  Optional. Sets the path to a file location where the report data is saved. The file extension must be ``.tar.gz``.  If this field is not provided, it will automatically generate a JSON report to stdout.


Downloading Reports
~~~~~~~~~~~~~~~~~~~

The ``QPC_VAR_PROGRAM_NAME report download`` command downloads a set of reports, identified either by scan job identifer or report identifier, as a TAR.GZ file.  The report TAR.GZ file contains the details and deployments reports in both their JSON and CSV formats.

**QPC_VAR_PROGRAM_NAME report download (--scan-job** *scan_job_identifier* **|** **--report** *report_identifier* **)** **--output-file** *path*

``--scan-job=scan_job_identifier``

  Contains the scan job identifier to use to download the reports. Mutually exclusive with the ``--report`` option.

``--report=report_identifier``

  Contains the report identifier to use to download the reports. Mutually exclusive with the ``--scan-job`` option.

``--output-file=path``

  Required. Sets the path to a file location where the report data is saved. The file extension must be ``.tar.gz``.

Merging Scan Job Results
~~~~~~~~~~~~~~~~~~~~~~~~

The ``QPC_VAR_PROGRAM_NAME report merge`` command merges report data and returns the report identifier of the merged report. You can use this report identifier and the ``QPC_VAR_PROGRAM_NAME report`` command with the ``details`` or ``deployments`` subcommands to retrieve a report from the merged results.

**QPC_VAR_PROGRAM_NAME report merge (--job-ids** *scan_job_identifiers* **|** **--report-ids** *report_identifiers* **|** **--json-files** *json_details_report_files* **|** **--json-directory** *path_to_directory_of_json_files* **)**

``--job-ids=scan_job_identifiers``

  Contains the scan job identifiers of the report data that is to be merged. Mutually exclusive with the ``--report-ids`` option and the ``--json-files`` option.

``--report-ids=report_identifiers``

  Contains the report identifiers of the report data that is to be merged.  Mutually exclusive with the ``--job-ids`` option and the ``--json-files`` option.

``--json-files=json_details_report_files``

  Contains the JSON details report files to use to merge report data.  Mutually exclusive with the ``--job-ids`` option and the ``--report-ids`` option.

``--json-directory=path_to_directory_of_json_files``

  Contains a path to a directory with JSON details report files to use to merge report data. Mutually exclusive with the ``--job-ids`` and the ``--report-ids`` option.

The ``QPC_VAR_PROGRAM_NAME report merge`` command runs an asynchronous job. The output of this command provides a job ID that you can use to check the status of the merge job. To check the status of a merge job, run the following command, where the example job ID is ``1``::

# QPC_VAR_PROGRAM_NAME job status --id 1

Viewing the Status of an asynchronous Job
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``QPC_VAR_PROGRAM_NAME job status`` command can be used to check the status of a any asynchronous job (like report upload or merge).

**QPC_VAR_PROGRAM_NAME job status (--id** *report_job_identifier* **)**

``--id=report_job_identifier``

  Contains the job identifier to use to check for the status of a asynchronous job.


Manually Reprocessing Reports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``QPC_VAR_PROGRAM_NAME report upload`` command uploads a details report to reprocess it.  This could be useful if a value in the details report caused a system to be excluded.  After modication of the details report, simply run the ``QPC_VAR_PROGRAM_NAME report upload --json-file DETAILS_REPORT_JSON``.

**QPC_VAR_PROGRAM_NAME report upload (--json-file** *json_details_report_file* **)**

``--json-file=json_details_report_file``

  Contains the JSON details report file path to upload for reprocessing.

The ``QPC_VAR_PROGRAM_NAME report upload`` command runs an asynchronous job. The output of this command provides a job ID that you can use to check the status of the merge job. To check the status of a merge job, run the following command, where the example job ID is ``1``::

# QPC_VAR_PROGRAM_NAME job status --id 1

Insights
--------

Use the ``QPC_VAR_PROGRAM_NAME insights`` command to interact with Red Hat Insights and its services.

Configuring Insights
~~~~~~~~~~~~~~~~~~~~

To configure the connection to Insights server, you may optionally provide the host address and port to override the default values.

**QPC_VAR_PROGRAM_NAME insights config --host=** *host* **[--port=** *port* **]** **[--use-http]**

``--host=host``

  Optional. Sets the host address for Insights. The default host is ``console.redhat.com``.

``--port=port``

  Optional. Sets the port to use to connect to Insights. The default port is ``443``.

``--use-http``

  Optional. Determines whether to use HTTP instead of HTTPS. The default value is ``False``.

Login to Insights
~~~~~~~~~~~~~~~~~

To be able to publish reports to Insights, one must be authorized and successfully logged into Insights.

**QPC_VAR_PROGRAM_NAME insights login**

This command requests the authorization of the user to Insights. A user code and associated authorization URL is displayed that the user can access in a separate browser window to login to Insights and be authorized to use {{QPC_VAR_PROGRAM_NAME}} to publish reports.


Publishing to Insights
~~~~~~~~~~~~~~~~~~~~~~

The ``QPC_VAR_PROGRAM_NAME insights publish`` command allows you to publish an Insights report to Red Hat Insights and its services. You have two options for publishing a report: use the associated report identifier from the generating scan, or provide a previously downloaded report as an input file.

**QPC_VAR_PROGRAM_NAME insights publish (--report** *report_identifiers* **| --input-file** *path_to_tar_gz* )

``--report=report_identifier``

  Contains the report identifier to use to retrieve and publish the Insights report. Mutually exclusive with the ``--input-file`` option.

``--input-file=path to tar.gz containing the Insights report``

  Contains the path to the tar.gz containing the Insights report. Mutually exclusive with ``--report`` option.


Options for All Commands
------------------------

The following options are available for every QPC_VAR_PROJECT command.

``--help``

  Prints the help for the ``QPC_VAR_PROGRAM_NAME`` command or subcommand.

``-v``

  Enables the verbose mode. The ``-vvv`` option increases verbosity to show more information. The ``-vvvv`` option enables connection debugging.

Examples
--------

* Creating a new network type credential with a password

  ``QPC_VAR_PROGRAM_NAME cred add --name net_cred --type network --username QPC_VAR_PROGRAM_NAME_user --password``

* Creating a new network type credential with an SSH key from file

  ``QPC_VAR_PROGRAM_NAME cred add --name net_cred4 --type network --username QPC_VAR_PROGRAM_NAME_user --sshkeyfile $HOME/.ssh/user_ssh_key``

* Creating a new network type credential and prompt for an SSH key

  ``QPC_VAR_PROGRAM_NAME cred add --name net_cred4 --type network --username QPC_VAR_PROGRAM_NAME_user --sshkeyfile -``

* Creating a new network type credential with an SSH key from file requiring a passphrase

  ``QPC_VAR_PROGRAM_NAME cred add --name net_cred5 --type network --username QPC_VAR_PROGRAM_NAME_user --sshkeyfile $HOME/.ssh/user_ssh_key --sshpassphrase``

* Creating a new openshift type credential with a token

  ``QPC_VAR_PROGRAM_NAME cred add --name ocp_cred --type openshift --token``

* Creating a new openshift type credential with a password

  ``QPC_VAR_PROGRAM_NAME cred add --name ocp_cred2 --type openshift --username ocp_user --password``

* Creating a new vcenter type credential

  ``QPC_VAR_PROGRAM_NAME cred add --name vcenter_cred --type vcenter --username vc_user --password``

* Creating a new satellite type credential

  ``QPC_VAR_PROGRAM_NAME cred add --name sat_cred --type satellite --username sat_user --password``

* Creating a new ansible type credential

  ``QPC_VAR_PROGRAM_NAME cred add --name ansible_cred --type ansible --username ansible_user --password``

* Creating a new rhacs type credential

  ``QPC_VAR_PROGRAM_NAME cred add --name rhacs_cred --type rhacs --token``

* Listing all credentials

  ``QPC_VAR_PROGRAM_NAME cred list``

* Listing network credentials

  ``QPC_VAR_PROGRAM_NAME cred list --type network``

* Showing details for a specified credential

  ``QPC_VAR_PROGRAM_NAME cred show --name ocp_cred2``

* Clearing all credentials

  ``QPC_VAR_PROGRAM_NAME cred clear --all``

* Clearing a specified credential

  ``QPC_VAR_PROGRAM_NAME cred clear --name vcenter_cred``

* Creating a new network source

  ``QPC_VAR_PROGRAM_NAME source add --name net_source --type network --hosts 1.192.0.19 1.192.0.20 --cred net_cred``

* Creating a new network source with an excluded host

  ``QPC_VAR_PROGRAM_NAME source add --name net_source2 --type network --hosts 1.192.1.[0:255] --exclude-hosts 1.192.1.19 --cred net_cred``

* Creating a new vcenter source specifying a SSL protocol

  ``QPC_VAR_PROGRAM_NAME source add --name vcenter_source --type vcenter --hosts 1.192.0.19 --cred vcenter_cred --ssl-protocol SSLv23``

* Creating a new satellite source disabling SSL

  ``QPC_VAR_PROGRAM_NAME source add --name sat_source --type satellite --hosts satellite.example.redhat.com --disable-ssl true --cred sat_cred``

* Creating a new ansible source disabling SSL certificate verification

  ``QPC_VAR_PROGRAM_NAME source add --name ansible_source --type ansible --hosts  10.0.205.205 --ssl-cert-verify false --cred ansible_cred``

* Creating a new rhacs source

  ``QPC_VAR_PROGRAM_NAME source add --name rhacs_source --type rhacs --hosts  rhacs-cluster.example.com --cred rhacs_cred``

* Editing a source

  ``QPC_VAR_PROGRAM_NAME source edit --name net_source --hosts 1.192.0.[0:255] --cred net_cred net_cred2``

* Creating a scan

  ``QPC_VAR_PROGRAM_NAME scan add --name net_scan --sources net_source net_source2``

* Creating a scan that includes a list of products in the inspection

  ``QPC_VAR_PROGRAM_NAME scan add --name net_scan2 --sources net_source --enabled-ext-product-search jboss_eap``

* Editing a scan setting maximum concurrency

  ``QPC_VAR_PROGRAM_NAME scan edit --name net_scan --max-concurrency 10``

* Listing a scan filtering by scan type

  ``QPC_VAR_PROGRAM_NAME scan list --type inspect``

* Running a scan

  ``QPC_VAR_PROGRAM_NAME scan start --name net_scan``

* Canceling a scan

  ``QPC_VAR_PROGRAM_NAME scan cancel --id 1``

* Viewing scan jobs related to a specified scan

  ``QPC_VAR_PROGRAM_NAME scan job --name net_scan``

* Retrieves a JSON details report with no output file

  ``QPC_VAR_PROGRAM_NAME report details --report 2  --json``

* Retrieves a JSON details report

  ``QPC_VAR_PROGRAM_NAME report details --report 2  --json --output-file path_to_your_file.json``

* Retrieves a CSV deployments report

  ``QPC_VAR_PROGRAM_NAME report deployments --report 2  --csv --output-file path_to_your_file.csv``

* Retrieves a JSON Insights report with no output file

  ``QPC_VAR_PROGRAM_NAME report insights --scan-job 1``

* Retrieves a tar.gz Insights report

  ``QPC_VAR_PROGRAM_NAME report insights --scan-job 1 --output-file path_to_your_file.tar.gz``

* Downloading a set of reports

  ``QPC_VAR_PROGRAM_NAME report download --report 1 --output-file path_to_your_file.tar.gz``

* Merging scan job results using ids

  ``QPC_VAR_PROGRAM_NAME report report merge --job-ids 1 3``

* Merging scan job results providing JSON files

  ``QPC_VAR_PROGRAM_NAME report report merge --json-files path_to_report_1.json path_to_report_2.json``

* Reprocessing a report

  ``QPC_VAR_PROGRAM_NAME report upload --json-file path_to_report.json``

* Configuring Insights

  ``QPC_VAR_PROGRAM_NAME insights config --host stage.console.redhat.com --port 8080``

* Login to Insights

  ``QPC_VAR_PROGRAM_NAME insights login``

* Publishing to Insights using a report id

  ``QPC_VAR_PROGRAM_NAME insights publish --report 1``

* Publishing to Insights using a previously downloaded report

  ``QPC_VAR_PROGRAM_NAME insights publish --input-file path_to_report.tar.gz``


Security Considerations
-----------------------

The authentication data in the credentials and the network-specific and system-specific data in sources are stored in an AES-256 encrypted value within a database. A vault password is used to encrpyt and decrypt values. The vault password and decrypted values are in the system memory, and could theoretically be written to disk if memory swapping is enabled.

Authors
-------

QPC_VAR_PROJECT is written and maintained by Red Hat. Please refer to the commit history for a full list of contributors.

Copyright
---------

Copyright 2018-QPC_VAR_CURRENT_YEAR Red Hat, Inc. Licensed under the GNU Public License version 3.
