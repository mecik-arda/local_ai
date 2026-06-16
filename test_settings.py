import local_ai
c = local_ai.load_config()
orig = c.get('cyberpuf_enabled', False)
print('Original:', orig)
c['cyberpuf_enabled'] = not orig
local_ai.save_config(c)
c2 = local_ai.load_config()
print('Toggled:', c2.get('cyberpuf_enabled'))
c2['cyberpuf_enabled'] = orig
local_ai.save_config(c2)
print('Restored:', local_ai.load_config().get('cyberpuf_enabled'))
