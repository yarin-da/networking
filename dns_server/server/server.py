import sys
import socket
import time


# write our domain:ip:ttl table into a file 
def write_file(filename, table):
    try:
        output_file = open(filename, 'w')
    
        for line in table:
			# convert a line into a string (that contains 'systime')
            string = to_output_format(line, True)
            output_file.write(string + '\n')
    finally:
        output_file.close()


# we want to convert a line in our table to a string
# we may want to ignore 'systime' (e.g. when we send a message over the network)
# we may also want to include 'systime' (e.g. when we write to a file)
def to_output_format(line, systime=False):
    response = '{},{},{}'.format(line['domain'], line['ip'], line['ttl']) 
    if systime:
        return '{},{}'.format(response, line['systime']) 
    return response


# returns True if the line's ttl has expired
# special case: -1, means that this line is static and therefore never expires
def has_ttl_expired(line):
    if line['systime'] == -1:
        return False

    time_elapsed = time.time() - line['systime']
    return time_elapsed >= line['ttl']


# find a line in our table (search by domain)
def find_line(table, domain):
    for line in table:
		# return the index of the line that matches 'domain'
        if line['domain'] == domain:
            return table.index(line)
    # return error value - domain not found
    return -1


# add a line to the table
# extract the string's information into multiple variables
def add_to_table(table, string, reading_file=False):
    # default systime - used for static lines
	systime = -1
   
    content = string.rstrip().split(',')        
    params = len(content)

	# string must contain a systime parameter
    if params == 4:
        systime = float(content[3])
	# string came from our parent, which means it is now learned by us
	# so we set its systime to right now
    elif not reading_file:
        systime = time.time()

    domain = content[0]
    ip = content[1]
    ttl = int(content[2])

	# combine all parameters into a dictionary and add it to our table
    table.append({'domain': domain, 'ip': ip, 'ttl': ttl, 'systime': systime})


# read an input file and initialize a table
def read_input_file(filename):
    try:
        ips_file_read = open(ips_filename, 'r')
        ips_table = []
        for line in ips_file_read:
			# we pass True to make sure we treat it as a static line
            add_to_table(ips_table, line, True)
        return ips_table
    finally:
        ips_file_read.close()


# read args
my_port = int(sys.argv[1])
parent_ip = sys.argv[2]
parent_port = int(sys.argv[3])
ips_filename = sys.argv[4]

# we have a parent is both args aren't -1
has_parent = (parent_ip != '-1') and (parent_port != -1)

# init socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('', my_port))

# init table
ips_table = read_input_file(ips_filename)

while True:
	# read a request
    data, addr = s.recvfrom(1024)
    user_request = data.decode('utf-8')
        
    response = ''
    ttl_expired = False

	# get the line that matches the domain
    line_index = find_line(ips_table, user_request)
    line_found = (line_index != -1)

	# if we did find the line, we must make sure its ttl is not expired
    if line_found:
        ttl_expired = has_ttl_expired(ips_table[line_index])

    ask_parent = has_parent and ((not line_found) or ttl_expired)
    if ask_parent:
		# request the domain from the parent
        s.sendto(bytes(user_request, 'utf-8'), (parent_ip, parent_port))
        # receive the parent's answer
		parent_data, parent_addr = s.recvfrom(1024)
        parent_response = parent_data.decode('utf-8')
        response = parent_response

		# if the domain already exists in our table
        if ttl_expired:
            ips_table.remove(ips_table[line_index])

		# add the parent's answer to our table
        add_to_table(ips_table, response)
		# update the file to make sure we remember the answer
        write_file(ips_filename, ips_table)
	# we can immediately answer the client
    else:
        response = to_output_format(ips_table[line_index])

	# send the answer to the client
    s.sendto(bytes(response, 'utf-8'), addr)

