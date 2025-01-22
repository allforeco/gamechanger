from nacl.public import PrivateKey, PublicKey, SealedBox
#from nacl.encoding import URLSafeBase64Encoder
#from nacl.utils import random
from base64 import urlsafe_b64decode, urlsafe_b64encode
from .models import PubKey

class Crypto():
    ENC_MARKER = "@"
    ENC_SEPARATOR = ":"
    COOKIE_PREFIX = "gc_key_"
    KEYLEN = 5
    current_num = 0
    current_pub = None

    class WrongType(Exception):
        ...

    @staticmethod
    def bin_to_urlstr(bin):
        if not isinstance(bin, bytes):
            raise Crypto.WrongType()
        return urlsafe_b64encode(bin).decode('utf-8')
        #return URLSafeBase64Encoder.encode(bin).decode('utf-8')

    @staticmethod
    def urlstr_to_bin(urlstr):
        if not isinstance(urlstr, str):
            raise Crypto.WrongType()
        return urlsafe_b64decode(urlstr.encode('utf-8'))
        #return URLSafeBase64Encoder.decode(urlstr.encode('utf-8'))

    @staticmethod
    def gen_privkey_as_urlstr():
        privkey = Crypto.gen_privkey()
        priv_urlstr = Crypto.privkey_to_urlstr(privkey)
        print(f"gen:pk={privkey} urlstr={priv_urlstr}")
        Crypto.set_new_current_key(privkey)
        return (Crypto.current_num, priv_urlstr)

    @staticmethod
    def set_new_current_key(privkey):
        if not isinstance(privkey, PrivateKey):
            raise Crypto.WrongType()
        Crypto.current_pub = privkey.public_key
        Crypto.current_num = Crypto.commit_pubkey(Crypto.current_pub)

    @staticmethod
    def encrypt(val, pubkey):
        if not isinstance(pubkey, PublicKey):
            raise Crypto.WrongType()
        if not isinstance(val, str):
            raise Crypto.WrongType()
        print(f'ENIGMA ENCRYPTION PUBKEY={pubkey}')
        enigma = Crypto.get_enigma(pubkey)
        raw_val = val.encode('utf-8')
        print(f'raw_val={raw_val}')
        enc_val = urlsafe_b64encode(enigma.encrypt(raw_val)).decode('utf-8')
        print(f'enc_val={enc_val}')
        #enc_val = URLSafeBase64Encoder.encode(enigma.encrypt(raw_val)).decode('utf-8')
        return enc_val

    @staticmethod
    def decrypt(raw_val, privkey):
        if not isinstance(privkey, PrivateKey):
            raise Crypto.WrongType()
        if not isinstance(raw_val, bytes):
            raise Crypto.WrongType()
        print(f'ENIGMA DECRYPTION PRIVKEY={privkey}')
        enigma = Crypto.get_enigma(privkey)
        print(f'raw_val={raw_val}')
        bin_val = urlsafe_b64decode(raw_val)
        dec_val = enigma.decrypt(bin_val).decode('utf-8')
        print(f'dec_val={dec_val}')
        return dec_val

    @staticmethod
    def gen_privkey():
        return PrivateKey.generate()
    
    @staticmethod
    def get_public_key(privkey):
        if not isinstance(privkey, PrivateKey):
            raise Crypto.WrongType()
        return privkey.public_key

    @staticmethod
    def pubkey_to_urlstr(pubkey):
        if not isinstance(pubkey, PublicKey):
            raise Crypto.WrongType()
        return urlsafe_b64encode(pubkey._public_key).decode('utf-8')
        #return URLSafeBase64Encoder.encode(pubkey._public_key).decode('utf-8')
    
    @staticmethod
    def pubkeybytes_from_urlstr(urlstr):
        return urlsafe_b64decode(urlstr.encode('utf-8'))
        #return URLSafeBase64Encoder.decode(urlstr.encode('utf-8'))

    @staticmethod
    def pubkey_from_bytes(pubkeybytes):
        return PublicKey(pubkeybytes)

    @staticmethod
    def privkey_to_urlstr(privkey):
        return urlsafe_b64encode(privkey._private_key).decode('utf-8')
        #return URLSafeBase64Encoder.encode(privkey._private_key).decode('utf-8')

    @staticmethod
    def privkeybytes_from_urlstr(privkeystr):
        return urlsafe_b64decode(privkeystr.encode('utf-8'))
        #return URLSafeBase64Encoder.decode(privkeystr.encode('utf-8'))

    @staticmethod
    def privkey_from_bytes(privkeybytes):
        return PrivateKey(privkeybytes)

    @staticmethod
    def get_enigma(privkey):
        return SealedBox(privkey)

    @staticmethod
    def selftest5():
        print("SELFTEST 0")
        # Generate Bob's private key, as we've done in the Box example
        nskbob = Crypto.gen_privkey()
        npkbob = Crypto.get_public_key(nskbob)

        npkbobstr = Crypto.pubkey_to_urlstr(npkbob)
        npkbobraw = Crypto.pubkeybytes_from_urlstr(npkbobstr)
        npkbob2 = Crypto.pubkey_from_bytes(npkbobraw)

        nskbobstr = Crypto.privkey_to_urlstr(nskbob)
        nskbobraw = Crypto.privkeybytes_from_urlstr(nskbobstr)
        nskbob2 = Crypto.privkey_from_bytes(nskbobraw)
 
        # Alice wishes to send a encrypted message to Bob,
        # but prefers the message to be untraceable
        nsealed_box = Crypto.get_enigma(npkbob2)

        # This is Alice's message
        message = b"Kill all kittens"

        # Encrypt the message, it will carry the ephemeral key public part
        # to let Bob decrypt it
        nencrypted = nsealed_box.encrypt(message)

        print(nencrypted)

        nunseal_box = Crypto.get_enigma(nskbob2)
        # decrypt the received message
        nplaintext = nunseal_box.decrypt(nencrypted)
        print(nplaintext.decode('utf-8'))

    @staticmethod
    def selftest4():
        print("SELFTEST 0")
        # Generate Bob's private key, as we've done in the Box example
        skbob = PrivateKey.generate()
        nskbob = Crypto.gen_privkey()
        print(f"skbob={skbob}")
        pkbob = skbob.public_key
        npkbob = Crypto.get_public_key(nskbob)
        print(f"pkbob={pkbob} ")

        pkbobstr = urlsafe_b64encode(pkbob._public_key).decode('utf-8')
        #pkbobstr = URLSafeBase64Encoder.encode(pkbob._public_key).decode('utf-8')
        npkbobstr = Crypto.pubkey_to_urlstr(npkbob)
        print(f"pkbobstr={pkbobstr}")
        pkbobraw = urlsafe_b64decode(pkbobstr.encode('utf-8'))
        #pkbobraw = URLSafeBase64Encoder.decode(pkbobstr.encode('utf-8'))
        npkbobraw = Crypto.pubkeybytes_from_urlstr(npkbobstr)
        print(f"pkbobraw={pkbobraw}")
        pkbob2 = PublicKey(pkbobraw)
        npkbob2 = Crypto.pubkey_from_bytes(npkbobraw)

        skbobstr = urlsafe_b64encode(skbob._private_key).decode('utf-8')
        #skbobstr = URLSafeBase64Encoder.encode(skbob._private_key).decode('utf-8')
        nskbobstr = Crypto.privkey_to_urlstr(nskbob)
        print(f"skbobstr={skbobstr}")
        skbobraw = urlsafe_b64decode(skbobstr.encode('utf-8'))
        #skbobraw = URLSafeBase64Encoder.decode(skbobstr.encode('utf-8'))
        nskbobraw = Crypto.privkeybytes_from_urlstr(nskbobstr)
        print(f"skbobraw={skbobraw}")
        skbob2 = PrivateKey(skbobraw)
        nskbob2 = Crypto.privkey_from_bytes(nskbobraw)
 
        # Alice wishes to send a encrypted message to Bob,
        # but prefers the message to be untraceable
        sealed_box = SealedBox(pkbob2)
        nsealed_box = Crypto.get_enigma(npkbob2)

        # This is Alice's message
        message = b"Kill all kittens"

        # Encrypt the message, it will carry the ephemeral key public part
        # to let Bob decrypt it
        encrypted = sealed_box.encrypt(message)
        nencrypted = nsealed_box.encrypt(message)

        print(encrypted)
        print(nencrypted)

        unseal_box = SealedBox(skbob2)
        nunseal_box = Crypto.get_enigma(nskbob2)
        # decrypt the received message
        plaintext = unseal_box.decrypt(encrypted)
        nplaintext = nunseal_box.decrypt(nencrypted)
        print(plaintext.decode('utf-8'))
        print(nplaintext.decode('utf-8'))

    @staticmethod
    def selftest1():
        print("SELFTEST 0")
        # Generate Bob's private key, as we've done in the Box example
        skbob = PrivateKey.generate()
        print(f"skbob={skbob}")
        pkbob = skbob.public_key
        print(f"pkbob={pkbob} ")

        # Alice wishes to send a encrypted message to Bob,
        # but prefers the message to be untraceable
        sealed_box = SealedBox(pkbob)

        # This is Alice's message
        message = b"Kill all kittens"

        # Encrypt the message, it will carry the ephemeral key public part
        # to let Bob decrypt it
        encrypted = sealed_box.encrypt(message)

        print(encrypted)

        unseal_box = SealedBox(skbob)
        # decrypt the received message
        plaintext = unseal_box.decrypt(encrypted)
        print(plaintext.decode('utf-8'))

    @staticmethod
    def selftest0():
        print("SELFTEST 0")
        secretstr = "My favorite colors are yellow and green."
        (num, privkeystr) = Crypto.gen_keypair_as_url()
        pubkey = Crypto.current_pub
        print(f"Key {num} privkeystr {privkeystr} pubkey {pubkey}")
        enc_str = Crypto.encrypt(secretstr, pubkey)
        print(f"Encrypted '{secretstr}' into '{enc_str}'")
        print("SELFTEST 1")
        dec_str = Crypto.decrypt(enc_str, privkeystr)
        print(f"Decrypted '{enc_str}' into '{dec_str}'")

    @staticmethod
    def get_current_pubkey():
        if Crypto.current_pub:
            return Crypto.current_pub
        (Crypto.current_num, Crypto.current_pub) = Crypto.load_pubkey()
        return Crypto.current_pub

    @staticmethod
    def load_pubkey():
        db_pubkey = PubKey.objects.latest('pk')
        print(f"PUBKEY {db_pubkey}")
        pubkey =  Crypto.pubkey_from_bytes(Crypto.pubkeybytes_from_urlstr(db_pubkey.pubkey_str))
        return f'{db_pubkey.pk:05}', pubkey

    @staticmethod
    def commit_pubkey(pubkey):
        if not isinstance(pubkey, PublicKey):
            raise Crypto.WrongType()
        urlstr = Crypto.pubkey_to_urlstr(pubkey)
        print(f"urlstr={urlstr}")
        dbpk = PubKey(pubkey_str=urlstr)
        dbpk.save()
        print(f"dbpk.pk={dbpk.pk}")
        idstr = f'{dbpk.pk:05}'
        return idstr

    @staticmethod
    def encrypt_with_markup(val, pubkey = None):
        if not pubkey:
            pubkey = Crypto.get_current_pubkey()
        if not isinstance(pubkey, PublicKey):
            raise Crypto.WrongType()
        if not isinstance(val, str):
            raise Crypto.WrongType()
        enc_val = Crypto.encrypt(val, pubkey)
        return f'{Crypto.ENC_MARKER}{Crypto.current_num}{Crypto.ENC_SEPARATOR}{enc_val}'

    @staticmethod
    def decrypt_if_possible(val, cookies):
        print(f"dip:{val}")
        if Crypto.is_cleartext(val):
            return val
        known_keys = Crypto.get_known_keys(cookies)
        print(f"dip.known:{known_keys}")
        key_num = val[len(Crypto.ENC_MARKER):len(Crypto.ENC_MARKER)+Crypto.KEYLEN]
        print(f"dip.num:{key_num}")
        if key_num in known_keys:
            raw_val = val[len(Crypto.ENC_MARKER)+Crypto.KEYLEN+len(Crypto.ENC_SEPARATOR):].encode('utf-8')
            print(f"dip.in {raw_val}")
            privkey = Crypto.privkey_from_bytes(Crypto.urlstr_to_bin(cookies[f'{Crypto.COOKIE_PREFIX}{key_num}']))
            try:
                return Crypto.decrypt(raw_val, privkey)
            except:
                print(f'ARGH: val={raw_val} pk={privkey}')
                pass
        return val

    @staticmethod
    def get_known_keys(cookies):
        known_keys = []
        for ck in cookies.keys():
            if Crypto.COOKIE_PREFIX in ck:
                known_keys += [ck[len(Crypto.COOKIE_PREFIX):]]
        known_keys.sort()
        return known_keys

    @staticmethod
    def is_encrypted(strval):
        return strval and strval.startswith(Crypto.ENC_MARKER)

    @staticmethod
    def is_cleartext(strval):
        return not Crypto.is_encrypted(strval)

Crypto.selftest5()