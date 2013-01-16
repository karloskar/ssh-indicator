#!/usr/bin/env python

import gobject
import gtk
import appindicator
from paramiko import SSHConfig
import os, re, pwd, subprocess, locale, datetime, time

class PontyIndicator():

    def __init__(self):

        self.home = os.path.expanduser('~')

        self.indicator = appindicator.Indicator("ssh-indicator",
            self.home + "/ssh-indicator/ssh-indicator.svg",
            appindicator.CATEGORY_APPLICATION_STATUS)
        self.indicator.set_status(appindicator.STATUS_ACTIVE)

        self.menu = gtk.Menu()

        active_hosts = self.active_hosts()
        hosts = self.load_ssh_config()

        for hostdict in hosts:
            if '*' not in hostdict['host']:
                host = hostdict['host']
                if 'user' not in hostdict:
                    hostdict['user'] = pwd.getpwuid(os.getuid()).pw_name
                if 'port' not in hostdict:
                    hostdict['port'] = '22'
                filename = '/tmp/ssh_mux_{0}_{1}_{2}'.format(
                        hostdict['hostname'],
                        hostdict['port'],
                        hostdict['user']
                    )
                active  = '+' if filename in active_hosts else '-'
                self.menu_item = gtk.MenuItem(host+' '+active)
                self.menu.append(self.menu_item)
                self.menu_item.connect("activate",
                        self.connect_host, 
                        host)
                self.menu_item.show()
        self.indicator.set_menu(self.menu)
        
    def poll_status(self):
        while True:
            self.update_status()
            time.sleep(60)

    def connect_host(self, w, host):
        subprocess.Popen(['ssh', '-nNT', host], stdout=subprocess.PIPE)
        time.sleep(3)
        self.update_status()

    def update_status(self):
        host_lookup = {}
        active_hosts = self.active_hosts()
        hosts = self.load_ssh_config()
        for hostdict in hosts:
            if '*' not in hostdict['host']:
                host = hostdict['host']
                if 'user' not in hostdict:
                    hostdict['user'] = pwd.getpwuid(os.getuid()).pw_name
                if 'port' not in hostdict:
                    hostdict['port'] = '22'
                filename = '/tmp/ssh_mux_{0}_{1}_{2}'.format(
                        hostdict['hostname'],
                        hostdict['port'],
                        hostdict['user']
                    )
                active  = '+' if filename in active_hosts else '-'
                host_lookup[host] = active
        for x in self.menu:
            if x.get_child():
                parts = x.get_child().get_label().split(' ')
                if len(parts) > 1:
                    x.get_child().set_text(parts[0]+' '+host_lookup[parts[0]])

    def load_ssh_config(self):
        p = SSHConfig()
        with open(os.path.expanduser('~/.ssh/config')) as f:
            p.parse(f)
        hosts = p.__dict__['_config']
        return hosts

    def active_hosts(self):
        active = []
        # TODO get the date and time for the mux file, parse the ControlPath
        ls_tmp = subprocess.Popen(['ls', '-l', '/tmp'], stdout=subprocess.PIPE)
        for line in ls_tmp.stdout.readlines():
            if 'ssh_mux' in line:
                filename = line.split(' ')
                filename = "/tmp/"+"".join(filename[-1:]).rstrip()
                dt_buf = subprocess.Popen(
                        ['stat', '-c', '%y', filename], 
                        stdout=subprocess.PIPE
                    )
                dt = "".join(dt_buf.stdout.read().split('.')[0])
                dt_obj = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
                dt_diff = datetime.datetime.today()-dt_obj
                if divmod(dt_diff.days*86400+dt_diff.seconds, 60)[0] < 120:
                    active.append(filename)
        return active

if __name__ == "__main__":
    ponty_indicator = PontyIndicator()
    gtk.main()
    ponty_indicator.poll_status()
