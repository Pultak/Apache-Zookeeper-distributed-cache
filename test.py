from kazoo.client import KazooClient

zk = KazooClient(hosts="10.0.1.100")

zk.start()

path_queue = ["/"]
while len(path_queue) > 0:
    curr_path = path_queue.pop()
    print(f"Found node: {curr_path}")
    # begin the search for parent node
    data, stats = zk.get(curr_path)
    if stats.children_count > 0:
        children = zk.get_children(curr_path)
        for addr in children:
            # add new paths to queue for future search
            path_queue.append(f"{curr_path}/{addr}")

# Close the session
zk.stop()
