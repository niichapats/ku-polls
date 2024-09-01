import datetime

from django.db import models
from django.utils import timezone


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published', default=timezone.now)
    end_date = models.DateTimeField(null=True)

    def __str__(self):
        return self.question_text

    def was_published_recently(self):
        """Return Ture if the question was published within 1 day."""
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

    def is_published(self):
        """Return True if the current date is on or after the question's pub_date."""
        return timezone.now() >= self.pub_date

    def can_vote(self):
        """Return True if voting is allowed for this question."""
        if self.end_date is None:
            return timezone.now() >= self.pub_date
        return self.pub_date <= timezone.now() <= self.end_date


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text
