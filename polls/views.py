"""This module contains views of polls app"""
from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.contrib import messages
from django.contrib.messages import get_messages
from django.contrib.auth.decorators import login_required

from .models import Question, Choice, Vote


class IndexView(generic.ListView):
    """Take request to index.html which displays the latest few questions."""
    template_name = "polls/index.html"
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
    a question text, with no results but with a form to vote.
    """
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())

    def get(self, request, *args, **kwargs):
        question = self.get_object()

        # Check if the question is published
        if not question.is_published():
            messages.error(request, "This poll is not yet published.")
            return redirect('polls:index')

        # Check if voting is allowed
        if not question.can_vote():
            messages.error(request, "The voting period for this poll has ended.")
            # Render detail.html with the error message
            return render(request, self.template_name, {'question': question})

        return super().get(request, *args, **kwargs)


class ResultsView(generic.DetailView):
    """
    Take request to results.html
    which displays results for a particular question.
    """
    model = Question
    template_name = "polls/results.html"


def vote(request, question_id):
    """Handles voting for a particular choice in a particular question."""
    question = get_object_or_404(Question, pk=question_id)

    if not question.is_published():
        messages.error(request, "This poll has not been published yet.")
        return HttpResponseRedirect(reverse('polls:index'))

    if not question.can_vote():
        messages.error(request, "The voting period for this poll has ended.")
        return HttpResponseRedirect(reverse('polls:detail', args=(question.id,)))

    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        context = {
            "question": question,
            "error_message": "You didn’t select a choice.",
        }
        return render(request, "polls/detail.html", context)

    selected_choice.votes = F("votes") + 1
    selected_choice.save()

    return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))


@login_required
def vote(request, question_id):
    """ Handle user vote in a Django application."""
    question = get_object_or_404(Question, pk=question_id)

    if not question.is_published():
        messages.error(request, "This poll has not been published yet.")
        return HttpResponseRedirect(reverse('polls:index'))

    if not question.can_vote():
        messages.error(request, "The voting period for this poll has ended.")
        return HttpResponseRedirect(reverse('polls:detail', args=(question.id,)))

    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        context = {
            "question": question,
            "error_message": "You didn't select a choice.",
        }
        return render(request, "polls/detail.html", context)

    # Reference to the current user
    this_user = request.user

    # Get the user's vote
    try:
        vote = this_user.vote_set.get(choice__question=question)
        vote.choice = selected_choice
        vote.save()
        messages.success(request, f"Your vote was changed to '{selected_choice.choice_text}'")
    except Vote.DoesNotExist:
        Vote.objects.create(user=this_user, choice=selected_choice)
        messages.success(request, f"You voted for '{selected_choice.choice_text}'")

    # Redirect to the results page after voting
    return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))


def results(request, question_id):
    """ Display the results of a particular poll. """
    question = get_object_or_404(Question, pk=question_id)
    storage = get_messages(request)  # Get messages and remove them from the storage after display

    return render(request, "polls/results.html", {'question': question, 'messages': storage})
