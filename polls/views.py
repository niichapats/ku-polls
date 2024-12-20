import logging
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.contrib import messages
from django.contrib.messages import get_messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from .models import Question, Choice, Vote

logger = logging.getLogger('polls')


def get_client_ip(request):
    """Get the visitor’s IP address using request headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log the user login event."""
    ip_address = get_client_ip(request)
    logger.info(f'User {user.username} logged in from {ip_address}')


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log the user logout event."""
    ip_address = get_client_ip(request)
    logger.info(f'User {user.username} logged out from {ip_address}')


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Log the failed login attempt."""
    ip_address = get_client_ip(request)
    username = credentials.get('username', 'unknown')
    logger.warning(f'User {username} login failed from {ip_address}')


class IndexView(generic.ListView):
    """
    Take request to index.html which displays the latest few questions.

    This view shows the latest five published questions.
    """
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """Return the last five published questions."""
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]


class DetailView(generic.DetailView):
    """Take request to detail.html which displays a question text."""

    model = Question
    template_name = "polls/detail.html"

    # def get_queryset(self):
    #     """
    #     Return all published questions sorted by publication date from newest to oldest.
    #     Excludes questions set to be published in the future.
    #     """
    #     # Filter questions to only include those published in the past or present
    #     return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")

    def get_context_data(self, **kwargs):
        """Get context data for rendering the detail view."""
        context = super().get_context_data(**kwargs)
        question = self.get_object()

        # Get the current user vote for this question
        user_vote = None
        if self.request.user.is_authenticated:
            try:
                # Get the choice that the user has already voted for this question
                user_vote = Vote.objects.get(
                    user=self.request.user, choice__question=question
                )
                context['user_vote'] = user_vote.choice.id
            except Vote.DoesNotExist:
                context['user_vote'] = None
        else:
            context['user_vote'] = None

        return context

    def get(self, request, *args, **kwargs):
        """Handle GET requests for the detail view."""
        # Use the filtered queryset from get_queryset to include only valid questions
        # question = get_object_or_404(self.get_queryset(), pk=question_id)
        question_id = self.kwargs["pk"]

        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist as ex:
            logger.exception(f"Non-existent question {question_id} %s", ex)
            messages.warning(request, f"No question found with ID {question_id}")
            return redirect('polls:index')

        # Check if the question is not published (past or present)
        if not question.is_published():
            messages.error(request, "This poll is not yet published.")
            return redirect('polls:index')

        # Check if voting is allowed
        if not question.can_vote():
            messages.error(request, "The voting period for this poll has ended.")
            return redirect('polls:index')

        return super().get(request, *args, **kwargs)


class ResultsView(generic.DetailView):
    """Take request to results.html."""

    model = Question
    template_name = "polls/results.html"

    def get(self, request, *args, **kwargs):
        """Handle GET requests for the results view."""
        question_id = self.kwargs['pk']
        try:
            question = Question.objects.get(pk=question_id)
            return super().get(request, *args, **kwargs)
        except Question.DoesNotExist:
            logger.error(f"Non-existent question {question_id}")
            messages.error(request, f'No question found with ID {question_id}.')
            return redirect('polls:index')


@login_required
def vote(request, question_id):
    """Handle user vote in a Django application."""
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
        messages.error(request, "You didn't select a choice.")
        return HttpResponseRedirect(reverse('polls:detail', args=(question.id,)))

    # Reference to the current user
    this_user = request.user

    # Get the user's vote
    try:
        vote = this_user.vote_set.get(choice__question=question)
        vote.choice = selected_choice
        vote.save()
        messages.success(
            request,
            f"Your vote was changed to '{selected_choice.choice_text}'"
        )
        logger.info(
            f"{this_user.username} changed vote for question {question.id} "
            f"to choice {selected_choice.id}"
        )
    except Vote.DoesNotExist:
        Vote.objects.create(user=this_user, choice=selected_choice)
        messages.success(request, f"You voted for '{selected_choice.choice_text}'")
        logger.info(
            f"{this_user.username} voted for question {question.id} choice "
            f"{selected_choice.id}"
        )
    except Exception as ex:
        logger.exception(
            f"Exception occurred while voting for question {question.id} "
            f"by user {this_user.username}: {str(ex)}"
        )

    # Redirect to the results page after voting
    return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))


def results(request, question_id):
    """Display the results of a particular poll."""
    question = get_object_or_404(Question, pk=question_id)
    storage = get_messages(request)  # Get messages and remove them from the storage after display

    return render(request, "polls/results.html", {'question': question, 'messages': storage})
