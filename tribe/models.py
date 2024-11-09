from django.db import models
from django.urls import reverse
from tribe.locker import PubKey, PrivKey, Box, Secret, KeyRing, Cell

class Country(models.Model):
    name = models.CharField(max_length=100)

    def get_name(self):
        return self.name
    
    def __str__(self):
        return f'[Country {self.name}]'

class Location(models.Model):
    name = models.CharField(max_length=100)
    in_country = models.ForeignKey('Country', on_delete=models.PROTECT, blank=True, null=True)
    in_location = models.ForeignKey('Location', on_delete=models.PROTECT, blank=True, null=True)
    zip_code = models.CharField(max_length=12, blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    lon = models.FloatField(blank=True, null=True)

    def get_name(self):
        return self.name

    def __str__(self):
        return self.name

class Key(models.CharField):
    def __str__(self):
        return self.name
    

class Hood(models.Model):
    name = models.CharField(max_length=100)
    pubkey = Key()
    creation_date = models.DateTimeField(auto_now_add=True, editable=False)
    creator = models.ForeignKey('Person', on_delete=models.SET_NULL, null=True, editable=False)
    

class Revent(models.Model): #fixme, Cell):
    name = models.CharField(max_length=100)
    in_country = models.ForeignKey(Country, on_delete=models.PROTECT, blank=True, null=True)
    in_location = models.ForeignKey(Location, on_delete=models.PROTECT, blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True, editable=False)
    creator = models.ForeignKey('Person', on_delete=models.SET_NULL, null=True, editable=False)

#    def __init__(self, name, pubkey, email, sm_handle, latlon):
#        if not isinstance(pubkey, PubKey):
#            raise TypeError(f'Wrong type {type(pubkey)}')
#        self.name = name
#        super().__init__(name, pubkey)
#        self.host_email = Secret(self, email)
#        self.sm_handle = Secret(self, sm_handle)
#        self.latlon = latlon

    @staticmethod
    def create(name, email, sm_handle, latlon):
        privkey = PrivKey.create()
        return (privkey, Revent(name, privkey.get_pubkey(), email, sm_handle, latlon))

    def __str__(self):
        return f'[Revent {self.name}]'

    def get_absolute_url(self):
        return reverse("tribe:revent", kwargs={"pk": self.pk})

class Person(models.Model):# #fixme, KeyRing):
    callsign = models.CharField(max_length=100)
    creation_date = models.DateTimeField(auto_now_add=True, editable=False)
    creator = models.ForeignKey('Person', related_name="creator_of_person", on_delete=models.SET_NULL, null=True, editable=False)
 
    #def __init__(self):
        #pubkey
        #if not isinstance(pubkey, PubKey):
        #    raise TypeError(f'Wrong type {type(pubkey)}')
        #super().__init__(pubkey)
        #self.name = name
    #    self.ring = {}

    class Unauthorized(Exception):
        pass

    @staticmethod
    def create(name, seed = None):
        privkey = PrivKey.create(seed)
        return (privkey, Person(name, privkey.get_pubkey()))

    def __str__(self):
        #return f'[Person {self.callsign} {len(self.ring)} keys]'
        return f'[Person {self.callsign}]'
    
    def grant_access(self, cell, person):
        if not isinstance(cell, Cell):
            raise TypeError(f'Wrong type {type(cell)}')
        if not isinstance(person, Person):
            raise TypeError(f'Wrong type {type(person)}')
        box = self.get_box(cell)
        if box:
            person.add_box(box)
        else:
            raise Person.Unauthorized(f'Person {self.callsign} has no access to cell {cell.get_id()}')

    def get_clear(self, val):
        secret_val = "???"
        if isinstance(val, Secret):
            val_box = val.get_box()
            #print(f'Val Box {val_box}')
            if not val_box: return secret_val
            my_box = self.get_box(val_box)
            #print(f'My Box {my_box}')
            if not my_box: return secret_val
            val = my_box.decrypt(val.get_bytes()).decode('utf-8')
        return val

class Role(models.Model):
    STEWARD = 'STWD'
    GUIDE = 'GIDE'
    CUSTODIAN = 'CSTN'
    _role_type_choices = [
      (STEWARD, "Steward"),
      (GUIDE, "Guide"),
      (CUSTODIAN, "Custodian"),
    ]
    role_type = models.CharField(max_length=4)
    seq = models.FloatField(blank=True, null=True)
    in_revent = models.ForeignKey(Revent, on_delete=models.CASCADE, blank=True, null=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True, editable=False)
    creator = models.ForeignKey(Person, related_name="assigner_of_role", on_delete=models.SET_NULL, null=True, editable=False)

    class Meta:
        ordering = ["-seq"]

    def get_role_name(self):
        lookup = {key:s for (key,s) in Role._role_type_choices}
        return lookup.get(self.role_type,self.role_type)

    def __str__(self):
        return f'[Role {self.get_role_name()} in {self.in_revent} is {self.person}]'


class ContactInfo(models.Model):
    OTHER="OTHR"
    EMAIL="MAIL"
    PHONE="PHON"
    WEBSITE="WEBS"
    YOUTUBE="YOUT"
    TWITTER="TWTR"
    FACEBOOK="FCBK"
    INSTAGRAM="INSG"
    LINKEDIN="LNIN"
    VIMEO="VIME"
    WHATSAPP="WHAP"
    TELEGRAM="TLGM"
    DISCORD="DCRD"
    SLACK="SLAK"
    _contact_type_choices =[
        (OTHER, "Other Contact Address"),
        (EMAIL, "Email Address"),
        (PHONE, "Phone Number"),
        (WEBSITE, "Organization Website URL"),
        (YOUTUBE, "Youtube URL"),
        (TWITTER, "X (formerly twitter) URL"),
        (FACEBOOK, "Facebook URL"),
        (INSTAGRAM, "Instagram URL"),
        (LINKEDIN, "LinkedIn URL"), #!!!
        (VIMEO, "Vimeo URL"), #!!!
        (WHATSAPP, "WhatsApp group URL"), #!!!
        (TELEGRAM, "Telegram group URL"), #!!!
        (DISCORD, "Discord group URL"), #!!!
        (SLACK, "Slack group URL"), #!!!
    ]

    info_type = models.CharField(max_length=4, choices=_contact_type_choices)
    seq = models.FloatField(blank=True, null=True)
    info = models.CharField(max_length=1000, null=True, blank=True)
    in_revent = models.ForeignKey(Revent, on_delete=models.CASCADE, blank=True, null=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True, editable=False)
    creator = models.ForeignKey(Person, related_name="source_of_info", on_delete=models.SET_NULL, null=True, editable=False)

    def get_contact_type_name(self):
        lookup = {key:s for (key,s) in ContactInfo._contact_type_choices}
        return lookup.get(self.info_type,self.info_type)

    def __str__(self):
        lookup = {key:s for (key,s) in ContactInfo._contact_type_choices}
        return f'[Contact {self.person if self.person else self.in_revent} {lookup.get(self.info_type,self.info_type)}]'


class ReventNote(models.Model):
    in_revent = models.ForeignKey(Revent, on_delete=models.CASCADE, blank=True, null=True)
    text = models.CharField(max_length=1000, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True, editable=True)
    creation_date = models.DateTimeField(auto_now_add=True, editable=False)
    creator = models.ForeignKey(Person, related_name="source_of_note", on_delete=models.SET_NULL, null=True, editable=False)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f'[Note for {self.in_revent} "{self.text[:10]}"]'

'''
pk = PrivKey.create()
pk2,box = Box.create()
print(f'boxid = {box.get_id()}')
sec_email = Secret(box, "my@email.com")
print(f'sec_email {sec_email} clear {sec_email.get_clear(pk2)}')
'''

'''
(bobK, bob) = User.create("Bob", b'XOVAhAGjYpqfNFPW2mvZrhhndH7jX1zhbYZUt5ATFsQ=')
bob.unlock(bobK)
print(f'Bob {bob}')
(aliceK, alice) = User.create("Alice", b'Ve_NDpmIrzetSQsAIAIuMk4B0MksjReaF10Mv6bUJ8c=')
alice.unlock(aliceK)
print(f'Alice {alice}')
(ussK, uss) = Group.create("US South", "uss@gmail", "@uss", "20.123N,120.123W")
print(f'uss = {uss}')
bob.add_box(ussK)
print(f'Bob {bob}')
bob.add_box(ussK)
bob.add_box(ussK)
print(f'Bobs boxes: {", ".join(bob.get_box_list())}')
print(f'Bob {bob}')
print(f'Bob knows {bob.get_clear(uss.host_email)}')
print(f'Alice knows {alice.get_clear(uss.host_email)}')
bob.grant_access(uss, alice)
print(f'Bob knows {bob.get_clear(uss.host_email)}')
print(f'Alice knows {alice.get_clear(uss.host_email)}')

(eunK, eun) = Group.create("EU North", "eun@protonmail", "@swe", "58.123N,18.123E")
try:
    bob.grant_access(eun, alice)
    raise Exception # Should not come here
except User.Unauthorized:
    pass

'''
