Installing the Insights Client
------------------------------
To work with the Insights Client, we must also install the Insights Core. To begin, create the insights directory at the same level as quipucords and clone the following repositories::

    git clone git@github.com:RedHatInsights/insights-client.git
    git clone git@github.com:RedHatInsights/insights-core.git
    curl https://api.access.redhat.com/r/insights/v1/static/core/insights-core.egg.asc > last_stable.egg.asc
    mv last_stable.egg.asc /var/lib/insights/last_stable.egg.asc
    curl https://api.access.redhat.com/r/insights/v1/static/core/insights-core.egg > last_stable.egg
    mv last_stable.egg /var/lib/insights/last_stable.egg

**Note:** You may need to create the ``/var/lib/insights`` structure.

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
    http_timeout=20

**Note:** The username and password is based off your login for https://accesss.redhat.com/

Building with Insights Client on Mac
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
After configuration is setup, you will need to build the insights client. For QPC to access the Insights Client locally on Mac, we need to checkout the `os-x-test` branch::

  cd ../insights-client
  git stash
  git fetch origin os-x-test && git checkout os-x-test
  git stash pop
  sudo sh lay-the-eggs-osx.sh

Building with Insights Client on RHEL
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
After configuration is setup, you will need to build the insights client::

    sudo sh lay-the-eggs.sh

Test Connection Command:
^^^^^^^^^^^^^^^^^^^^^^^^
To check your connection status using the Insight Clients you will need to run the following command::

    sudo BYPASS_GPG=True insights-client --no-gpg --test-connection

Insights Upload Command:
^^^^^^^^^^^^^^^^^^^^^^^^
To upload a tar.gz file using the Insight Clients you will need to run the following command::

    sudo BYPASS_GPG=True insights-client --no-gpg --payload=test.tar.gz --content-type=application/vnd.redhat.qpc.test+tgz

**WARNING:** If a ``machine-id`` is not present in the ``/etc/insights-client`` directory, your first upload attempt will fail. However, the ``machine-id`` will be created for you by the insights client, so your second attempt will work.

QPC Upload Command:
^^^^^^^^^^^^^^^^^^^
To upload a deployments report using the QPC Client you will need to run the following command::

    qpc insights upload (--scan-job scan_job_identifier | --report report_identifier | --no-gpg)

**Note:** If you are developing on a mac, you will need to use the ``--no-gpg`` argument.

Troubleshoot Caching Issues:
^^^^^^^^^^^^^^^^^^^^^^^^^^
If you run into caching issues while working with the insights client, you can delete the previous rpm that was created by running the following commands::

    cd /etc/insights-client/
    rm insights-client.conf
    rm rpm.egg
    rm rpm.egg.asc

**Note:** After removing the previous rpm, you will need to build the insights client.