#!/usr/bin/python
# -*- coding: utf-8 -*-

#    File name: new-client.py
#    Author: Maxime Berthault (Maxou56800)
#    Mail: contact@maxou56800.fr
#    Date created: 03/05/2014
#    Python Version: 2.7

import os
import crypt
import sys
import string
import random
import pwd
import fileinput
from email.mime.text import MIMEText
from subprocess import Popen, PIPE

script_version = "0.4"
date_last_modified = "03/05/2014"

logs = ""


def displayheader():
    print "new-client.py v%s developped by Maxou56800.\nLast edit: %s\n" % ( script_version, date_last_modified )

def help():
    print """Usage: python new-client.py [options]

Options:
  --option            add-user/add-domain/remove-all/remove-domain
  --client            Specify the name the client
  --domain            Specify domain(s) to add

Exemples:
  Add the client maxou56800 with domains maxou56800.fr/.net...
    python new-client.py --option=add-user --client=maxou56800
    python new-client.py --option=add-domain --client=maxou56800 --domain=maxou56800.fr
    python new-client.py --option=remove-domain --client=maxou56800 --domain=maxou56800.fr
    python new-client.py --option=remove-all --client=maxou56800 --domain=maxou56800.fr,kernel.org

"""
 
def pwgen(size=16, chars=string.ascii_letters + string.digits):
    """ 
    Howto: password = pwgen() 
    """
    return ''.join(random.choice(chars) for x in range(size))

def createuser(username, password):
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

def deleteuser(username):
    """
    Remove Unix User with Homedir
    """
    global logs 
    try:
        pwd.getpwnam(username)
        os.system("/usr/sbin/userdel %s --remove" % (username))              
    except KeyError:
        logs += "\nThe user does not exist." 
    

def adddomainfolders(username, domains):
    """
    Add domains folders
    """
    global logs
    try:
        pwd.getpwnam(username)
        for domain in domains:
            if os.path.exists("/home/%s/%s" % (username, domain)) == False:
                os.mkdir("/home/%s/%s" % (username, domain))
            else:
                logs += "\n/home/%s/%s folder already exists." % (username, domain)
            if os.path.isfile("/home/%s/%s/index.php" % (username, domain)) == False:
                os.system("echo 'Under construction.' > /home/%s/%s/index.php" % (username, domain))
            else:
                logs += "\n/home/%s/%s/index.php file already exists." % (username, domain)
            if os.path.exists("/home/%s/backup" % username) == False:
                os.mkdir("/home/%s/backup" % username)
            else:
                logs += "\n/home/%s/backup folder already exists." % username
            if os.path.exists("/home/%s/backup/%s" % (username, domain)) == False:
                os.mkdir("/home/%s/backup/%s" % (username, domain))
            else:
                logs += "\n/home/%s/backup/%s folder already exists." % (username, domain)
            os.system("/bin/chown %s:%s /home/%s/%s -R && /bin/chown %s:%s /home/%s/backup -R" % (username, username, username, domain, username, username, username))
               
    except KeyError:
        logs += "\nThe user does not exist."
        password = Inconue
        sendmail(username, password, domains, logs)
        exit()
        

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

def removehostfile(hostname):
    """
    Update Hosts file for add domain with local ipaddress
    """
    global logs
    ipaddress = "127.0.0.1"
    if ('127.0.0.1\t%s' % hostname in open('/etc/hosts').read()) != True:
        logs += "\nThe domain %s does not exist in /etc/hosts." % (hostname)
    else:
        for line in fileinput.input("/etc/hosts",inplace =1):
            line = line.strip()
            if not hostname in line:
                print line


def genvirtualhost(username, domains):
    """
    Create and enable VirtualHost in /etc/apache2/sites-available/
    """
    global logs
    if os.path.isfile("/etc/apache2/sites-available/%s" % domains[0]) == False:
        outputfile = open('/etc/apache2/sites-available/%s' % domains[0], 'a')
        entry = """<VirtualHost *:80>
        ServerAdmin contact@maxou56800.fr
        ServerName %s
        ServerAlias %s
        DocumentRoot /home/%s/%s
        <Directory />
            Options FollowSymLinks +Indexes
            IndexIgnore *
            IndexOptions +FancyIndexing
            #AllowOverride None
            AllowOverride All 
        </Directory>
        ErrorLog /home/%s/apache_error.log
        LogLevel warn
        CustomLog ${APACHE_LOG_DIR}/access.log combined
    </VirtualHost>""" % (domains[0], ' '.join(domains), username, domains[0], username)
        outputfile.writelines(entry)
        outputfile.close()
        os.system("/usr/sbin/a2ensite %s" % domains[0])
    else:
        logs += "\n/etc/apache2/sites-available/%s already exists." % (domains[0])

def rmvirtualhost(domain):
    """
    Create and enable VirtualHost in /etc/apache2/sites-available/
    """
    global logs
    if os.path.isfile("/etc/apache2/sites-available/%s" % domain) == True:
        os.system("/usr/sbin/a2dissite %s" % domain)
        try:
            os.remove("/etc/apache2/sites-available/%s"%(domain))
        except OSError:
            print "No such file or directory: '/etc/apache2/sites-available/%s'" % (domain)
            logs += "\nNo such file or directory: '/etc/apache2/sites-available/%s'." % (domain)
    else:
        logs += "\n/etc/apache2/sites-available/%s does not exists." % (domain)

def sendmail(username, password, domains, logs):
    """
    Send mail with logs to admins
    """
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
    if len(sys.argv) < 2:
        help()
        sys.exit(1)

    for command in sys.argv[1:]:
        if ("--help" or "?") in command.lower():
            help()
            exit()
        if ("--option" in command.lower()):
            option = command.lower().split("=")[1]            
        elif ( "--client=" in command.lower()):
            username = command.lower().split("=")[1]
        elif ( "--domain=" in command.lower()):
            domains = command.lower().split("=")[1].split(",")
        else:
            print "Error in params, check the exemple below...\n"
            help()
            sys.exit(1)

    if option == "add-user":
        password = pwgen()
        print "-- Note --\n\tUsername: %s\n\tPassword: %s\n----\n" % ( username, password )

        # Create Unix user
        def info_init():
            print("[>] Create Unix user... "),
        info_init()
        createuser(username, password)
        print "[OK]"
    elif option == "add-domain":
        # Make domain files and folders
        def info_init():
            print("[>] Make domain folders and files... "),
        adddomainfolders(username, domains)
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

        genvirtualhost(username, domains)
        print "[OK]"
    elif option == "remove-all":
        deleteuser(username)
        for domain in domains:
            removehostfile(domain)
            rmvirtualhost(domain)

    else:
        print "Error in option."
        exit()

    if ("domain" or "remove-all") in option:
        # Create and enable virtualhost file
        def info_init():
            print("[>] Restart apache2 service... "),
        info_init()
        os.system("/etc/init.d/apache2 reload &")
        #restartapache2()
        print "[OK]"


    # Send mail
    def info_init():
        print("[>] Send mail... "),
    info_init()
    if option == "add-user":
        domains = "aucun"
        sendmail(username, password, domains, logs)
    else:
        "Don't need to send mail."
    print "[OK]"


    print "\nAll be right."

if __name__ == '__main__':
    main()
