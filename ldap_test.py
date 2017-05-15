import os
import sha
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mso_portal.settings')

# import needed modules
import ldap
import ldap.modlist as modlist

from base64 import b64encode

# Open a connection
l = ldap.initialize("ldap://127.0.0.1")

# Bind/authenticate with a user with apropriate rights to add objects
l.simple_bind_s("cn=admin,dc=ldap,dc=portal,dc=com", "administrator")

# The dn of our new entry/object
dn="cn=python_test,dc=ldap,dc=portal,dc=com" 

ctx = sha.new("python") 
hash = "{SHA}" + b64encode(ctx.digest())

# A dict to help build the "body" of the object
attrs = {}
attrs['uid'] = ['python_test']
attrs['uidNumber'] = ['4999']
attrs['gidNumber'] = ['100']
attrs['objectclass'] = ['inetOrgPerson','organizationalPerson','person','posixAccount','top']
attrs['cn'] = 'python_test'
attrs['sn'] = 'python_test'
attrs['userPassword'] = hash
#attrs['description'] = 'test_python_user'
attrs['homeDirectory'] = '/home/users/python_test'

# Convert our dict to nice syntax for the add-function using modlist-module
ldif = modlist.addModlist(attrs)

# Do the actual synchronous add-operation to the ldapserver
l.add_s(dn,ldif)

# Its nice to the server to disconnect and free resources when done
l.unbind_s()
