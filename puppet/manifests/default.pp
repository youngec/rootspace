class { "apt":
  update => {
    frequency => "daily",
  }
}

class { "locales":
  default_locale => "en_US.UTF-8",
  locales => [ "en_US.UTF-8 UTF-8", "de_CH.UTF-8 UTF-8" ],
}

class { "timezone":
  timezone => "UTC",
}

class apt-upgrade {
  exec { "apt-upgrade":
    command => "apt-get --quiet --yes --fix-broken upgrade",
    path => "/usr/bin:/usr/sbin:/bin:/usr/local/bin:/usr/local/sbin:/sbin",
    require => [Class["apt"], Class["locales"], Class["timezone"]],
  }
}

class apt-autoremove {
  exec { "apt-autoremove":
    command => "apt-get --yes autoremove",
    path => "/usr/bin:/usr/sbin:/bin:/usr/local/bin:/usr/local/sbin:/sbin",
    require => Class["apt-upgrade"]
  }
}

class system-essential {
  package { ["build-essential", "git", "python3", "python3-dev", "libsdl2-2.0-0", "libsdl2-ttf-2.0-0" ]:
    ensure => "latest",
    require => [Class["apt-upgrade"], Class["apt-autoremove"]],
  }
}

class pip3 {
  exec { "pip3":
    command => "curl https://bootstrap.pypa.io/get-pip.py | python3",
    path => "/usr/bin",
    require => Class["system-essential"],
  }
  exec { "pip3-upgrade":
    command => "pip3 install --upgrade pip setuptools",
    path => ["/usr/bin", "/usr/local/bin"],
    require => Exec["pip3"],
  }
  exec { "wheel":
    command => "pip3 install wheel",
    path => ["/usr/bin", "/usr/local/bin"],
    require => Exec["pip3-upgrade"],
  }
}

class rootspace {
  exec { "rootspace":
    command => "pip3 install -e /vagrant",
    path => ["/usr/bin", "/usr/local/bin"],
    require => [Class["system-essential"], Class["pip3"]],
  }
}

include apt
include locales
include timezone
include apt-upgrade
include apt-autoremove
include system-essential
include pip3
include rootspace

