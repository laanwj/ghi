import codecs
import json
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_VERSION='2022-11-28'
API_URL='https://api.github.com'

def get(req_url, ghtoken=None):
    try:
        req = Request(API_URL + req_url)
        req.add_header('Accept', 'application/vnd.github+json')
        req.add_header('X-GitHub-Api-Version', API_VERSION)
        if ghtoken is not None:
            req.add_header('Authorization', 'token ' + ghtoken)

        reader = codecs.getreader('utf-8')
        response = urlopen(req)
        return json.load(reader(response))
    except (HTTPError, json.decoder.JSONDecodeError):
        return None

NOSTR_RE = re.compile('^(nprofile|npub)[0-9a-z]+$')

def get_socials(user, ghtoken=None):
    '''
    Get various socials from user's github profile that we might want to use in
    the rest of the bot.
    '''
    ret = {
        'mastodon': None,
        'nostr': None,
    }
    accounts = get(f'/users/{user}/social_accounts', ghtoken)
    if accounts is None: # in case of HTTP failure, we'll just return no socials
        accounts = []
    for rec in accounts:
        url = urlparse(rec['url'])
        components = url.path.split('/')
        if rec['provider'] == 'mastodon':
            if components[1].startswith('@'):
                ret['mastodon'] = components[1] + '@' + url.netloc
        else: # possibly nostr
            # netloc will probably be njump.me, but we'll handle other URLs just in case
            if NOSTR_RE.match(components[1]):
                ret['nostr'] = components[1]
    return ret

if __name__ == '__main__':
    socials = get_socials('laanwj')
    userinfo = f" (nostr:{socials['nostr']})" if socials['nostr'] is not None else ""
    print(userinfo)
