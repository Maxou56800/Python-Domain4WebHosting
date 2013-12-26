#!/usr/bin/python
# -*- coding: utf-8 -*-

#    File name: new-client.py
#    Author: Maxime Berthault (Maxou56800)
#    Mail: contact@maxou56800.fr
#    Date created: 23/12/2013
#    Python Version: 2.7

import os
import crypt
import sys
import string
import random
import pwd
from email.mime.text import MIMEText
from subprocess import Popen, PIPE

script_version = "0.4"
date_last_modified = "26/12/2013"

logs = ""


def displayheader():
    print "new-client.py v%s developped by Maxou56800.\nLast edit: %s\n" % ( script_version, date_last_modified )

def help():
    print """Usage: python new-client.py [options]

Options:
  --client            Specify the name the client
  --domain            Specify domain(s) to add

Exemples:
  Add the client maxou56800 with domains maxou56800.fr/.net...
    python new-client.py --client=maxou56800 --domain=maxou56800.fr,maxou56800.net,maxou56800.com
"""

def pwgen(size=16, chars=string.ascii_letters + string.digits):
    """ Howto: password = pwgen() """
    return ''.join(random.choice(chars) for x in range(size))

def createuser(username, password, domains):
    """
    Create Unix User with password
    """
    global logs
    encPass = crypt.crypt(password,"22")
    try:
        pwd.getpwnam(username)
        logs += "\nThe user already exists."       
    except KeyError:
        os.system("/usr/sbin/useradd -p %s -m %s" % (encPass, username))
    for domain in domains:
        if os.path.exists("/home/%s/%s" % (username, domain)) == False:
            os.system("mkdir /home/%s/%s" % (username, domain))
        else:
            logs += "\n/home/%s/%s folder already exists." % (username, domain)
        if os.path.isfile("/home/%s/%s/index.php" % (username, domain)) == False:
            os.system("echo 'Under construction.' > /home/%s/%s/index.php" % (username, domain))
        else:
            logs += "\n/home/%s/%s/index.php file already exists." % (username, domain)
        if os.path.exists("/home/%s/backup" % username) == False:
            os.system("mkdir /home/%s/backup" % username)
        else:
            logs += "\n/home/%s/backup folder already exists." % username
        if os.path.exists("/home/%s/backup/%s" % (username, domain)) == False:
            os.system("mkdir /home/%s/backup/%s" % (username, domain))
        else:
            logs += "\n/home/%s/backup/%s folder already exists." % (username, domain)
        os.system("chown %s:%s /home/%s/%s -R && chown %s:%s /home/%s/backup -R" % (username, username, username, domain, username, username, username))

def updatehostfile(hostname):
    """
    Update Hosts file for add domain with local ipaddress
    """
    global logs
    ipaddress = "127.0.0.1"
    if ('127.0.0.1\t%s' % hostname in open('/etc/hosts').read()) != True:
        outputfile = open('/etc/hosts', 'a')
        entry = "\n" + ipaddress + "\t" + hostname + "\n"
        outputfile.writelines(entry)
        outputfile.close()
    else:
        logs += "\nThe domain %s is already specified in /etc/hosts." % (hostname)

def genvirtualhost(username, domain):
    """
    Create and enable VirtualHost in /etc/apache2/sites-available/
    """
    global logs
    if os.path.isfile("/etc/apache2/sites-available/%s" % domain) == False:
        outputfile = open('/etc/apache2/sites-available/%s' % domain, 'a')
        entry = """<VirtualHost *:80>
        ServerAdmin contact@maxou56800.fr
        ServerName %s
        ServerAlias www.%s
        DocumentRoot /home/%s/%s
        ErrorLog /home/%s/apache_error.log
        LogLevel warn
        CustomLog ${APACHE_LOG_DIR}/access.log combined
    </VirtualHost>""" % (domain, domain, username, domain, username)
        outputfile.writelines(entry)
        outputfile.close()
        os.system("/usr/sbin/a2ensite %s" % domain)
    else:
        logs += "\n/etc/apache2/sites-available/%s already exists." % (domain)

def restartapache2():
    """
    Restart Apache2 service
    """
    os.system("/etc/init.d/apache2 reload &")

def sendmail(username, password, domains, logs):
    msg = MIMEText("-- Note --\n\tUsername: %s\n\tPassword: %s\n\tDomains: %s\n----\n-- Logs --\n%s" % ( username, password, domains, logs ))
    msg["From"] = "noreply@maxou56800.fr"
    msg["To"] = "maxou56800@gmail.com"
    msg["Subject"] = "New domain added to your server."
    p = Popen(["/usr/sbin/sendmail", "-t"], stdin=PIPE)
    p.communicate(msg.as_string())

def main():
    if os.geteuid() != 0:
        exit("You need to have root privileges to run this script.\nPlease try again, with root privileges. Exiting.")
    displayheader()

    # Check the number of argv
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        help()
        sys.exit(1)

    for command in sys.argv[1:]:
        if ( "--client=" in command.lower()):
            username = command.lower().split("=")[1]
        elif ( "--domain=" in command.lower()):
            domains = command.lower().split("=")[1].split(",")
        else:
            print "Error in params, check the exemple below...\n"
            help()
            sys.exit(1)

    password = pwgen()
    print "-- Note --\n\tUsername: %s\n\tPassword: %s\n\tDomains: %s\n----\n" % ( username, password, domains )

    # Create Unix user
    def info_init():
        print("[>] Create Unix user... "),
    info_init()
    createuser(username, password, domains)
    print "[OK]"

    # Edit /etc/host file
    def info_init():
        print("[>] Update host file... "),
    info_init()
    for domain in domains:
        updatehostfile(domain)
    print "[OK]"

    # Create and enable virtualhost file
    def info_init():
        print("[>] Create virtualhost file... "),
    info_init()
    for domain in domains:
        genvirtualhost(username, domain)
    print "[OK]"

    # Create and enable virtualhost file
    def info_init():
        print("[>] Restart apache2 service... "),
    info_init()
    restartapache2()
    print "[OK]"

    # Send mail
    def info_init():
        print("[>] Send mail... "),
    info_init()
    sendmail(username, password, domains, logs)
    print "[OK]"


    print "\nAll be right."

if __name__ == '__main__':
    main()
