from django.db import models

# Create your models here.


class Coupon(models.Model):
    pass

class OfferBanner(models.Model):

    offerBannerStatus = (
        ('active' , 'Active'),
        ('deactive' , 'Deactive'),
    )

    Type = (
        ('add' , 'Add'),
        ('sell' , 'Sell'),
        ('anoucement' , 'Anouncement'),
    )

    title= models.CharField(max_length=100)
    tagLine = models.CharField(max_length=100)
    matter = models.CharField(max_length=1000)

    OfferType = models.CharField(max_length=50, choices=Type, default=None)

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    offerBannerStatus = models.CharField(max_length=80,choices=offerBannerStatus, default='deactive')

    posted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Newsletter(models.Model):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email