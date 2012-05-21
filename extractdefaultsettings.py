import shelve

COMMON_KEYS = [
    'version',
    'APISettings:chdk'
]

input = shelve.open(r'c:\users\oren\scanmanager\scanmanager.settings','r')
output = shelve.open(r'scanmanager.settings.default','c')

for k in COMMON_KEYS:
    output[k] = input[k]

input.close()
output.close()

print 'Extraction of default settings completed'