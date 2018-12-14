Installing the Insights Client
------------------------------
To work with the Insights Client, we must also install the Insights Core. To begin, create the insights directory at the same level as quipucords and clone the following repositories::

    git clone git@github.com:RedHatInsights/insights-core.git
    git clone git@github.com:RedHatInsights/insights-client.git

Setting Up a Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The insights-client will need to be installed inside of the same virtual environment as the QPC client::

    cd ../location/of/qpc/client
    pipenv shell

Edit the Insights Client Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You will need uncomment and modify these values in the Insights Client Configuration in order to be authorized to upload::

    cd insights-client
    vim etc/insights-client.conf
    auto_config=False
    username=<your_username>
    password=<your_password>

**Note:** The username and password is based off your login for https://accesss.redhat.com/

Building with Insights Client on Mac
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
After configuration is setup, you will need to build the insights client. For QPC to access the Insights Client locally on Mac, we need to checkout the `os-x-test` branch::

    cd ../insights-client
    git fetch origin os-x-test && git checkout os-x-test
    sudo sh lay-the-eggs-osx.sh

Building with Insights Client on RHEL
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
After configuration is setup, you will need to build the insights client::

    sudo sh lay-the-eggs.sh

Test Connection Command:
^^^^^^^^^^^^^^^^^^^^^^^^
To check your connection status using the Insight Clients you will need to run the following command::

    sudo EGG=/etc/insights-client/rpm.egg BYPASS_GPG=True insights-client --no-gpg --test-connection

Insights Upload Command:
^^^^^^^^^^^^^^^^^^^^^^^^
To upload a tar.gz file using the Insight Clients you will need to run the following command::

    sudo EGG=/etc/insights-client/rpm.egg BYPASS_GPG=True insights-client --no-gpg --payload=test.tar.gz --content-type=application/vnd.redhat.qpc.test+tgz

QPC Upload Command:
^^^^^^^^^^^^^^^^^^^
To upload a deployments report using the QPC Client you will need to run the following command::

    qpc insights upload (--scan-job scan_job_identifier | --report report_identifier | --dev)

**Note:** If you developing on a mac, you will need to use the ``--dev`` argument.

Troubleshoot Caching Issues:
^^^^^^^^^^^^^^^^^^^^^^^^^^
If you run into caching issues while working with the insights client, you can delete the previous rpm that was created by running the following commands::

    cd /etc/insights-client/
    rm insights-client.conf
    rm rpm.egg
    rm rpm.egg.asc

**Note:** After removing the previous rpm, you will need to build the insights client.
