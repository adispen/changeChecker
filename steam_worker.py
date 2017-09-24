import logging
import gevent
from binascii import hexlify
from steam import SteamClient
from steam.core.msg import MsgProto
from steam.enums.emsg import EMsg
from steam.util import proto_to_dict
import vdf

LOG = logging.getLogger("Steam Worker")

class SteamWorker(object):
    def __init__(self):
	self.logged_on_once = False
	self.logon_details = {}

	self.steam = client = SteamClient()
	client.set_credential_location(".")

	@client.on("error")
	def handle_error(result):
	    LOG.info("Logon result: %s", repr(result))

	@client.on("channel_secured")
	def send_login():
	    if client.relogin_available:
		client.relogin()
	    else:
		client.login(**self.logon_details)
		self.logon_details.pop('auth_code', None)
		self.logon_details.pop('two_factor_code', None)

	@client.on("connected")
	def handle_connected():
	    LOG.info("Connected to %s", client.current_server_addr)

	@client.on("reconnect")
	def handle_reconnect(delay):
	    LOG.info("Reconnect in %ds...", delay)

	@client.on("disconnected")
	def handle_disconnect():
	    LOG.info("Disconnected.")

	    if self.logged_on_once:
		LOG.info("Reconnecting...")
		client.reconnect(maxdelay=30)

	@client.on("auth_code_required")
	def auth_code_prompt(is_2fa, mismatch):
	    if mismatch:
		LOG.info("Previous code was incorrect")

	    if is_2fa:
		code = raw_input("Enter 2FA Code: ")
		self.logon_details['two_factor_code'] = code
	    else:
		code = raw_input("Enter Email Code: ")
		self.logon_details['auth_code'] = code

	    client.connect()

	@client.on("logged_on")
	def handle_after_logon():
	    self.logged_on_once = True

	    LOG.info("-"*30)
	    LOG.info("Logged on as: %s", client.user.name)
	    LOG.info("Community profile: %s", client.steam_id.community_url)
	    LOG.info("Last logon: %s", client.user.last_logon)
	    LOG.info("Last logoff: %s", client.user.last_logoff)
	    LOG.info("-"*30)


    def start(self, username, password):
	self.logon_details = {
		'username': username,
		'password': password,
		}

	self.steam.connect()
	self.steam.wait_event('logged_on')

    def close(self):
	if self.steam.connected:
	    self.logged_on_once = False
	    LOG.info("Logout")
	    self.steam.logout()

    def get_change_number(self, appids=None):
        if not appids:
            appids = []
        else:
            appids = [appids]

        packageids = []

	resp = self.steam.send_job_and_wait(MsgProto(EMsg.ClientPICSProductInfoRequest),
		{
		    'apps': map(lambda x: {'appid': x}, appids),
		    'packages': map(lambda x: {'packageid': x}, packageids),
		    },
		timeout=10
		)

	if not resp: return {}

	resp = proto_to_dict(resp)

	for app in resp.get('apps', []):
	    app['appinfo'] = vdf.loads(app.pop('buffer').rstrip('\x00'))['appinfo']
	    app['sha'] = hexlify(app['sha'])
	for pkg in resp.get('packages', []):
	    pkg['appinfo'] = vdf.binary_loads(pkg.pop('buffer')[4:])[str(pkg['packageid'])]
	    pkg['sha'] = hexlify(pkg['sha'])

	return resp['apps'][0]['change_number']
