# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  # Use a standard box from the Vagrant Atlas
  config.vm.box = "ubuntu/trusty64"
  #config.vm.box = "deb/jessie-amd64"
  #config.vm.box = "ubuntu/ubuntu-15.04-snappy-core-stable"

  # Use the plugin vagrant-vbguest to auto-update the VirtualBox Guest Additions
  config.vbguest.auto_update = true
  config.vbguest.auto_reboot = true

  #Provision the machine using the puppet
  config.vm.provision "shell", inline: "apt-get -y install puppet"
  config.vm.provision :puppet do |puppet|
    puppet.manifests_path = "puppet/manifests"
    puppet.module_path = "puppet/modules"
    puppet.options = ["--verbose"]
  end
end
