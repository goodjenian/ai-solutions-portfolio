import unittest

from notifications.email_templates import DigestTemplate


class TestDigestTemplate(unittest.TestCase):
    def test_render_expert_section(self):
        """Test that the expert section is rendered when expert data is present."""
        data = {
            "expert": {
                "market_table": [{"City": "New York", "Trend": "Up", "Avg Price": "$1.2M"}],
                "analysis": "Market is booming.",
            }
        }

        subject, html = DigestTemplate.render("weekly", data, user_name="Test User")

        self.assertIn("Expert Market Insights", html)
        self.assertIn("Market Trends", html)
        self.assertIn("New York", html)
        self.assertIn("Market is booming", html)

    def test_render_no_expert_section(self):
        """Test that the expert section is NOT rendered when expert data is missing."""
        data = {"new_properties": 5, "expert": None}

        subject, html = DigestTemplate.render("weekly", data, user_name="Test User")

        self.assertNotIn("Expert Market Insights", html)
        self.assertIn("New Properties", html)


if __name__ == "__main__":
    unittest.main()
