import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from mysite import settings

from .models import Question, Choice


class QuestionModelTests(TestCase):
    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is in the future.
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date
        is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)

    def test_is_published_with_future_pub_date(self):
        """
        is_published() returns False for questions with a future pub_date.
        """
        future_time = timezone.now() + datetime.timedelta(days=1)
        future_question = Question(pub_date=future_time)
        self.assertFalse(future_question.is_published())

    def test_is_published_with_now_pub_date(self):
        """
        is_published() returns True for questions with the current pub_date (now).
        """
        now_time = timezone.now()
        question_now = Question(pub_date=now_time)
        self.assertTrue(question_now.is_published())

    def test_is_published_with_past_pub_date(self):
        """
        is_published() returns True for questions with a past pub_date.
        """
        past_time = timezone.now() - datetime.timedelta(days=1)
        past_question = Question(pub_date=past_time)
        self.assertTrue(past_question.is_published())

    def test_can_vote_with_no_end_date(self):
        """
        can_vote() returns True if no end_date is set and the question is published.
        """
        question = Question(pub_date=timezone.now(), end_date=None)
        self.assertTrue(question.can_vote())

    def test_can_vote_with_end_date_in_future(self):
        """
        can_vote() returns True if current time is before the end_date.
        """
        future_end_date = timezone.now() + datetime.timedelta(days=5)
        question = Question(pub_date=timezone.now(), end_date=future_end_date)
        self.assertTrue(question.can_vote())

    def test_cannot_vote_after_end_date(self):
        """
        can_vote() returns False if the current time is after the end_date.
        """
        past_end_date = timezone.now() - datetime.timedelta(days=1)
        question = Question(pub_date=timezone.now(), end_date=past_end_date)
        self.assertFalse(question.can_vote())


def create_question(question_text, days):
    """
    Create a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_past_question(self):
        """
        Questions with a pub_date in the past are displayed on the
        index page.
        """
        question = create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question],
        )

    def test_future_question(self):
        """
        Questions with a pub_date in the future aren't displayed on
        the index page.
        """
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "No polls are available.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions
        are displayed.
        """
        question = create_question(question_text="Past question.", days=-30)
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question],
        )

    def test_two_past_questions(self):
        """
        The questions index page may display multiple questions.
        """
        question1 = create_question(question_text="Past question 1.", days=-30)
        question2 = create_question(question_text="Past question 2.", days=-5)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question2, question1],
        )


class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future
        returns a 404 not found.
        """
        future_question = create_question(question_text="Future question.", days=5)
        url = reverse("polls:detail", args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past
        displays the question's text.
        """
        past_question = create_question(question_text="Past Question.", days=-5)
        url = reverse("polls:detail", args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)


class UserAuthTest(TestCase):

    def setUp(self):
        # superclass setUp creates a Client object and initializes test database
        super().setUp()
        self.username = "testuser"
        self.password = "FatChance!"
        self.user1 = User.objects.create_user(
            username=self.username,
            password=self.password,
            email="testuser@nowhere.com"
        )
        self.user1.first_name = "Tester"
        self.user1.save()
        # we need a poll question to test voting
        q = Question.objects.create(question_text="First Poll Question")
        q.save()
        # a few choices
        for n in range(1, 4):
            choice = Choice(choice_text=f"Choice {n}", question=q)
            choice.save()
        self.question = q

    def test_logout(self):
        """A user can logout using the logout url."""
        logout_url = reverse("logout")
        self.assertTrue(
            self.client.login(username=self.username, password=self.password)
        )
        response = self.client.post(logout_url, {})
        self.assertEqual(302, response.status_code)
        self.assertRedirects(response, reverse(settings.LOGOUT_REDIRECT_URL))

    def test_login_view(self):
        """A user can login using the login view."""
        login_url = reverse("login")
        response = self.client.get(login_url)
        self.assertEqual(200, response.status_code)
        form_data = {"username": "testuser", "password": "FatChance!"}
        response = self.client.post(login_url, form_data)
        self.assertEqual(302, response.status_code)
        self.assertRedirects(response, reverse(settings.LOGIN_REDIRECT_URL))

    def test_auth_required_to_vote(self):
        """Authentication is required to submit a vote."""
        vote_url = reverse('polls:vote', args=[self.question.id])
        choice = self.question.choice_set.first()
        form_data = {"choice": f"{choice.id}"}
        response = self.client.post(vote_url, form_data)
        self.assertEqual(response.status_code, 302)
        login_with_next = f"{reverse('login')}?next={vote_url}"
        self.assertRedirects(response, login_with_next)

    def test_user_can_only_vote_once_per_question(self):
        """Ensure a user can only have one vote per question."""
        # Login the user
        self.client.login(username=self.username, password=self.password)

        # Submit first vote
        choice1 = self.question.choice_set.first()
        vote_url = reverse('polls:vote', args=[self.question.id])
        response = self.client.post(vote_url, {"choice": choice1.id})
        self.assertRedirects(response, reverse('polls:results', args=[self.question.id]))

        # Verify one vote recorded
        self.assertEqual(self.user1.vote_set.count(), 1)
        self.assertEqual(choice1.vote_set.count(), 1)

        # Submit a second vote for a different choice
        choice2 = self.question.choice_set.last()
        response = self.client.post(vote_url, {"choice": choice2.id})
        self.assertRedirects(response, reverse('polls:results', args=[self.question.id]))

        # Verify the vote has changed to the new choice
        self.assertEqual(self.user1.vote_set.count(), 1)
        self.assertEqual(choice1.vote_set.count(), 0)
        self.assertEqual(choice2.vote_set.count(), 1)
