"""This module contains views of polls app"""

from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views import generic
from django.utils import timezone

from .models import Question, Choice


class IndexView(generic.ListView):
    """Take request to index.html which displays the latest few questions."""
    template_name = "polls/index.html"
    # originally, the context name would be question_list
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """
        Return the last five published questions
        (not including those set to be published in the future).
        """
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]


class DetailView(generic.DetailView):
    """
    Take request to detail.html which displays
    a question text, with no results but with a form to vote
    """
    model = Question
    template_name = "polls/detail.html"
    # context var is question

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    """
    Take request to results.html
    which displays results for a particular question.
    """
    model = Question
    template_name = "polls/results.html"
    # context var is question


def vote(request, question_id):
    """Handles voting for a particular choice in a particular question."""
    question = get_object_or_404(Question, pk=question_id)
    try:
        # find the selected choice from form in polls/templates/polls/detail.html
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):  # didn't pick any
        # Redisplay the question voting form and inform that they didn't select the choice
        context = {
                "question": question,
                "error_message": "You didn't select a choice.",
            }
        # when they search for templates, they already in template dir
        return render(request, "polls/detail.html", context)

    selected_choice.votes = F("votes") + 1  # add the vote to database
    selected_choice.save()
    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data.This prevents data from being posted twice if a
    # user hits the Back button.

    # After voted redirects to the results page for the question
    return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))
