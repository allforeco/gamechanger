class MediaObject:
  def __init__(self, name, description, code, icon, urls, domains, prefix):
    self.name = name
    self.code = code
    self.icon = '/static/icon_' +icon+'.png'
    self.description = description
    self.urls = urls
    self.domains = domains
    self.prefix = prefix

  name = ""
  code = ""
  icon = ""
  description = ""
  urls = []
  domains = []
  prefix = ""


class MediaParser:
  OTHER=MediaObject(
    "Other", "Other Media", "OTHR",
    'unknown',
    [],
    [],
    'https://')
  EMAIL=MediaObject(
    "Email", "Email Adress", "MAIL",
    'mail',
    [],
    [],
    'mailto:')
  PHONE=MediaObject(
    "Phone", "Phone Number", "PHON",
    'phone',
    [],
    [],
    'tel:')
  WEBSITE=MediaObject(
    "Website", "Webb Adress", "WEBS",
    'globe',
    [],
    [],
    'https://')
  YOUTUBE=MediaObject(
    "Youtube", "YouTube Adress", "YOUT",
    'yt30',
    ['youtube'],
    ['.com'],
    'https://')
  TWITTER=MediaObject(
    "X (formerly Twitter)", "X (formerly Twitter) Adress", "TWTR",
    'twitter30',
    ['twitter'],
    ['.com'],
    'https://')
  FACEBOOK=MediaObject(
    "Facebook", "Facebook Adress", "FCBK",
    'fb30',
    ['facebook'],
    ['.com'],
    'https://')
  INSTAGRAM=MediaObject(
    "Instagram", "Instagram Adress", "INSG",
    'insta30',
    ['instagram'],
    ['.com'],
    'https://')
  LINKEDIN=MediaObject(
    "LinkedIN", "LinkedIN Adress", "LNIN",
    'linkedin',
    ['linkedin'],
    ['.com'],
    'https://')
  VIMEO=MediaObject(
    "Vimeo", "Vimeo Adress", "VIMW",
    'vimeo',
    [],
    ['.com'],
    'https://')
  WHATSAPP=MediaObject(
    "Whatsapp", "Whatsapp Adress", "WHAP",
    'whatsapp',
    ['whatsapp'],
    ['.com'],
    'https://')
  TELEGRAM=MediaObject(
    "Telegram", "Telegram Adress", "TLMG",
    'telegram',
    ['t'],
    ['.me'],
    'https://')
  DISCORD=MediaObject(
    "Discord", "Discord Adress", "DCRD",
    'discord',
    [],
    ['.com'],
    'https://')
  SLACK=MediaObject(
    "Slack", "Slack Adress", "SLAK",
    'slack',
    [],
    ['.com'],
    'https://')

  def get_Icon(self, MEDIA):
    if self._media_description[MEDIA]:
      return self._media_icon[MEDIA]
    else:
      return self._media_icon[self.OTHER]

  def checkMEDIA(self, link):
    splitlink = link.split('/')

  def checkURL(self, MEDIA, link):
    splitlink = link.split('/')
    
  def get_URL(self, MEDIA, link):
    splitlink = link.split('/')
    outlink=''

    if not self._media_description[MEDIA]:
      return self.checkURL(self, self.OTHER, link)

    if self._media_url_prefix[MEDIA][0] and not link.startswith(self._media_url_prefix[MEDIA][0]):
      outlink+=self._media_url_prefix[MEDIA]

    if self._media_url_prefix[MEDIA][1] and not link.contains(self._media_url_prefix[MEDIA][1]):
      outlink+=self._media_url_prefix[MEDIA][1]

    outlink+=link

    if self._media_url_prefix[MEDIA][2] and not link.endswith(self._media_url_prefix[MEDIA][2]):
      outlink+=self._media_url_prefix[MEDIA][1]

    return outlink
  
