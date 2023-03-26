from django.db import models

class Topic(models.Model):
  def __str__(self):
    return "<Topic:" + str(self.slogan) + ">"
  slogan = models.CharField(max_length=80)
  created_on = models.TimeField(auto_now_add=True, editable=False)
  updated_on = models.TimeField(auto_now=True, editable=False)

class Conversation(models.Model):
  def __str__(self):
    return "<Conversation: " + str(self.created_on) + ">"
  settings = models.CharField(max_length=2000)
  created_on = models.TimeField(auto_now_add=True, editable=False)
  updated_on = models.TimeField(auto_now=True, editable=False)

class Quote(models.Model):
  def __str__(self):
    return "<Quote " + str(self.quote_from) + " to " + str(self.quote_to) + ": " + str(self.quote) + ">"
  quote = models.CharField(max_length=2000, blank=True, null=True)
  quote_from = models.ForeignKey('Actor', on_delete=models.PROTECT, editable=False, related_name='quotes_by_me')
  quote_to = models.ForeignKey('Actor', on_delete=models.PROTECT, editable=False, related_name='quotes_to_me')
  created_on = models.TimeField(auto_now_add=True, editable=False)
  updated_on = models.TimeField(auto_now=True, editable=False)

class Actor(models.Model):
  def __str__(self):
    return "<Actor: " + str(self.user_handle) + ">"
  user_handle = models.CharField(max_length=80, blank=True, null=True)
  admin_user_id = models.IntegerField(blank=True, null=True)
  country_code = models.CharField(max_length=2, blank=True, null=True)
  zip_code = models.CharField(max_length=12, blank=True, null=True)
  conversation = models.ForeignKey(Conversation, on_delete=models.PROTECT, blank=True, null=True, editable=False)
  history = models.ForeignKey(Quote, on_delete=models.PROTECT, blank=True, null=True, editable=False)
  influence = models.PositiveIntegerField(blank=True, null=True, default=1000)
  level = models.PositiveIntegerField(blank=True, null=True, default=1)
  follows = models.ManyToManyField('Actor', related_name="actors_following_me", blank=True)
  interests = models.ManyToManyField(Topic, related_name="actors_interested", blank=True)
  created_on = models.TimeField(auto_now_add=True, editable=False)
  updated_on = models.TimeField(auto_now=True, editable=False)

class Post(models.Model):
  def __str__(self):
    return "<Post: " + str(self.name) + ">"
  name = models.CharField(max_length=80)
  body = models.CharField(max_length=2000)
  media_url = models.CharField(max_length=80, blank=True, null=True)
  settings = models.CharField(max_length=2000, blank=True, null=True)
  related_to = models.ManyToManyField(Topic, related_name="posts_related", blank=True)
  created_by = models.ForeignKey(Actor, on_delete=models.PROTECT, blank=True, null=True, editable=False)
  owners = models.ManyToManyField(Actor, related_name="actions_owned", blank=True)
  editors = models.ManyToManyField(Actor, related_name="actions_editor", blank=True)
  backers = models.ManyToManyField(Actor, related_name="actions_backer", blank=True)
  children = models.ManyToManyField('Post', related_name="parents", blank=True)
  comments = models.ManyToManyField('Post', related_name="comment_on", blank=True)
  created_on = models.TimeField(auto_now_add=True, editable=False)
  updated_on = models.TimeField(auto_now=True, editable=False)
