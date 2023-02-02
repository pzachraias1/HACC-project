from django.contrib import admin
from .models import Url, IP_Adresses, Verification_Table

# Register your models here.
admin.site.register(Url)
admin.site.register(IP_Adresses)
admin.site.register(Verification_Table)