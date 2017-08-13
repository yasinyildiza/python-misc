########################################
###           INSTALLATION           ###
########################################

********************
***    SERVER    ***
********************

------------
Prerequisite
------------
    - python2.7 => https://www.python.org/downloads/

---------------
Python packages
---------------
    - lxml
    - mysql-connector
    - paramiko
    - psutil
    - pycrypto
    - sqlalchemy
    - sqlalchemy_utils

-----
Notes
-----

After installing python2.7 from the link provided above, go to the setup directory under "Source/setup".
By this way, you will be able to install all required Python packages with no additional effort.

1) run "get-pip.py" with admin privileges
    python get-pip.py

2) run "setup.py" for server with admin privileges
    python setup.py server

********************
***   DATABASE   ***
********************

------------
Prerequisite
------------
    - MySQL => http://dev.mysql.com/doc/refman/5.7/en/installing.html

-----
Notes
-----

After installing MySQL, follow these steps to complete database installation:

1) make sure that MySQL service is running.

2) create a clean database with "CREATE DATABASE" statement.
    for a sample database creation, go to "sql" directory under "Source/sql".
        mysql -u <username> -p < create.sql

    - run the command above on a command line.
    - replace <username> with your MySQL username.
    - enter your MySQL password if prompted.

    + this command will create a database with name 'MachineLogger'.
    + if you want, you can change the name from the create.sql script, and create a new database with that name.

3) after creating database, you need to create the schema.
    for a sample database creation, go to "sql" directory under "Source/sql".
        mysql -u <username> -p <database> < create.sql

    - run the command above on a command line.
    - replace <username> with your MySQL username.
    - replace <database> with your MySQL database name (created in step 1)
    - enter your MySQL password if prompted.

********************
***    CLIENT    ***
********************

------------
Prerequisite
------------
    - python2.7 => https://www.python.org/downloads/
    - ssh server

---------------
Python packages
---------------
    - psutil
    - lxml
    - pycrypto
    - pypiwin32 (Windows only!)

-----
Notes
-----

After installing python2.7 from the link provided above, go to the setup directory under "Source/setup".
By this way, you will be able to install all required Python packages with no additional effort.
The script is able to detect the OS environment to select appropriate packages.

1) run "get-pip.py" with admin privileges
    python get-pip.py

2) run "setup.py" for client  with admin privileges
    python setup.py client

########################################
###           CONFIGURATION          ###
########################################

********************
***    SERVER    ***
********************

Server script has a configuration file in xml format.

You can find a sample xml config file for server at
    "Source/server/config.xml"


___config.xml___
<root>
    <srcpath value='../client/client.py' />
    <clients>
        <client ip='127.0.0.1' port='22' username='user' password='pass' mail='username@gmail.com' execpath='client.py' outpath='stat.bin' >
            <alert type='memory' limit='50%' />
            <alert type='cpu' limit='20%' />
        </client>
    </clients>
    <database name='MachineLogger' username='mysqluser' password='mysqlpass' host='127.0.0.1' port='3306' />
    <mailer ip='smtp.googlemail.com' port='587' timeout='30' username='server@gmail.com' password='mailpass' />
    <multithread enabled='true' />
</root>
___config.xml___

You need to provide path to this xml config file to the server script as the first command line argument

Here is the description of tags and attributes in the server xml configuration file.

<root>
    [Mandatory]
    root tag is used as a container for all of the server config tags.

<srcpath>
    [Mandatory]
    keeps the path to the client script that will be copied to remote client machine in "value" attribute.

    ----------
    attributes
    ----------
        [Mandatory] "value": keeps the path value to the client script either as an absolute path or a relative path to the path where the server script is triggered.

<clients>
    [Mandatory]
    keeps the client list under child "client" tags.

<client>
    [Optional]
    keeps the information of a remote client machine, always as a child of "clients".

    ----------
    attributes
    ----------
        [Mandatory] "ip"      : remote machine ip.
        [Mandatory] "port"    : remote machine ssh port (in most cases it is 22).
        [Mandatory] "username": remote machine ssh username.
        [Mandatory] "password": remote machine ssh pasword.
        [Mandatory] "mail"    : mail address which will be used to send an alert mail when a cpu and/or memory usage exceeds the predefined limits.
        [Mandatory] "execpath" : path on the remote machine to which the client script will be copied and under which the client script will be triggered
        [Mandatory] "outpath" : path on the remote machine to which the client script will write the output

<alert>
    [Optional]
    keeps the critical limit information for memory or cpu usage.

    ----------
    attributes
    ----------
        [Mandatory] "type":  type of the usage (memory/usage).
        [Mandatory] "limit": percentage limit ('%' sign can be used optinally when writing the value, config file parser can handle both cases).

<database>
    [Mandatory]
    keeps the database credentials

    ----------
    attributes
    ----------
        [Mandatory] "name"    : name of the database that statistics and log records will be written by server.
        [Mandatory] "username": database username.
        [Mandatory] "password": database password.
        [Mandatory] "host"    : database host ip ("localhost" or "127.0.0.1" if server and database is running on the same machine).
        [Mandatory] "port"    : database host port (3306 for MySQL in most of the cases)

<mailer>
    [Mandatory]
    keeps the mail facility credentials

    ----------
    attributes
    ----------
        [Mandatory] "ip"      : smtp mail server ip address ("localhost" or "127.0.0.1" if server and mail aerver is running on the same machine).
        [Mandatory] "port"    : smtp mail server port (587 for googlemail)
        [Mandatory] "timeout" : timeout duration when connecting to the mail server
        [Mandatory] "username": mail server username (also will be shown on FROM field in mails).
        [Mandatory] "password": mail server password.

<multithread>
    [Optional]
    enables/disables multithreading while running client scripts. this provides parallel execution of clients and performance improvement.

    if this tag does not exist at all in the config file, it means multithread mode is disabled.

    the only way to enable the mode is to add the tag into the config file and set the "enabled" attribute to "true"

    ----------
    attributes
    ----------
        [Optional]  "enabled"      : takes "true" or "false" values. values other "true" are considered as "false". if the attribute does not exists at all, it means it is "false".

********************
***    CLIENT    ***
********************

On client side, make sure that the machine is accessible via ssh.

########################################
###            ASSUMPTIONS           ###
########################################

1) required packages, programs are installed and required configurations are performed on client and server side before running the scripts.
2) if server configuration has an error (field/tag missing/invalid, xml parsing error, no access to database/mail server etc.), execution stops.
3) given a list of clients, if an error occurs on one of them on any step, skip that client and continue with the next one.
4) statistics values are read as floating numbers.
5) if an statistics value "IS EQUAL TO" or "GREATER THAN" the predefined limit, a mail is sent.
6) path on the remote machine where the client script will be triggered shall be defined per machine.

########################################
###            REQUIREMENTS          ###
########################################

All requirements are covered in the solution.

In addition, a logging mechanism added to server.

You can track server logs by tracking server.log file (log file name is given via command line argument) which will be created in the same directory where the script is triggered upon execution.

########################################
###               ISSUES             ###
########################################

I didn't encountered a serious issue other than those can be experienced in almost every development process.
The most challenging part, in my opinion, was the multi-platform support because it takes considerable time to setup the environment on a new machine.
Testing was a little bit hard for ssh connection cases especially when designing exception cases.

########################################
###              FEEDBACK            ###
########################################

The size of the project and the time given to complete it is fair enough to measure one's Python skills as well as programming skills from a broader aspect.

########################################
###              RUNNING             ###
########################################

As the client script will be triggered by the server script automatically on a remote machine, the only thing that the user should run is the server script.
Before running the script, please make sure that you have created a proper configuration file as described in the CONFIGURATION part of this document.

Server script takes three command line arguments:

1) configuration file path (mandatory)
2) log file path (mandatory)
3) log level (optional)
    default: info
    possible values: debug | info | warning | error | critical
    for further information on log levels, please refer to python logging package:
        https://docs.python.org/2/library/logging.html

sample run:
    python server.py config.xml server.log warning

########################################
###             UNIT TESTS           ###
########################################

Unit tests are provided for server and client scripts seperately.

If python "coverage" tool is installed on your environment, you can use the test_*.cmd scripts to run unit tests.

Coverage tool provides information on which lines are executed/covered during the test run.

Refer to "Coverage" sections of the following parts.

********************
***    SERVER    ***
********************

Before running server unit tests,

1) make sure that you have a valid/proper configuration file similar to one that is used while running the server script itself.
    -- you can even use the same configuration file for both the script and the unit tests.

2) copy the configuration file to the path:
    Source/server

3) name the configuration file as:
    test.config.xml

Then, you can run unit tests for server:

1) cd Source/server
2) run the command
    pyhton test_server.py

During the tests, there will some prints on the shell coming from server script.

When tests are completed, you will see the number of tests executed, and "OK" message indicating that all tests are successful.

If you see an error message and if no test is executed, please check the error logs on the shell, and check the configuration file (test.config.xml)

- The test script validates the structure and the data given by the configuration file.
- The test script checks the srcpath existence, database connection, database schema, mail server connection as well as client connection.
- If one of these checks fails, the script will terminate and no test case will run.

--------
Coverage
--------

1) cd Source/server
2) run test_server.cmd
3) cd Source/server/htmlcov
4) open index.html file in a browser

IMPORTANT: be sure that you have already installed coverage, i.e., pip install coverage

********************
***    CLIENT    ***
********************

You can run unit tests for client:

1) cd Source/client
2) run the command
    python test_client.py

--------
Coverage
--------

1) cd Source/client
2) run test_client.cmd
3) cd Source/client/htmlcov
4) open index.html file in a browser

IMPORTANT: be sure that you have already installed coverage, i.e., pip install coverage
