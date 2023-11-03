from util_scheduler import job, set_word_of_the_day, record_it
from unittest.mock import patch
import unittest

with open("sample.html", "r") as f:
    article_html = f.read()


class TestScheduler(unittest.TestCase):
    @patch("util_scheduler.push_history_to_github")
    @patch("util_scheduler.send_email")
    def test_job(self, mock_push_history_to_github, mock_send_email):
        history = []
        job(article_html, history, None, None)
        assert len(history) == 1

        print("------------")
        history = []
        record_it("1", history)
        set_word_of_the_day('x = y')
        (ex_id, content) = job(article_html, history, None, None)
        assert ex_id == "2"


if __name__ == '__main__':
    import easyocr

    reader = easyocr.Reader(['en'])
    result = reader.readtext('test.jpg', detail=0)
    print(result)
    unittest.main()
