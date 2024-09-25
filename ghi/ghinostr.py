import hashlib
import json
import logging
import os
import time

try:
    import secp256k1
    import websocket
except ImportError:
    pass

from nostrutil import embeds_to_tags

def sendMessages(pool, messages):
    error = False
    sk = secp256k1.PrivateKey(bytes.fromhex(pool.nostrPrivKey))
    public_key = sk.pubkey.serialize()[1:].hex()

    for content in messages:
        tags, relays = embeds_to_tags(content)
        event = {
            'pubkey': public_key,
            'created_at': int(time.time()),
            'kind': 1,
            'tags': tags,
            'content': content,
        }

        data = [0, event['pubkey'], event['created_at'], event['kind'], event['tags'], event['content']]
        data_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        event['id'] = hashlib.sha256(data_str.encode()).hexdigest()

        sig = sk.schnorr_sign(bytes.fromhex(event['id']), None, raw=True)
        event['sig'] = sig.hex()

        message = json.dumps(['EVENT', event])

        # add our own configured relays, in addition to pinged user's relays
        relays.update(pool.nostrRelays)

        # send to all relays
        logging.info(f"Nostr - notifying relays {','.join(relays)}")
        for url in relays:
            try:
                relay = websocket.create_connection(url)
                relay.send(message)
            except Exception as e: # Just try the next one
                logging.error(f"Nostr - There was an error sending to relay {url}: {e}")
                error = True

    if error:
        resultMessage = "Nostr - There was a problem sending messages to Nostr"
    else:
        resultMessage = "Nostr - Successfully sent {} messages.".format(len(messages))
    logging.info(resultMessage)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "success": True,
            "message": resultMessage
        })
    }

