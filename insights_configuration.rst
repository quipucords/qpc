Installing the Insights Client
------------------------------
To work with the Insights Client, we must also install the Insights Core::

    git clone git@github.com:RedHatInsights/insights-client.git
    curl https://api.access.redhat.com/r/insights/v1/static/core/insights-core.egg.asc > last_stable.egg.asc
    mv last_stable.egg.asc /var/lib/insights/
    curl https://api.access.redhat.com/r/insights/v1/static/core/insights-core.egg
    mv last_stable.egg /var/lib/insights/

Edit the Insights Client Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You will need uncomment and modify these values in the Insights Client Configuration in order to be authorized to upload::

    cd insights-client
    vim etc/insights-client.conf
    auto_config=False
    username=<your_username>
    password=<your_password>

**Note:** The username and password is based off your login for https://accesss.redhat.com/

Copy files into etc directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The insights-client requires the following files to be present inside of ``/etc/insights-client/``::

    cd ../insights-client
    sudo cp etc/insights-client.conf /etc/insights-client/
    sudo cp etc/cert-api.access.redhat.com.pem /etc/insights-client/

**Note:** You may need to create the ``/etc/insights-client`` directory.

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
    sudo cp etc/insights-client.conf /etc/insights-client/
