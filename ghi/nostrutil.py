import re

import bech32

EMBED_RE = re.compile('nostr:([0-9a-z]+)')

def parse_tlv(data):
    try:
        rv = {}
        ptr = 0
        while ptr < len(data):
            t = data[ptr]
            l = data[ptr + 1]
            if t not in rv:
                rv[t] = []
            rv[t].append(data[ptr + 2:ptr + 2 + l])
            ptr += 2 + l
        return rv
    except IndexError:
        return None

def embeds_to_tags(content):
    '''
    Returns 'p' tags for embedded user profiles, and a set of relays extracted
    from nprofiles.
    '''
    tags = []
    relays_out = set()
    for match in EMBED_RE.finditer(content):
        embed = match.group(1)
        (hrp, data, spec) = bech32.bech32_decode(embed, 1000)
        if hrp is None or data is None or spec is None:
            continue # no valid bech32
        data = bytes(bech32.convertbits(data, 5, 8, False))

        if hrp == 'nprofile':
            tlv = parse_tlv(data)
            if tlv is None or 0x00 not in tlv or len(tlv[0x00][0]) != 32:
                continue # no valid tlv, no key, or invalid-length key
            key = tlv[0x00][0].hex()
            relays = [relay.decode('utf8') for relay in tlv.get(0x01, [])]
            if relays: # if relay supplied, specify the first one
                tags.append(['p', key, relays[0]])
            else: # no relay supplied
                tags.append(['p', key])

            relays_out.update(relays)
        elif hrp == 'npub':
            if len(data) != 32:
                continue
            tags.append(['p', data.hex()])

    return tags, relays_out

if __name__ == '__main__':
    print(embeds_to_tags('[test] Merged PR from laanwj (nostr:nprofile1qqsq4gu7tthengqq577mpdyezkxf90z25g8mvkf355ks2k67km0lwwqpzdmhxue69uhkummnw3ezu7psvchx7un8zn5kcn nostr:npub1p23eukh0nxsqpfaakz6fj9vvj27y4gs0kevnrffdq4d4adkl7uuq7crnl6): pr2 https://github.com/laanwj/test/pull/2'))
    print(embeds_to_tags('[test] Merged PR from laanwj (nostr:nprofile1qqsq4gu7tthengqq577mpdyezkxf90z25g8mvkf355ks2k67km0lwwqpz3mhxue69uhhyetvv9ujuerpd46hxtnfdur2ev7c): pr5 https://github.com/laanwj/test/pull/5'))
