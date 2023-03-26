from django.contrib import admin
from .models import Topic, Conversation, Quote, Actor, Post

admin.site.register(Topic)
admin.site.register(Conversation)
admin.site.register(Quote)
admin.site.register(Actor)
admin.site.register(Post)