VAGRANTFILE_API_VERSION = "2"

# set docker as the default provider
ENV['VAGRANT_DEFAULT_PROVIDER'] = 'docker'

# disable parallellism so that the containers come up in order
ENV['VAGRANT_NO_PARALLEL'] = "1"
ENV['FORWARD_DOCKER_PORTS'] = "1"
# minor hack enabling to run the image and configuration trigger just once
ENV['VAGRANT_EXPERIMENTAL']="typed_triggers"

unless Vagrant.has_plugin?("vagrant-docker-compose")
  system("vagrant plugin install vagrant-docker-compose")
  puts "Dependencies installed, please try the command again."
  exit
end

# Names of Docker images built:
ZOONODE_IMAGE  = "dshw/zookeeper:0.1"
BACKEND_IMAGE  = "dshw/client:0.1"

# Node definitions

CLIENTS  = { :nameprefix => "client-",  # backend nodes get names: client-1, client-2, etc.
              :subnet => "10.0.1.",
              :ip_offset => 100,  # backend nodes get IP addresses: 10.0.1.101, .102, .103, etc
              :image => BACKEND_IMAGE }

# Number of "layers" of our cache tree:
TREE_LEVEL = 3

PARENT_ADDRESS = "10.0.1.55"

# Common configuration
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    config.trigger.before :up, type: :command do |trigger|
        trigger.name = "Build docker images"
        trigger.ruby do |env, machine|
            puts "Building node image:"
            `docker build client -t "#{BACKEND_IMAGE}"`

            # Build Zoonode image:
            puts "Building Zoonode image:"
            `docker build zookeeper -t "#{ZOONODE_IMAGE}"`
        end
    end

    config.ssh.insert_key = false

    # Definition of Zoonode
    config.vm.define "zoonode" do |s|
        s.vm.network "private_network", ip: "#{CLIENTS[:subnet]}100"
        s.vm.hostname = "zoonode"
        s.vm.network "forwarded_port", guest: 80, host: 5000, host_ip: "0.0.0.0", auto_correct: true
        s.vm.provider "docker" do |d|
          d.image = ZOONODE_IMAGE
          d.name = "zoonode"
          d.has_ssh = true
        end
        s.vm.post_up_message = "Node 'zoonode' up and running. You can access the node with 'vagrant ssh zoonode'}"
    end

    CLIENTS_COUNT = (2**TREE_LEVEL) - 1

    puts "The tree with #{TREE_LEVEL} layers will have #{CLIENTS_COUNT} nodes in total"
    # Definition of root node
    root_ip_addr = PARENT_ADDRESS
    root_name = "root#{CLIENTS[:nameprefix]}1"
    # Definition of BACKEND
    config.vm.define root_name do |root|
        root.vm.network "private_network", ip: root_ip_addr
        root.vm.network "forwarded_port", guest: 80, host: 5000, host_ip: "0.0.0.0", auto_correct: true
        root.vm.hostname = root_name
        root.vm.provider "docker" do |d|
            d.image = CLIENTS[:image]
            d.name = root_name
            d.has_ssh = true
            d.env = {
               "PARENT_NODE" => "ROOT",
               "NODE_ADDRESS" => "#{root_ip_addr}",
               "ZOO_SERVERS" => "#{CLIENTS[:subnet]}100",
               "CLIENT_ID" => "1",
               "CLIENT_COUNT" => "#{CLIENTS_COUNT + 1}",
               "ADDRESS_OFFSET" => "#{CLIENTS[:ip_offset]}",
               "BASE_SUBNET" => "#{CLIENTS[:subnet]}"
                 }
        end
        root.vm.post_up_message = "Node #{root_name} up and running. You can access the node with 'docker exec -it  #{root_name} bash'}"
    end

    # Definition of N backends
    (2..CLIENTS_COUNT).each do |i|
        node_ip_addr = "#{CLIENTS[:subnet]}#{CLIENTS[:ip_offset] + i}"
        node_name = "#{CLIENTS[:nameprefix]}#{i}"
        # Definition of BACKEND
        config.vm.define node_name do |s|
            s.vm.network "private_network", ip: node_ip_addr
            s.vm.network "forwarded_port", guest: 80, host: 5000, host_ip: "0.0.0.0", auto_correct: true
            s.vm.hostname = node_name
            s.vm.provider "docker" do |d|
                d.image = CLIENTS[:image]
                d.name = node_name
                d.has_ssh = true
                d.env = {
                "PARENT_NODE" => root_ip_addr,
                "NODE_ADDRESS" => "#{node_ip_addr}",
                "ZOO_SERVERS" => "#{CLIENTS[:subnet]}100"
                }
            end
            s.vm.post_up_message = "Node #{node_name} up and running. You can access the node with 'docker exec -it #{node_name} bash'}"
        end
    end
end
# EOF
